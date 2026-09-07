from __future__ import annotations

import hashlib
import json
from pathlib import Path

from caproute.core.io import read_json, write_json
from caproute.ir.schema import CanonicalDocument
from caproute.parsers.base import DocumentInput, DocumentParser


class PredictionCache:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def key(self, parser: DocumentParser, item: DocumentInput) -> str:
        stat = item.source_path.stat()
        payload = {
            "parser": parser.fingerprint,
            "path": str(item.source_path.resolve()),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "page_index": item.page_index,
        }
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, key: str) -> CanonicalDocument | None:
        path = self.root / f"{key}.json"
        return CanonicalDocument.from_dict(read_json(path)) if path.exists() else None

    def put(self, key: str, value: CanonicalDocument) -> None:
        write_json(self.root / f"{key}.json", value.to_dict())

