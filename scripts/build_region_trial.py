import argparse
import json
from pathlib import Path

from voynich.observation.model import read_jsonl
from voynich.observation.region_trial import build_trial_manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    candidates = read_jsonl(args.candidates)
    value = build_trial_manifest(work_queue=queue, candidates=candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
