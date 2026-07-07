import argparse
import json
from pathlib import Path

from voynich.observation.authoring_packet import write_packet_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    manifest = write_packet_bundle(
        trial_manifest_path=args.trial_manifest,
        output_root=args.output_root,
        repository_root=args.repository_root,
    )
    print(json.dumps({
        "packet_set_id": manifest["packet_set_id"],
        "packet_count": manifest["packet_count"],
        "packet_set_sha256": manifest["packet_set_sha256"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
