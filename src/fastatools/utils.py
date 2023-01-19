import argparse
from pathlib import Path
from typing import Dict, Iterator, Tuple, Union

FilePath = Union[str, Path]
SequenceRecord = Tuple[str, str]
FastaParser_T = Iterator[SequenceRecord]
EnumeratedFastaParser_T = Iterator[Tuple[int, SequenceRecord]]
GenomicORFFastaParser_T = Iterator[Tuple[str, SequenceRecord]]


def has_stops(sequence: str, stop_char: str = "*"):
    return stop_char in sequence


def _add_common_args(
    argparser: argparse.ArgumentParser,
    requires_output: bool = True,
    requires_outdir: bool = False,
):
    common_args = argparser.add_argument_group("REQUIRED I/O")
    # TODO: add support for multiple fasta files
    common_args.add_argument("-i", "--input", required=True, help="input fasta file")

    if requires_outdir:
        # overrides output
        common_args.add_argument(
            "-o", "--outdir", required=True, help="output directory"
        )
    elif requires_output:
        common_args.add_argument(
            "-o", "--output", required=True, help="output fasta file"
        )


class _HelpAction(argparse._HelpAction):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values,
        option_string=None,
    ):
        parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print(f"{choice:10s}{subparser.description}")

        parser.exit()


def _read_mapfile(mapfile: FilePath, sep: str = "\t") -> Dict[str, str]:
    with open(mapfile) as fp:
        mapper: Dict[str, str] = dict()
        for line in fp:
            key, value = line.rstrip().split(sep)
            mapper[key] = value
        return mapper
