import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/manifest.json")
SEED = 20261022


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def create_manifest():
    files = []

    for path in sorted(DATA_DIR.glob("*.csv")):
        rows = len(pd.read_csv(path))

        files.append({
            "file": path.name,
            "rows": rows,
            "sha256": sha256_file(path),
        })

    manifest = {
        "seed": SEED,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "data_directory": str(DATA_DIR),
        "files": files,
    }

    MANIFEST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(MANIFEST_PATH, "w") as file:
        json.dump(manifest, file, indent=2)

    print("Manifest created!")
    print("Path:", MANIFEST_PATH)
    print("Files:", len(files))

    for item in files:
        print(
            f"{item['file']:30s} "
            f"{item['rows']:>8,} rows  "
            f"{item['sha256'][:12]}..."
        )

    return manifest


if __name__ == "__main__":
    create_manifest()