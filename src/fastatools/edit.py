"""Edit fasta files"""
import argparse
import re
from typing import Optional, Set, TextIO

from fastatools.utils import FilePath, FastaParser_T, _add_common_args, _read_mapfile

ILLEGAL_FN = re.compile("|".join(re.escape(c) for c in r"@#<>%=&*{}?\/!`|:"))
ILLEGAL_SUB_CHAR = "--"


def _add_args(argparser: argparse.ArgumentParser, add_common: bool = True):
    if add_common:
        _add_common_args(argparser, True, False)

    edit_args = argparser.add_argument_group("CLEAN")
    mx_args = edit_args.add_mutually_exclusive_group()

    mx_args.add_argument(
        "--clean-header",
        default=False,
        action="store_true",
        help="use to clean the fasta headers by choosing the part up until the delimiter [mutually exclusive with --clean and -mv/--rename]",
    )
    edit_args.add_argument(
        "-d",
        "--delimiter",
        default=r"\s+",
        help='delimiter to clean/split headers (default: "%(default)s")',
    )
    edit_args.add_argument(
        "--remove-stops",
        default=False,
        action="store_true",
        help="use to remove stop characters in the sequence",
    )
    edit_args.add_argument(
        "--deduplicate",
        default=False,
        action="store_true",
        help="use to deduplicate the fasta file based on the header only",
    )
    edit_args.add_argument(
        "-s",
        "--stop-char",
        default="*",
        help='stop character for ORF fasta files (default: "%(default)s")',
    )
    mx_args.add_argument(
        "--clean",
        default=False,
        action="store_true",
        help="equivalent to --remove-stops --clean-header [mutually exclusive with --clean-header and -mv/--rename]",
    )
    mx_args.add_argument(
        "-mv",
        "--rename",
        metavar="MV",
        help="tab-delimited file to map headers to new names [mutually exclusive with --clean/--clean-header]",
    )


def _clean_header(header: str, delimiter: str) -> str:
    header = ILLEGAL_FN.sub(ILLEGAL_SUB_CHAR, header)
    return re.split(delimiter, header, maxsplit=1)[0]


def _write_changed_names(fobj: TextIO, oldname: str, newname: str):
    if oldname != newname:
        fobj.write(f"{oldname}\t{newname}\n")


def clean_headers(parser: FastaParser_T, delimiter: str) -> FastaParser_T:
    for name, seq in parser:
        cleaned_name = _clean_header(name, delimiter)
        yield cleaned_name, seq


def remove_stops(parser: FastaParser_T, stop_char: str = "*") -> FastaParser_T:
    for name, seq in parser:
        yield name, seq.replace(stop_char, "")


def rename(parser: FastaParser_T, mapfile: FilePath) -> FastaParser_T:
    headermap = _read_mapfile(mapfile)
    for name, seq in parser:
        # default just return same name
        newname = headermap.get(name, name)
        yield newname, seq


def deduplicate(parser: FastaParser_T) -> FastaParser_T:
    headers: Set[str] = set()
    for name, seq in parser:
        if name not in headers:
            headers.add(name)
            yield name, seq


def _modify_parser(
    parser: FastaParser_T,
    clean_header: bool = True,
    delimiter: str = r"\s+",
    rename_header: bool = False,
    mapfile: Optional[FilePath] = None,
) -> FastaParser_T:
    # TODO: could simplify by only checking for map file or changelof_fp
    if clean_header and rename_header:
        raise ValueError("Cleaning headers and renaming headers is mutually exclusive.")

    if clean_header:
        return clean_headers(parser, delimiter)
    elif rename_header and mapfile is not None:
        return rename(parser, mapfile)
    else:
        return parser
