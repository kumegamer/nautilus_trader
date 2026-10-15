"""Restore public archives against the original, immutable experiment manifests."""

import argparse
import hashlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
MANIFESTS = (
    "preholdout_manifest.json",
    "preholdout_repairs.json",
    "holdout_manifest.json",
    "holdout_repairs.json",
)


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(row, verify_only):
    path = (ROOT / row["path"]).resolve()
    if not path.is_relative_to((ROOT / "data/raw").resolve()):
        raise ValueError(f"Archive outside data/raw: {row['path']}")
    url = urlparse(row["url"])
    if url.scheme != "https" or url.netloc != "data.binance.vision":
        raise ValueError("Only public Binance Vision HTTPS sources are permitted")
    expected = row["sha256"]
    if expected != row["publisher_sha256"]:
        raise ValueError(f"Original publisher checksum differs: {path.name}")
    if path.exists():
        if path.stat().st_size != row["bytes"] or checksum(path) != expected:
            raise ValueError(f"Existing archive differs from frozen checksum: {path}")
        return
    if verify_only:
        raise FileNotFoundError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        with urlopen(row["url"], timeout=120) as response:
            destination = urlparse(response.url)
            if destination.scheme != "https" or destination.netloc != "data.binance.vision":
                raise ValueError("Unexpected archive redirect")
            with temporary.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        if temporary.stat().st_size != row["bytes"] or checksum(temporary) != expected:
            raise ValueError(f"Downloaded archive differs from frozen checksum: {path}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Check local archives offline")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        parser.error("--workers must be between 1 and 16")
    rows = [row for name in MANIFESTS for row in json.loads((ROOT / "data" / name).read_text())]
    if len({row["path"] for row in rows}) != len(rows):
        raise ValueError("Duplicate archive paths in original manifests")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda row: restore(row, args.verify_only), rows))
    print(f"Verified {len(rows)} archives against original publisher SHA256 checksums.")


if __name__ == "__main__":
    main()
