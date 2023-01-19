#!/usr/bin/env python3
import argparse
from pathlib import Path
from shutil import rmtree

from fastatools import edit, fastaparser, split, subset, utils


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="fastatools - manipulate fasta sequences", add_help=False
    )
    parser.add_argument(
        "-h", "--help", action=utils._HelpAction, help="show this help message and exit"
    )
    subparsers = parser.add_subparsers(
        title="Utility functions",
        dest="command",
        # metavar="COMMAND",
        required=True,
    )

    edit_parser = subparsers.add_parser(
        "edit",
        description="edit FASTA headers and sequences [usable within other utility modules]",
    )
    edit._add_args(edit_parser)

    subset_parser = subparsers.add_parser("subset", description="subset FASTA files")
    subset._add_args(subset_parser)

    split_parser = subparsers.add_parser("split", description="split FASTA files")
    split._add_args(split_parser)

    return parser.parse_args()


def main(args: argparse.Namespace):
    file = args.input
    parser = fastaparser.fastaparser(file)
    command = args.command

    ### EDITING - can be combined with others###
    clean_header = args.clean_header
    remove_stops = args.remove_stops
    if args.clean:
        clean_header = True
        remove_stops = True
    stop_char = args.stop_char
    delimiter = args.delimiter
    rename = args.rename
    deduplicate = args.deduplicate

    # ORDER MATTERS
    if remove_stops:
        parser = edit.remove_stops(parser, stop_char)

    if deduplicate:
        parser = edit.deduplicate(parser)

    # TODO: how to fix this
    # changelog_fp = (
    #     open(f"{str(file).rsplit('.',1)[0]}_header.changelog", "w")
    #     if clean_header
    #     else None
    # )

    cleaning_tasks = dict(
        clean_header=clean_header,
        delimiter=delimiter,
        # changelog_fp=changelog_fp,
        rename_header=(rename is not None),
        mapfile=rename,
    )

    if command == "edit":
        parser = edit._modify_parser(parser=parser, **cleaning_tasks)
        output = args.output
        fastaparser.write_fastafile(output, parser)
    elif command == "subset":
        kwargs = dict()
        if args.take is not None:
            kwargs["mode"] = "take"
            kwargs["n_seqs"] = args.take
        elif args.fetch is not None:
            kwargs["mode"] = "fetch"
            kwargs["subset_file"] = args.fetch
        elif args.remove is not None:
            kwargs["mode"] = "remove"
            kwargs["subset_file"] = args.remove

        kwargs.update(cleaning_tasks)

        parser = subset._subset(parser=parser, **kwargs)
        output = args.output
        fastaparser.write_fastafile(output, parser)
    elif command == "split":
        outdir = Path(args.outdir)
        if not outdir.exists():
            outdir.mkdir()
        elif outdir.exists() and not args.force_split:
            raise ValueError(
                f"Cannot split {file} into {outdir} since directory already exists and you could modify existing files. Try using --force-split if ok."
            )
        kwargs = dict()

        if args.mode == "files" or args.mode == "sequence":
            if args.number is None:
                raise ValueError(
                    "-n/--number must be provided with -m files or -m sequence"
                )
            kwargs["n"] = args.number

        if args.mode == "genome" and rename is None:
            cleaning_tasks["clean_header"] = True

        parser = edit._modify_parser(parser=parser, **cleaning_tasks)

        parser = split.split(parser=parser, mode=args.mode, **kwargs)
        split.write_splits(
            parser=parser,
            outdir=outdir,
            file=file,
            genomic_split=(args.mode == "genome"),
        )


if __name__ == "__main__":
    args = parse_args()
    main(args)
