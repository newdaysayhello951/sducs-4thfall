import json
import math
import random
import time
from dataclasses import asdict
from functools import partial
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader

from .data import BOS, PAD, collate_training, load_data
from .model import TAKG, topic_model_loss
from .utils import ROOT, atomic_torch_save, choose_device, save_json, seed_everything


def build_model(config, data):
    word_vocab, bow_vocab = data["word_vocab"], data["bow_vocab"]
    return TAKG(
        vocabulary_size=len(word_vocab), bow_size=len(bow_vocab),
        padding_id=word_vocab.token_to_id[PAD], embedding_size=config.embedding_size,
        encoder_hidden_size=config.encoder_hidden_size, encoder_layers=config.encoder_layers,
        decoder_hidden_size=config.decoder_hidden_size, topic_count=config.topic_count,
        topic_hidden_size=config.topic_hidden_size, dropout=config.dropout,
    )


def generator_loss(distributions, extended_targets, target_mask):
    probabilities = distributions.gather(2, extended_targets.unsqueeze(-1)).squeeze(-1)
    token_losses = -torch.log(probabilities.clamp_min(1e-9)) * target_mask
    return token_losses.sum() / target_mask.sum(), token_losses.sum().detach(), target_mask.sum().detach()


def move_batch(batch, device):
    return {key: value.to(device) if torch.is_tensor(value) else value for key, value in batch.items()}


def make_loaders(config, data):
    collate = partial(collate_training, padding_id=data["word_vocab"].token_to_id[PAD],
                      bow_size=len(data["bow_vocab"]))
    generator = torch.Generator().manual_seed(config.seed)
    return {
        "train": DataLoader(data["train"], batch_size=config.batch_size, shuffle=True,
                            num_workers=config.num_workers, collate_fn=collate, generator=generator),
        "valid": DataLoader(data["valid"], batch_size=config.batch_size, shuffle=False,
                            num_workers=config.num_workers, collate_fn=collate),
    }


def capture_rng():
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None}


def restore_rng(state):
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"].cpu())
    if torch.cuda.is_available() and state["cuda"] is not None:
        torch.cuda.set_rng_state_all([item.cpu() for item in state["cuda"]])


def save_checkpoint(path, model, optimizers, schedule, config):
    atomic_torch_save({"model": model.state_dict(),
                       "optimizers": {name: optimizer.state_dict() for name, optimizer in optimizers.items()},
                       "schedule": schedule, "config": asdict(config), "rng": capture_rng()}, path)


def train_topic_epoch(model, loader, optimizer, device, gradient_clip):
    model.topic_model.train()
    total, examples = 0.0, 0
    for step, raw_batch in enumerate(loader, 1):
        batch = move_batch(raw_batch, device)
        optimizer.zero_grad(set_to_none=True)
        normalized = F.normalize(batch["bow"], p=2, dim=-1)
        _, word_log_probs, mean, log_variance = model.topic_model(normalized)
        loss = topic_model_loss(word_log_probs, batch["bow"], mean, log_variance)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.topic_model.parameters(), gradient_clip)
        optimizer.step()
        total += loss.item() * batch["source"].size(0)
        examples += batch["source"].size(0)
        if step % 100 == 0:
            print(f"topic batch {step}/{len(loader)} loss={total/examples:.4f}", flush=True)
    return total / examples


def train_generation_epoch(model, loader, optimizer, config, device, joint):
    model.train()
    model.topic_model.train(joint)
    for parameter in model.topic_model.parameters():
        parameter.requires_grad_(joint)
    total_generation, total_topic, tokens, examples = 0.0, 0.0, 0, 0
    bos_id = model.bos_id
    for step, raw_batch in enumerate(loader, 1):
        batch = move_batch(raw_batch, device)
        optimizer.zero_grad(set_to_none=True)
        outputs, _, word_log_probs, mean, log_variance = model(
            batch["source"], batch["source_lengths"], batch["source_mask"],
            batch["extended_source"], batch["bow"], batch["target"], bos_id)
        generation, generation_sum, token_count = generator_loss(
            outputs, batch["extended_target"], batch["target_mask"])
        topic = topic_model_loss(word_log_probs, batch["bow"], mean, log_variance) if joint else generation.new_zeros(())
        loss = config.gamma * generation + topic
        if not torch.isfinite(loss):
            raise FloatingPointError("Training produced a non-finite loss")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip)
        optimizer.step()
        total_generation += generation_sum.item()
        total_topic += topic.item() * batch["source"].size(0)
        tokens += int(token_count.item())
        examples += batch["source"].size(0)
        if step % 100 == 0:
            print(f"generation batch {step}/{len(loader)} nll={total_generation/tokens:.4f}", flush=True)
    return {"generation_nll": total_generation / tokens, "topic_loss": total_topic / examples}


