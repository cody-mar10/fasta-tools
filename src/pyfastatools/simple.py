from pathlib import Path
from typing import Iterator, NamedTuple

FilePath = str | Path


class PyRecord(NamedTuple):
    name: str
    desc: str
    seq: str

    @classmethod
    def from_header(cls, header: str, sequence: str):
        if " " in header:
            name, desc = header.split(maxsplit=1)
        else:
            name = header
            desc = ""
        return cls(name, desc, sequence)


class PyParser:
    def __init__(self, filename: FilePath):
        self.filename = Path(filename)

    def _parse(self) -> Iterator[PyRecord]:
        with self.filename.open() as fp:
            for line in fp:
                if line[0] == ">":
                    header = line[1:].rstrip()
                    break
            else:
                raise ValueError("No headers found")

            subseq: list[str] = []
            for line in fp:
                line = line.rstrip()

                if line[0] == ">":
                    yield PyRecord.from_header(header, "".join(subseq))
                    header = line[1:]
                    subseq.clear()
                else:
                    subseq.append(line)
            # get last one
            yield PyRecord.from_header(header, "".join(subseq))

    def __iter__(self):
        return self._parse()

    def __next__(self):
        it = self._parse()
        return next(it)

    def all(self) -> list[PyRecord]:
        return list(self._parse())

    def take(self, n: int) -> list[PyRecord]:
        it = self._parse()
        records = [next(it) for _ in range(n)]
        return records
