"""Command-line entry point for Yale IIIF acquisition."""

from pathlib import Path
import argparse
import json

from voynich.acquisition.yale import DEFAULT_MANIFEST_URL, acquire


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-url", default=DEFAULT_MANIFEST_URL)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = acquire(args.manifest_url, args.output_root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
