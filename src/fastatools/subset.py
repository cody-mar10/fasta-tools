"""Subset a FASTA file"""
import argparse
from itertools import islice
from typing import Callable, Dict, Optional, Set

from fastatools import edit
from fastatools.utils import FilePath, FastaParser_T, _add_common_args


def _add_args(argparser: argparse.ArgumentParser, add_common: bool = True):
    if add_common:
        _add_common_args(argparser, True, False)
    _mode = argparser.add_argument_group("SUBSET MODE -- CHOOSE ONE")
    mode = _mode.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "-t",
        "--take",
        type=int,
        help="take the first n sequences and save to the output",
    )
    mode.add_argument(
        "-f",
        "--fetch",
        help="fetch all sequences in the provided file from the input fasta file",
    )
    mode.add_argument(
        "-r",
        "--remove",
        help="remove all sequences in the provided file from the input fasta file",
    )

    edit._add_args(argparser, False)


def _read_subset_file(file: FilePath) -> Set[str]:
    with open(file) as fp:
        subset = {line.rstrip() for line in fp}
    return subset


def remove_seqs(parser: FastaParser_T, subset_file: FilePath) -> FastaParser_T:
    seq_subset = _read_subset_file(subset_file)
    return ((name, seq) for name, seq in parser if name not in seq_subset)


def fetch_seqs(parser: FastaParser_T, subset_file: FilePath) -> FastaParser_T:
    seq_subset = _read_subset_file(subset_file)
    return ((name, seq) for name, seq in parser if name in seq_subset)


def take_seqs(parser: FastaParser_T, n_seqs: int) -> FastaParser_T:
    return islice(parser, n_seqs)


_DISPATCH: Dict[str, Callable[..., FastaParser_T]] = {
    "remove": remove_seqs,
    "fetch": fetch_seqs,
    "take": take_seqs,
}


def subset(parser: FastaParser_T, mode: str, **kwargs) -> FastaParser_T:
    # python API
    subsetter = _DISPATCH[mode]
    return subsetter(parser=parser, **kwargs)


def _subset(
    parser: FastaParser_T,
    mode: str,
    clean_header: bool = True,
    delimiter: str = r"\s+",
    # changelog_fp: Optional[TextIO] = None,
    rename_header: bool = False,
    mapfile: Optional[FilePath] = None,
    **kwargs
):
    # cli API
    # order is import, need to subset first then clean/modify headers
    parser = subset(parser, mode, **kwargs)
    parser = edit._modify_parser(
        parser=parser,
        clean_header=clean_header,
        delimiter=delimiter,
        # changelog_fp=changelog_fp,
        rename_header=rename_header,
        mapfile=mapfile,
    )
    return parser
