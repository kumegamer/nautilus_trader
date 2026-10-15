"""Restore consumed archives against the frozen expected hashes, without rewriting evidence."""

import concurrent.futures
import hashlib
import json

from .common import ROOT, digest
from .data import fetch


def restore_one(record):
    path = ROOT / record["path"]
    if path.exists():
        if digest(path) != record["sha256"]:
            raise RuntimeError(
                f"Existing consumed archive differs from frozen manifest: {path}"
            )
        return path.name
    content = fetch(record["url"])
    if hashlib.sha256(content).hexdigest() != record["sha256"]:
        raise RuntimeError(
            f"Publisher archive differs from frozen experiment: {record['url']}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".part")
    temporary.write_bytes(content)
    temporary.replace(path)
    path.with_suffix(".zip.CHECKSUM").write_text(
        record["sha256"] + "  " + path.name + "\n"
    )
    return path.name


def main():
    records = []
    for name in ("historical_manifest.json", "historical_repairs.json"):
        path = ROOT / "data" / name
        if path.exists():
            records.extend(json.loads(path.read_text()))
    if not records:
        raise RuntimeError("Frozen historical archive manifest is required")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, _name in enumerate(pool.map(restore_one, records), 1):
            if i % 30 == 0 or i == len(records):
                print(
                    f"Restored/verified {i}/{len(records)} consumed archives",
                    flush=True,
                )


if __name__ == "__main__":
    main()
