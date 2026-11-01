import torch
from torch import nn
from torch.nn import functional as F


class NeuralTopicModel(nn.Module):
    """VAE topic model corresponding to equations 1 and 12 in the paper."""

    def __init__(self, bow_size, hidden_size=500, topic_count=50):
        super().__init__()
        self.bow_size = bow_size
        self.topic_count = topic_count
        self.encoder = nn.Sequential(
            nn.Linear(bow_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, hidden_size), nn.ReLU(),
        )
        self.mean = nn.Linear(hidden_size, topic_count)
        self.log_variance = nn.Linear(hidden_size, topic_count)
        self.topic_projection = nn.Linear(topic_count, topic_count)
        self.topic_word = nn.Linear(topic_count, bow_size)

    def forward(self, normalized_bow, sample=None):
        hidden = self.encoder(normalized_bow)
        mean = self.mean(hidden)
        log_variance = self.log_variance(hidden).clamp(-10, 10)
        if sample is None:
            sample = self.training
        if sample:
            standard_deviation = torch.exp(0.5 * log_variance)
            latent = mean + torch.randn_like(standard_deviation) * standard_deviation
        else:
            latent = mean
        topic_mixture = F.softmax(self.topic_projection(latent), dim=-1)
        word_log_probabilities = F.log_softmax(self.topic_word(topic_mixture), dim=-1)
        return topic_mixture, word_log_probabilities, mean, log_variance

    def top_words(self, id_to_token, count=10):
        indices = self.topic_word.weight.detach().T.topk(min(count, len(id_to_token)), dim=1).indices
        return [[id_to_token[index] for index in row.tolist()] for row in indices]


def topic_model_loss(word_log_probabilities, bow_counts, mean, log_variance):
    reconstruction = -(bow_counts * word_log_probabilities).sum(dim=1)
    divergence = -0.5 * (1 + log_variance - mean.square() - log_variance.exp()).sum(dim=1)
    return (reconstruction + divergence).mean()


class SequenceEncoder(nn.Module):
    def __init__(self, vocabulary_size, embedding_size, hidden_size, layers, padding_id, dropout):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, embedding_size, padding_idx=padding_id)
        self.rnn = nn.GRU(embedding_size, hidden_size, num_layers=layers, batch_first=True,
                          bidirectional=True, dropout=dropout if layers > 1 else 0.0)
        self.layers = layers

    def forward(self, source, lengths):
        embedded = self.embedding(source)
        packed = nn.utils.rnn.pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        packed_output, final_state = self.rnn(packed)
        memory, _ = nn.utils.rnn.pad_packed_sequence(packed_output, batch_first=True, total_length=source.size(1))
        final = torch.cat((final_state[-2], final_state[-1]), dim=-1)
        return memory, final


