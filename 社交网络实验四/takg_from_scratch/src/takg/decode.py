from pathlib import Path

import torch
from torch.nn import functional as F

from .data import BOS, EOS, PAD, UNK, load_data
from .train import build_model
from .utils import ROOT, choose_device, save_json


def tensorize_item(item, bow_size, device):
    source = torch.tensor([item["source"]], dtype=torch.long, device=device)
    extended_source = torch.tensor([item["extended_source"]], dtype=torch.long, device=device)
    source_mask = torch.ones_like(source, dtype=torch.bool)
    lengths = torch.tensor([len(item["source"])], dtype=torch.long, device=device)
    bow = torch.zeros((1, bow_size), dtype=torch.float, device=device)
    for index, count in item["bow"]:
        bow[0, index] = count
    return source, extended_source, source_mask, lengths, bow


@torch.no_grad()
def beam_search(model, item, word_vocab, bow_vocab, beam_size, max_length, device):
    source, extended_source, source_mask, lengths, bow = tensorize_item(item, len(bow_vocab), device)
    memory, initial_state, topics, _, _, _ = model.encode(source, lengths, F.normalize(bow, p=2, dim=-1), sample_topics=False)
    bos_id, eos_id, unk_id = (word_vocab.token_to_id[token] for token in (BOS, EOS, UNK))
    max_oov = len(item["oov_tokens"])
    beams = [([], 0.0, initial_state.squeeze(0), bos_id, [], False)]
    for _ in range(max_length):
        active = [beam for beam in beams if not beam[5]]
        if not active:
            break
        count = len(active)
        previous = torch.tensor([beam[3] for beam in active], dtype=torch.long, device=device)
        states = torch.stack([beam[2] for beam in active])
        distribution, next_states, attention = model.decoder.step(
            previous, states, memory.expand(count, -1, -1), source_mask.expand(count, -1),
            extended_source.expand(count, -1), max_oov, topics.expand(count, -1))
        log_probabilities = torch.log(distribution.clamp_min(1e-12))
        candidates = [beam for beam in beams if beam[5]]
        per_beam = min(beam_size, distribution.size(1))
        values, indices = log_probabilities.topk(per_beam, dim=1)
        for row, beam in enumerate(active):
            for value, token in zip(values[row].tolist(), indices[row].tolist()):
                generated = beam[0] + [token]
                candidates.append((generated, beam[1] + value, next_states[row], token,
                                   beam[4] + [attention[row].cpu().tolist()], token == eos_id))
        beams = sorted(candidates, key=lambda entry: entry[1], reverse=True)[:beam_size]

    phrases = []
    details = []
    seen = set()
    for token_ids, score, _, _, attentions, _ in sorted(beams, key=lambda entry: entry[1], reverse=True):
        tokens = []
        for token_id in token_ids:
            if token_id == eos_id:
                break
            if token_id < len(word_vocab):
                token = word_vocab.id_to_token[token_id]
            else:
                oov_index = token_id - len(word_vocab)
                token = item["oov_tokens"][oov_index] if oov_index < len(item["oov_tokens"]) else UNK
            if token not in (PAD, BOS):
                tokens.append(token)
        key = tuple(tokens)
        if key and key not in seen:
            seen.add(key)
            phrases.append(tokens)
            details.append({"tokens": tokens, "log_probability": score, "attention": attentions})
    return phrases, details


def run_prediction(config, checkpoint=None):
    device = choose_device(config.device)
    data = load_data(config)
    model = build_model(config, data).to(device)
    run_folder = ROOT / "runs" / config.run_name
    checkpoint = Path(checkpoint) if checkpoint else run_folder / "best.pt"
    with checkpoint.open("rb") as stream:
        saved = torch.load(stream, map_location=device, weights_only=False)
    model.load_state_dict(saved["model"])
    model.eval()
    prediction_path = run_folder / "predictions.txt"
    examples = []
    with prediction_path.open("w", encoding="utf-8") as output:
        for index, item in enumerate(data["test"]):
            predictions, details = beam_search(model, item, data["word_vocab"], data["bow_vocab"],
                                               config.beam_size, config.decode_max_length, device)
            predictions = predictions[:config.predictions_per_post]
            output.write(";".join(" ".join(phrase) for phrase in predictions) + "\n")
            if len(examples) < 30:
                examples.append({"source": item["source_tokens"], "targets": item["targets"],
                                 "predictions": predictions[:5], "beam_details": details[:1]})
            if (index + 1) % 100 == 0:
                print(f"decoded {index + 1}/{len(data['test'])}", flush=True)
    save_json(examples, run_folder / "examples.json")
    return prediction_path
