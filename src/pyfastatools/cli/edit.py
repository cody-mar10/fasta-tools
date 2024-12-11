from typing import Optional, TypeVar

from pydantic import BaseModel, Field, FilePath
from pydantic_argparse import BaseCommand

from pyfastatools.cli.base import MultipleOutputArgs, SingleOutputArgs
from pyfastatools.file import FastaFile
from pyfastatools.iterator import FastaIterator
from pyfastatools.utils import read_rename_file


class EditArgsMixin(BaseModel):
    clean_header: bool = Field(
        False, description="remove all characters after the first whitespace"
    )
    remove_stops: bool = Field(
        False, description="remove stop codons (*) from protein orf sequences"
    )
    deduplicate: bool = Field(
        False, description="remove duplicate sequences based on sequence name"
    )
    rename: Optional[FilePath] = Field(
        None, description="rename sequences based on this input mapping file"
    )
    # TODO: --clean for both clean_header and remove_stops?
    # TODO: mutually exclusive args? can add pydantic validator


class SingleOutputBaseCommand(BaseCommand):
    io: SingleOutputArgs
    edit: EditArgsMixin


class MultipleOutputBaseCommand(BaseCommand):
    io: MultipleOutputArgs
    edit: EditArgsMixin


class EditArgs(SingleOutputBaseCommand):
    pass


_FastaIterator = TypeVar("_FastaIterator", bound=FastaIterator)


def edit(iterator: _FastaIterator, args: EditArgsMixin) -> _FastaIterator:
    if args.rename is not None:
        renamer = read_rename_file(args.rename)
        iterator = iterator.rename(renamer)

    if args.deduplicate:
        iterator = iterator.deduplicate()

    if args.clean_header:  # or edit.clean
        iterator = iterator.clean()

    if args.remove_stops:
        iterator = iterator.remove_stops()

    return iterator


def main(args: EditArgs):
    fasta_iterator = FastaFile(args.io.input).parse()
    fasta_iterator = edit(fasta_iterator, args.edit)
    with open(args.io.output, "w") as fp:
        fasta_iterator.write(fp)
