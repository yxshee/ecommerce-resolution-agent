from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MockStore:
    data: dict[str, Any]
    counters: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> MockStore:
        payload = json.loads(Path(path).read_text())
        return cls(data=payload)

    def clone(self) -> MockStore:
        return MockStore(data=copy.deepcopy(self.data), counters=copy.deepcopy(self.counters))

    def next_id(self, prefix: str) -> str:
        current = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = current
        return f"{prefix}_{current:04d}"