class TopicAwareDecoder(nn.Module):
    """Equations 5-11: topic-aware state, attention, vocabulary and copy distributions."""

    def __init__(self, vocabulary_size, embedding_size, hidden_size, memory_size, topic_count,
                 padding_id, dropout=0.1, use_topics=True, use_copy=True,
                 topic_in_state=True, topic_in_attention=True, topic_in_copy=True):
        super().__init__()
        self.vocabulary_size = vocabulary_size
        self.hidden_size = hidden_size
        self.topic_count = topic_count
        self.use_topics = use_topics
        self.use_copy = use_copy
        self.topic_in_state = use_topics and topic_in_state
        self.topic_in_attention = use_topics and topic_in_attention
        self.topic_in_copy = use_topics and topic_in_copy
        self.embedding = nn.Embedding(vocabulary_size, embedding_size, padding_idx=padding_id)
        state_input = embedding_size + (topic_count if self.topic_in_state else 0)
        self.rnn = nn.GRU(state_input, hidden_size, batch_first=True)
        self.memory_projection = nn.Linear(memory_size, hidden_size, bias=False)
        self.state_projection = nn.Linear(hidden_size, hidden_size, bias=False)
        self.topic_attention_projection = nn.Linear(topic_count, hidden_size, bias=False) if self.topic_in_attention else None
        self.attention_score = nn.Linear(hidden_size, 1, bias=False)
        vocabulary_input = hidden_size + memory_size
        self.vocabulary_hidden = nn.Linear(vocabulary_input, hidden_size)
        self.vocabulary_output = nn.Linear(hidden_size, vocabulary_size)
        copy_input = embedding_size + hidden_size + memory_size + (topic_count if self.topic_in_copy else 0)
        self.copy_gate = nn.Linear(copy_input, 1) if use_copy else None
        self.dropout = nn.Dropout(dropout)

    def step(self, previous_token, state, memory, source_mask, extended_source, max_oov, topics):
        safe_token = previous_token.masked_fill(previous_token >= self.vocabulary_size, 1)
        embedded = self.embedding(safe_token)
        rnn_input = torch.cat((embedded, topics), dim=-1) if self.topic_in_state else embedded
        output, next_state = self.rnn(rnn_input.unsqueeze(1), state.unsqueeze(0))
        decoder_state = output.squeeze(1)

        scores = self.memory_projection(memory) + self.state_projection(decoder_state).unsqueeze(1)
        if self.topic_in_attention:
            scores = scores + self.topic_attention_projection(topics).unsqueeze(1)
        scores = self.attention_score(torch.tanh(scores)).squeeze(-1)
        scores = scores.masked_fill(~source_mask, torch.finfo(scores.dtype).min)
        attention = F.softmax(scores, dim=-1)
        context = torch.bmm(attention.unsqueeze(1), memory).squeeze(1)

        vocabulary_features = torch.cat((decoder_state, context), dim=-1)
        vocabulary_distribution = F.softmax(
            self.vocabulary_output(self.dropout(torch.tanh(self.vocabulary_hidden(vocabulary_features)))), dim=-1)
        if not self.use_copy:
            return vocabulary_distribution, next_state.squeeze(0), attention

        gate_parts = [embedded, decoder_state, context]
        if self.topic_in_copy:
            gate_parts.append(topics)
        generation_probability = torch.sigmoid(self.copy_gate(torch.cat(gate_parts, dim=-1)))
        final_distribution = generation_probability * vocabulary_distribution
        if max_oov:
            final_distribution = torch.cat((final_distribution, final_distribution.new_zeros(final_distribution.size(0), max_oov)), dim=-1)
        final_distribution = final_distribution.scatter_add(
            1, extended_source, (1 - generation_probability) * attention)
        return final_distribution, next_state.squeeze(0), attention


class TAKG(nn.Module):
    def __init__(self, vocabulary_size, bow_size, padding_id, embedding_size=150,
                 encoder_hidden_size=150, encoder_layers=2, decoder_hidden_size=300,
                 topic_count=50, topic_hidden_size=500, dropout=0.1,
                 use_topics=True, use_copy=True, topic_in_state=True,
                 topic_in_attention=True, topic_in_copy=True):
        super().__init__()
        self.vocabulary_size = vocabulary_size
        self.use_topics = use_topics
        self.use_copy = use_copy
        self.encoder = SequenceEncoder(vocabulary_size, embedding_size, encoder_hidden_size,
                                       encoder_layers, padding_id, dropout)
        self.topic_model = NeuralTopicModel(bow_size, topic_hidden_size, topic_count)
        self.decoder = TopicAwareDecoder(vocabulary_size, embedding_size, decoder_hidden_size,
                                         2 * encoder_hidden_size, topic_count, padding_id, dropout,
                                         use_topics, use_copy, topic_in_state, topic_in_attention, topic_in_copy)

    def encode(self, source, source_lengths, normalized_bow, sample_topics=None):
        memory, initial_state = self.encoder(source, source_lengths)
        topics, word_log_probabilities, mean, log_variance = self.topic_model(normalized_bow, sample=sample_topics)
        if not self.use_topics:
            topics = topics.detach().new_zeros(topics.shape)
        return memory, initial_state, topics, word_log_probabilities, mean, log_variance

    def forward(self, source, source_lengths, source_mask, extended_source, bow_counts,
                decoder_targets, bos_id):
        normalized_bow = F.normalize(bow_counts, p=2, dim=-1)
        memory, state, topics, word_log_probabilities, mean, log_variance = self.encode(
            source, source_lengths, normalized_bow)
        batch_size, target_steps = decoder_targets.shape
        max_oov = max(0, int(extended_source.max().item()) - self.vocabulary_size + 1)
        previous_token = source.new_full((batch_size,), bos_id)
        distributions, attentions = [], []
        for step in range(target_steps):
            distribution, state, attention = self.decoder.step(
                previous_token, state, memory, source_mask, extended_source, max_oov, topics)
            distributions.append(distribution)
            attentions.append(attention)
            previous_token = decoder_targets[:, step]
        return (torch.stack(distributions, dim=1), torch.stack(attentions, dim=1),
                word_log_probabilities, mean, log_variance)
