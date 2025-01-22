from pathlib import Path
from typing import Iterator, Optional

from pyfastatools._fastatools import Parser as _Parser
from pyfastatools._fastatools import Record, Records
from pyfastatools._types import FilePath

RecordIterator = Iterator[Record]


class Parser:
    def __init__(self, file: FilePath):
        if isinstance(file, Path):
            file = file.as_posix()

        self._parser = _Parser(file)

    def __iter__(self):
        return self

    def __next__(self):
        return self._parser.py_next()

    def all(self) -> Records:
        return self._parser.all()

    def take(self, n: int) -> Records:
        return self._parser.take(n)

    def refresh(self):
        self._parser.refresh()

    def _keep(self, subset: set[str]) -> RecordIterator:
        for record in self:
            if record.name in subset or record.header() in subset:
                yield record

    def _remove(self, subset: set[str]) -> RecordIterator:
        for record in self:
            if record.name not in subset and record.header() not in subset:
                yield record

    def filter(
        self, include: Optional[set] = None, exclude: Optional[set] = None
    ) -> RecordIterator:
        if include is None and exclude is None:
            raise ValueError("At least one of include or exclude must be provided")
        elif include is not None and exclude is not None:
            raise ValueError("Only one of include or exclude can be provided")

        if include is not None:
            return self._keep(include)

        if exclude is not None:
            return self._remove(exclude)

        raise RuntimeError("UNREACHABLE")
