from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass
class ExperimentConfig:
    dataset: str = "Weibo"
    run_name: str = "weibo_takg"
    seed: int = 9527
    device: str = "auto"
    num_workers: int = 0

    max_source_length: int = 100
    max_target_length: int = 10
    vocabulary_size: int = 50000
    bow_vocabulary_size: int = 10000
    min_bow_frequency: int = 3

    embedding_size: int = 150
    encoder_hidden_size: int = 150
    encoder_layers: int = 2
    decoder_hidden_size: int = 300
    topic_count: int = 50
    topic_hidden_size: int = 500
    dropout: float = 0.1

    batch_size: int = 64
    learning_rate: float = 0.001
    gradient_clip: float = 1.0
    gamma: float = 1.0
    topic_pretrain_epochs: int = 100
    generator_pretrain_epochs: int = 1
    joint_epochs: int = 10
    patience: int = 3

    beam_size: int = 50
    predictions_per_post: int = 50
    decode_max_length: int = 6

    train_limit: int = 0
    valid_limit: int = 0
    test_limit: int = 0
    smoke: bool = False

    @classmethod
    def load(cls, path):
        values = json.loads(Path(path).read_text(encoding="utf-8"))
        unknown = set(values) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        config = cls(**values)
        if not config.smoke and any((config.train_limit, config.valid_limit, config.test_limit)):
            raise ValueError("Limited datasets must be marked smoke=true")
        if config.decoder_hidden_size != 2 * config.encoder_hidden_size:
            raise ValueError("decoder_hidden_size must equal twice encoder_hidden_size")
        return config

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
