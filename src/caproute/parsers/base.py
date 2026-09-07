from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from caproute.ir.schema import CanonicalDocument


@dataclass(frozen=True)
class DocumentInput:
    document_id: str
    source_path: Path
    page_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentParser(ABC):
    name: str
    role: str
    version: str
    adapter_version = "1"

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @property
    def fingerprint(self) -> str:
        return f"{self.name}:{self.version}:adapter-{self.adapter_version}:{self.options!r}"

    @abstractmethod
    def parse(self, item: DocumentInput) -> CanonicalDocument:
        raise NotImplementedError