@torch.no_grad()
def validate(model, loader, device):
    model.eval()
    generation_total, topic_total, tokens, examples = 0.0, 0.0, 0, 0
    for raw_batch in loader:
        batch = move_batch(raw_batch, device)
        outputs, _, word_log_probs, mean, log_variance = model(
            batch["source"], batch["source_lengths"], batch["source_mask"],
            batch["extended_source"], batch["bow"], batch["target"], model.bos_id)
        _, generation_sum, token_count = generator_loss(outputs, batch["extended_target"], batch["target_mask"])
        topic = topic_model_loss(word_log_probs, batch["bow"], mean, log_variance)
        generation_total += generation_sum.item()
        topic_total += topic.item() * batch["source"].size(0)
        tokens += int(token_count.item())
        examples += batch["source"].size(0)
    return {"generation_nll": generation_total / tokens, "perplexity": math.exp(min(20, generation_total / tokens)),
            "topic_loss": topic_total / examples}


def run_training(config, resume=False):
    seed_everything(config.seed)
    device = choose_device(config.device)
    data = load_data(config)
    loaders = make_loaders(config, data)
    model = build_model(config, data).to(device)
    model.bos_id = data["word_vocab"].token_to_id[BOS]
    optimizers = {
        "topic": torch.optim.Adam(model.topic_model.parameters(), lr=config.learning_rate),
        "generator": torch.optim.Adam([p for name, p in model.named_parameters() if not name.startswith("topic_model.")], lr=config.learning_rate),
        "joint": torch.optim.Adam(model.parameters(), lr=config.learning_rate),
    }
    run_folder = ROOT / "runs" / config.run_name
    run_folder.mkdir(parents=True, exist_ok=True)
    checkpoint = run_folder / "last.pt"
    if checkpoint.exists() and not resume:
        raise FileExistsError(f"{checkpoint} exists; pass --resume or choose another run_name")
    schedule = {"topic_epochs": 0, "generator_epochs": 0, "joint_epochs": 0,
                "best_validation_nll": float("inf"), "stale_epochs": 0, "finished": False}
    if resume:
        with checkpoint.open("rb") as stream:
            saved = torch.load(stream, map_location=device, weights_only=False)
        if saved["config"] != asdict(config):
            raise ValueError("Checkpoint configuration differs from the requested configuration")
        model.load_state_dict(saved["model"])
        for name, optimizer in optimizers.items():
            optimizer.load_state_dict(saved["optimizers"][name])
        schedule = saved["schedule"]
        restore_rng(saved["rng"])
    config.save(run_folder / "config.json")
    save_json({"device": str(device), "torch": torch.__version__, "training_pairs": len(data["train"]),
               "validation_pairs": len(data["valid"])}, run_folder / "environment.json")

    def report(event):
        with (run_folder / "history.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        save_json({"schedule": schedule, "latest": event}, run_folder / "status.json")
        print(json.dumps(event, ensure_ascii=False), flush=True)

    for epoch in range(schedule["topic_epochs"] + 1, config.topic_pretrain_epochs + 1):
        started = time.monotonic()
        loss = train_topic_epoch(model, loaders["train"], optimizers["topic"], device, config.gradient_clip)
        schedule["topic_epochs"] = epoch
        event = {"phase": "topic_pretraining", "epoch": epoch, "loss": loss, "seconds": time.monotonic() - started}
        save_checkpoint(checkpoint, model, optimizers, schedule, config)
        report(event)

    for epoch in range(schedule["generator_epochs"] + 1, config.generator_pretrain_epochs + 1):
        started = time.monotonic()
        metrics = train_generation_epoch(model, loaders["train"], optimizers["generator"], config, device, joint=False)
        validation = validate(model, loaders["valid"], device)
        schedule["generator_epochs"] = epoch
        event = {"phase": "generator_pretraining", "epoch": epoch, **metrics,
                 "validation": validation, "seconds": time.monotonic() - started}
        save_checkpoint(checkpoint, model, optimizers, schedule, config)
        report(event)

    if schedule["finished"]:
        return run_folder
    for epoch in range(schedule["joint_epochs"] + 1, config.joint_epochs + 1):
        started = time.monotonic()
        metrics = train_generation_epoch(model, loaders["train"], optimizers["joint"], config, device, joint=True)
        validation = validate(model, loaders["valid"], device)
        improved = validation["generation_nll"] < schedule["best_validation_nll"]
        schedule["joint_epochs"] = epoch
        schedule["stale_epochs"] = 0 if improved else schedule["stale_epochs"] + 1
        if improved:
            schedule["best_validation_nll"] = validation["generation_nll"]
            save_checkpoint(run_folder / "best.pt", model, optimizers, schedule, config)
        schedule["finished"] = epoch == config.joint_epochs or schedule["stale_epochs"] >= config.patience
        event = {"phase": "joint_training", "epoch": epoch, **metrics, "validation": validation,
                 "best": improved, "seconds": time.monotonic() - started}
        save_checkpoint(checkpoint, model, optimizers, schedule, config)
        report(event)
        if schedule["finished"]:
            break

    with (run_folder / "best.pt").open("rb") as stream:
        best = torch.load(stream, map_location=device, weights_only=False)
    model.load_state_dict(best["model"])
    save_json(model.topic_model.top_words(data["bow_vocab"].id_to_token), run_folder / "topics.json")
    return run_folder
