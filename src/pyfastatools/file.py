import re
from functools import cached_property, lru_cache
from pathlib import Path
from statistics import median
from typing import Iterator, Optional, Set, TextIO, Union

from more_itertools import ilen, tail

from pyfastatools._types import FilePath
from pyfastatools.iterator import FastaIterator
from pyfastatools.record import FastaFormat, FastaHeader, FastaRecord
from pyfastatools.utils import detect_compression


class FastaFormatError(Exception):
    """File not in FASTA format."""

    pass


NUCLEOTIDES = set("ACGTURYSWKMBDHVN")
AMINOACIDS = set("ACDEFGHIKLMNPQRSTVWYX*")


class FastaFile:
    def __init__(
        self,
        file: FilePath,
        format: Optional[FastaFormat] = None,
        header_delimiter: str = r"\s+",
    ) -> None:
        self._file = Path(file)
        self._header_split_pattern = re.compile(header_delimiter)
        self._compression_info = detect_compression(file).value

        self._format = FastaFormat._UNKNOWN
        if format is None:
            self._detect_format()
        else:
            self._format = format

    def _detect_format(self) -> None:
        # try based on file extension
        ext = self._file.suffix
        self._format = FastaFormat.from_extension(ext)

        if self._format == FastaFormat._UNKNOWN:
            # otherwise we have to parse the file and guess
            records = list(self.parse().take(3))

            aa_distinguish = AMINOACIDS - NUCLEOTIDES
            if any(char in aa_distinguish for char in records[0].sequence):
                self._format = FastaFormat.PROTEIN
            else:
                # nt format -> genome or gene?
                avg_seqlen = sum(len(rec.sequence) for rec in records) / len(records)
                if avg_seqlen >= 1500.0:
                    self._format = FastaFormat.GENOME
                else:
                    self._format = FastaFormat.GENE

    @property
    def format(self) -> FastaFormat:
        return self._format

    def __enter__(self) -> TextIO:
        self._fp = self._compression_info.open(self._file)
        return self._fp

    def __exit__(self, *args, **kwargs) -> None:
        self._fp.close()

    def _parse(self):
        """Parse a FASTA file by yielding (header, sequence) tuples.

        Args:
            file (FilePath): path to a valid FASTA file

        Yields:
            FastaRecord dataclass with fields for name, description, and sequence
            and methods for writing the record to a file.
        """
        with self as fp:
            for line in fp:
                if line.startswith(">"):
                    header = FastaHeader.from_string(line, self._header_split_pattern)
                    break
            else:
                raise FastaFormatError("No FASTA records found")

            sequence: list[str] = list()
            for line in fp:
                if line.startswith(">"):
                    # yield previous
                    seqstr = "".join(sequence)
                    yield FastaRecord(header, seqstr, self._format)

                    # start over
                    header = FastaHeader.from_string(line, self._header_split_pattern)
                    sequence.clear()
                else:
                    sequence.append(line.rstrip())

            # get last seq
            yield FastaRecord(header, "".join(sequence), self._format)

    def parse(self) -> FastaIterator:
        return FastaIterator(self._parse())

    def parse_headers(self) -> Iterator[FastaHeader]:
        """Parse a FASTA file by yielding only the headers.

        Args:
            file (FilePath): path to a valid FASTA file

        Yields:
            FastaHeader
        """
        with self as fp:
            for line in fp:
                if line.startswith(">"):
                    yield FastaHeader.from_string(line, self._header_split_pattern)

    def read_subset_file(self, file: FilePath) -> Set[str]:
        with open(file) as fp:
            subset = {
                FastaHeader.from_string(line, pattern=self._header_split_pattern).name
                for line in fp
            }
        return subset

    def first(self) -> FastaRecord:
        return next(iter(self.parse()))

    @lru_cache(1)
    def last(self) -> FastaRecord:
        return next(tail(1, self.parse()))

    #### STAT METHODS ####

    @lru_cache(1)
    def __len__(self) -> int:
        return ilen(self.parse_headers())

    @cached_property
    def count(self) -> int:
        return len(self)

    @lru_cache(1)
    def n50(self) -> float:
        lengths = [len(record.sequence) for record in self.parse()]
        return float(median(lengths))

    # TODO: this should just use file level concat?
    def concat(self, other: Union["FastaFile", FastaIterator]) -> FastaIterator:
        if isinstance(other, FastaFile) and self.format != other.format:
            raise ValueError("Cannot concatentate Fasta files with different formats")

        iterator = self.parse().concat(other)
        return iterator

    def __repr__(self) -> str:
        return f'FastaFile("{self._file}", format={self.format.name})'
