"""Split a FASTA file"""
import argparse
import os
from itertools import cycle
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from more_itertools import ichunked

from fastatools import edit
from fastatools.fastaparser import fastaparser, write_fasta
from fastatools.utils import (
    EnumeratedFastaParser_T,
    FastaParser_T,
    FilePath,
    GenomicORFFastaParser_T,
    _add_common_args,
    _read_mapfile,
)


def _add_args(argparser: argparse.ArgumentParser, add_common: bool = True):
    if add_common:
        _add_common_args(argparser, False, True)

    split_args = argparser.add_argument_group("SPLIT")

    mode_choices = {"genome", "sequence", "files"}
    split_args.add_argument(
        "-m",
        "--mode",
        choices=mode_choices,
        default="genome",
        metavar="MODE",
        help=(
            f'mode to split the fasta file. choices = [{" | ".join(mode_choices)}]. '
            '"genome" = split into files per genome. '
            '"sequence" = split into files that all contain n sequences. '
            '"files" = split into n files.'
        ),
    )

    split_args.add_argument(
        "-n",
        "--number",
        type=int,
        metavar="N",
        help='if mode is "sequence" or "files", the number of sequences per file or the number of total files, respectively',
    )

    split_args.add_argument(
        "--force-split",
        default=False,
        action="store_true",
        help="use if -o outdir already exists and it is ok to split the -i input file into this directory",
    )

    edit._add_args(argparser, False)


def split_partition(parser: FastaParser_T, n: int) -> EnumeratedFastaParser_T:
    n_partitions = cycle(range(n))
    yield from zip(n_partitions, parser)


def split_uniformly(parser: FastaParser_T, n: int) -> EnumeratedFastaParser_T:
    for idx, subparser in enumerate(ichunked(parser, n)):
        for record in subparser:
            yield idx, record


def split_by_genome(
    parser: FastaParser_T,
    keyfile: Optional[FilePath] = None,
) -> GenomicORFFastaParser_T:
    key = None if keyfile is None else _read_mapfile(keyfile)

    def keyfunc(name: str, key: Optional[Dict[str, str]] = None) -> str:
        if key is None:
            # header = GENOME_PTNNUM
            # requires header to be cleaned
            return name.rsplit("_", 1)[0]
        else:
            # key is a dict
            return key[name]

    for name, seq in parser:
        genome = keyfunc(name, key)
        yield genome, (name, seq)


_SPLIT_PARSERS = Union[
    EnumeratedFastaParser_T,
    GenomicORFFastaParser_T,
]


def write_splits(
    parser: _SPLIT_PARSERS,
    outdir: Path,
    file: FilePath,
    genomic_split: bool = False,
):
    basename = os.path.basename(file)
    basename, ext = str(file).rsplit(".", 1)
    if genomic_split:
        for genome, (name, seq) in parser:
            output = outdir.joinpath(f"{genome}.{ext}")
            with output.open("a") as fp:
                write_fasta(fp, name, seq)
    else:
        for idx, (name, seq) in parser:
            output = outdir.joinpath(f"{basename}_{idx}.{ext}")
            with output.open("a") as fp:
                write_fasta(fp, name, seq)


_DISPATCH: Dict[str, Callable[..., _SPLIT_PARSERS]] = {
    "genome": split_by_genome,
    "files": split_partition,
    "sequence": split_uniformly,
}


def split(parser: FastaParser_T, mode: str, **kwargs):
    splitter = _DISPATCH[mode]
    return splitter(parser=parser, **kwargs)
