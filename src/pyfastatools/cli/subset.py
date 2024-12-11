from typing import Optional

from pydantic import Field, FilePath
from pydantic_argparse import BaseCommand

from pyfastatools.cli.edit import SingleOutputBaseCommand
from pyfastatools.file import FastaFile


class TakeArgs(SingleOutputBaseCommand):
    number: int = Field(..., description="take first N sequences")


class FetchArgs(SingleOutputBaseCommand):
    file: FilePath = Field(
        ..., description="fetch all sequences named in this file from the input fasta"
    )


class RemoveArgs(SingleOutputBaseCommand):
    file: FilePath = Field(
        ..., description="remove all sequences named in this file from the input fasta"
    )


class SubsetArgs(BaseCommand):
    take: Optional[TakeArgs] = Field(None, description="take sequences")
    fetch: Optional[FetchArgs] = Field(None, description="fetch sequences")
    remove: Optional[RemoveArgs] = Field(None, description="remove sequences")


def main(args: SubsetArgs):
    if args.take is not None:
        output = args.take.io.output
        fasta_iterator = FastaFile(args.take.io.input).parse().take(args.take.number)
    elif args.fetch is not None:
        output = args.fetch.io.output
        fastafile = FastaFile(args.fetch.io.input)
        keep = fastafile.read_subset_file(args.fetch.file)
        fasta_iterator = fastafile.parse().fetch(keep)
    elif args.remove is not None:
        output = args.remove.io.output
        fastafile = FastaFile(args.remove.io.input)
        remove = fastafile.read_subset_file(args.remove.file)
        fasta_iterator = fastafile.parse().remove(remove)
    else:
        raise RuntimeError("unreachable")

    with open(output, "w") as fp:
        fasta_iterator.write(fp)
