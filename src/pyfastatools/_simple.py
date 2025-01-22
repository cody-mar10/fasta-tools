from pathlib import Path
from typing import Iterator, NamedTuple, Union

FilePath = Union[str, Path]


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
        self._parser = iter(self)

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
        return next(self._parser)

    def all(self) -> list[PyRecord]:
        """Return a list of all FASTA records in the file. This will reset the file pointer
        so that all records in the FASTA file are guaranteed to be returned.

        Returns:
            list[PyRecord]: list of `PyRecord` objects, each having a `name`, `desc`, and `seq` attribute.
        """
        # reset just in case file was advanced
        return list(self._parse())

    def take(self, n: int) -> list[PyRecord]:
        records = [next(self) for _ in range(n)]
        return records
