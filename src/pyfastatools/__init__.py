from pathlib import Path

from pyfastatools._fastatools import Parser as _Parser
from pyfastatools._fastatools import Record, Records
from pyfastatools.file import FastaFile
from pyfastatools.simple import PyParser

FilePath = str | Path


class Parser:
    def __init__(self, file: FilePath):
        if isinstance(file, Path):
            file = file.as_posix()

        self._parser = _Parser(file)

    def __iter__(self):
        return self

    def __next__(self):
        record = self._parser.next()
        if record.empty():
            raise StopIteration
        return record

    def all(self) -> Records:
        return self._parser.all()

    def take(self, n: int) -> Records:
        return self._parser.take(n)

    def refresh(self):
        self._parser.refresh()
