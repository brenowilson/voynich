import argparse
import json
from pathlib import Path

from voynich.observation.packet_import import write_import_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--blank-package", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    manifest = write_import_bundle(
        packet_path=args.packet,
        blank_package_path=args.blank_package,
        output_root=args.output_root,
        overwrite=args.overwrite,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
