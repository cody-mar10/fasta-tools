from enum import Enum, auto
from typing import Optional, cast

from pydantic import Field, field_validator, model_validator

from pyfastatools.cli.edit import MultipleOutputBaseCommand, edit
from pyfastatools.file import FastaFile


class Mode(Enum):
    genome = auto()
    uniform = auto()
    chunk = auto()


class SplitArgs(MultipleOutputBaseCommand):
    mode: Mode = Field(
        ...,
        description=(
            "split mode: genome = split into 1 file per genome, "
            "uniform = split into N files of equal size, "
            "chunk = split into N files of equal number of sequences"
        ),
    )
    number: Optional[int] = Field(
        None, description="number for --mode uniform and --mode chunk"
    )

    @field_validator("mode", mode="before")
    def convert(cls, value: str) -> Mode:
        return Mode[value]

    @model_validator(mode="after")
    def check_number_set(self) -> "SplitArgs":
        if self.mode in (Mode.uniform, Mode.chunk) and self.number is None:
            raise ValueError(f"--number must be set for --mode {self.mode}")
        return self


def main(args: SplitArgs):
    # pydantic validator ensures number is set in correct modes
    number = cast(int, args.number)
    fastafile = FastaFile(args.io.input)
    if args.mode == Mode.genome:
        fasta_iterator = fastafile.parse().split_by_genome()
    elif args.mode == Mode.uniform:
        fasta_iterator = fastafile.parse().split_uniformly(number)
    elif args.mode == Mode.chunk:
        fasta_iterator = fastafile.parse().split_into_chunks(number)
    else:
        raise RuntimeError("unreachable")

    fasta_iterator = edit(fasta_iterator, args.edit)

    fasta_iterator.write(args.io.outdir)
