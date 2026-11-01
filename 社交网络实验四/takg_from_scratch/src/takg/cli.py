import argparse
import json
import sys

import torch

from .config import ExperimentConfig
from .data import prepare_data
from .decode import run_prediction
from .metrics import evaluate_prediction_file
from .train import run_training
from .utils import ROOT, save_json


def main():
    parser = argparse.ArgumentParser(description="Independent TAKG reproduction from the ACL 2019 paper")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "train", "predict", "evaluate", "all"):
        child = subparsers.add_parser(command)
        child.add_argument("--config", required=True)
        child.add_argument("--resume", action="store_true")
        child.add_argument("--checkpoint")
    subparsers.add_parser("doctor")
    args = parser.parse_args()

    if args.command == "doctor":
        result = {"python": sys.version, "torch": torch.__version__,
                  "cuda_available": torch.cuda.is_available(), "root": str(ROOT)}
        save_json(result, ROOT / "reports" / "environment.json")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    config = ExperimentConfig.load(args.config)
    if args.command in ("prepare", "all"):
        _, manifest = prepare_data(config)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if args.command in ("train", "all"):
        run_training(config, resume=args.resume)
    if args.command in ("predict", "all"):
        prediction_path = run_prediction(config, args.checkpoint)
        if args.command == "predict":
            print(prediction_path)
    if args.command in ("evaluate", "all"):
        prediction_path = ROOT / "runs" / config.run_name / "predictions.txt"
        print(json.dumps(evaluate_prediction_file(config, prediction_path), ensure_ascii=False, indent=2))
