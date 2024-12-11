import re
import textwrap
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterator, Optional, Sequence, TextIO, Tuple

from pyfastatools.utils import split_genome_and_orf


class FastaFormat(Enum):
    GENOME = "fna"
    GENE = "ffn"
    PROTEIN = "faa"
    _UNKNOWN = "fasta"

    def __repr__(self) -> str:
        return self.name

    @property
    def extension(self) -> str:
        return self.value

    @classmethod
    def from_extension(cls, extension: str) -> "FastaFormat":
        extension = extension.lstrip(".")
        if extension == cls.GENOME.value:
            return cls.GENOME

        if extension == cls.GENE.value:
            return cls.GENE

        if extension == cls.PROTEIN.value:
            return cls.PROTEIN

        return cls._UNKNOWN


@dataclass
class FastaHeader:
    name: str
    description: str

    def clean(self):
        self.description = ""

    def __str__(self) -> str:
        if self.description:
            return f"{self.name} {self.description}"
        return self.name

    @classmethod
    def from_string(cls, header: str, pattern: Optional[re.Pattern] = None):
        if pattern is None:
            pattern = re.compile(r"\s+")
        name, *description = pattern.split(header.lstrip(">"), maxsplit=1)
        description = " ".join(description).rstrip()
        return cls(name, description)

    def _split_genome_and_orf(self) -> Tuple[str, int]:
        return split_genome_and_orf(self.name)


@dataclass
class FastaRecord:
    header: FastaHeader
    sequence: str
    format: FastaFormat

    def __repr__(self) -> str:
        if len(self.sequence) <= 6:
            seqrepr = self.sequence
        else:
            seqrepr = f"{self.sequence[:3]}...{self.sequence[-3:]}"
        clsname = self.__class__.__name__
        return (
            f"{clsname}(header={self.header}, sequence={seqrepr}, format={self.format})"
        )

    def clean(self):
        self.header.clean()

    def remove_stops(self):
        self.sequence = self.sequence.replace("*", "")

    def apply(self, *methods) -> None:
        # useful for fusing methods together instead of making a ton of generators
        for method in methods:
            method()

    def wrap(self, width: int = 75) -> Iterator[str]:
        """Wrap a sequence when outputting to a FASTA file.

        Args:
            width (int, optional): width of a sequence line.
                Defaults to 75 characters.

        Yields:
            str: a single sequence line of width `width`
        """
        yield from textwrap.wrap(self.sequence, width=width)

    def write(self, fobj: TextIO, width: int = 75) -> None:
        """Write a fasta sequence to file with line wrapping for the sequence.

        Args:
            fobj (TextIO): open file object in text write mode
            width (int, optional): text wrapping width. Defaults to 75.
        """
        fobj.write(f">{self.header}\n")
        for seqline in self.wrap(width):
            fobj.write(f"{seqline}\n")

    def split_genome_and_orf(self) -> Tuple[str, int]:
        if self.format is FastaFormat.GENOME:
            raise ValueError(
                "FastaRecord should be a protein or gene orf, not a genome"
            )
        return self.header._split_genome_and_orf()

    def content(self, chars: Sequence[str]) -> float:
        charset = set(chars)
        return sum(char in charset for char in self.sequence) / len(self.sequence)

    def reverse_complement(self) -> None:
        # TODO: more robust for other IUPAC codes
        # TODO: distinguish between protein and nucleotide
        # easy way is in postinit to make ttable based on format
        self.sequence = self.sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]


FastaRecordModifier = Callable[[FastaRecord], None]
