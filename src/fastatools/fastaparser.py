"""Parsing FASTA files for reading and writing"""
import textwrap
from functools import wraps
from pathlib import Path
from typing import Callable, Iterator, List, Optional, TextIO

from fastatools import edit, subset, split
from fastatools.utils import FilePath, FastaParser_T

# TODO: add gzip support?
def fastaparser(file: FilePath) -> FastaParser_T:
    """Parse a FASTA file by yielding (header, sequence) tuples.

    Args:
        file (FilePath): path to a valid FASTA file

    Yields:
        SequenceRecord: (header, sequence) tuple
    """
    with open(file) as f:
        header = f.readline().rstrip()[1:]
        seq: List[str] = list()
        for line in f:
            line = line.rstrip()
            if line[0] == ">":
                yield header, "".join(seq)
                header = line[1:]
                seq = list()
            else:
                seq.append(line)
        yield header, "".join(seq)


def _wrap_fasta(sequence: str, width: int = 75) -> Iterator[str]:
    """Wrap a sequence when outputting to a FASTA file.

    Args:
        sequence (str): biological sequence str
        width (int, optional): width of a sequence line.
            Defaults to 75 characters.

    Yields:
        str: a single sequence line of width `width`
    """
    yield from textwrap.wrap(sequence, width=width)


def write_fasta(fobj: TextIO, name: str, sequence: str, width: int = 75) -> None:
    """Write a fasta sequence to file with line wrapping for the sequence.

    Args:
        fobj (TextIO): open file object in text write mode
        name (str): name of fasta sequence
        sequence (str): fasta sequence
        width (int, optional): text wrapping width. Defaults to 75.
    """
    fobj.write(f">{name}\n")
    for seqline in _wrap_fasta(sequence, width):
        fobj.write(f"{seqline}\n")


def write_fastafile(file: FilePath, parser: FastaParser_T) -> None:
    """Given an output file and a `FastaParser` iterator, write all `SequenceRecord`s
    in the `FastaParser` into the output file.

    Args:
        file (FilePath): output file
        parser (FastaParser): iterator over (header, seq) SequenceRecord tuples
    """
    with open(file, "w") as fp:
        for name, seq in parser:
            write_fasta(fp, name, seq)


def log_cmd(func: Callable):
    @wraps(func)
    def log(self, *args, **kwargs):
        args_msg = ", ".join(
            f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in args
        )
        kwargs_msg = ", ".join(
            f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"
            for k, v in kwargs.items()
        )
        if args_msg and kwargs_msg:
            msg = f"{func.__name__}({args_msg}, {kwargs_msg})"
        elif kwargs_msg:
            msg = f"{func.__name__}({kwargs_msg})"
        elif args_msg:
            msg = f"{func.__name__}({args_msg})"
        else:
            msg = f"{func.__name__}(DEFAULTS)"
        self._cached_cmds.append(msg)
        res = func(self, *args, **kwargs)
        return res

    return log


class FastaParser:
    def __init__(self, fastafile: FilePath) -> None:
        self._file = fastafile
        self._parser = fastaparser(fastafile)
        self._cached_cmds: List[str] = list()

    def __repr__(self) -> str:
        cmds = "\n\t.".join(self._cached_cmds)
        middle = f'{self.__class__.__name__}("{self._file}")'

        if self._cached_cmds:
            start = "(\n"
            end = "\n\t." + f"{cmds}\n)"
            middle = "\t" + middle
        else:
            start = "<"
            end = ">"
        return f"{start}{middle}{end}"

    def __iter__(self):
        return self._parser

    def __next__(self):
        return next(self._parser)

    def write_fastafile(self, output: FilePath):
        write_fastafile(output, self._parser)

    ### EDIT
    @log_cmd
    def clean_headers(self, delimiter: str = r"\s+"):
        self._parser = edit.clean_headers(self._parser, delimiter)
        return self

    @log_cmd
    def deduplicate(self):
        self._parser = edit.deduplicate(self._parser)
        return self

    @log_cmd
    def rename(self, mapfile: FilePath):
        self._parser = edit.rename(self._parser, mapfile)
        return self

    @log_cmd
    def remove_stops(self, stop_char: str = "*"):
        self._parser = edit.remove_stops(self._parser, stop_char)
        return self

    ### SUBSET
    @log_cmd
    def remove_seqs(self, subset_file: FilePath):
        self._parser = subset.remove_seqs(self._parser, subset_file)
        return self

    @log_cmd
    def fetch_seqs(self, subset_file: FilePath):
        self._parser = subset.fetch_seqs(self._parser, subset_file)
        return self

    @log_cmd
    def take_seqs(self, n: int):
        self._parser = subset.take_seqs(self._parser, n)
        return self

    @log_cmd
    def subset(self, mode: str, **kwargs):
        self._parser = subset.subset(self._parser, mode, **kwargs)
        return self

    ### SPLIT
    @log_cmd
    def split_partition(self, n: int):
        self._parser = split.split_partition(self._parser, n)
        return self

    @log_cmd
    def split_uniformly(self, n: int):
        self._parser = split.split_uniformly(self._parser, n)
        return self

    def write_splits(self, outdir: Path, file: FilePath):
        split.write_splits(self._parser, outdir, file, False)


class ORFFastaParser(FastaParser):
    @log_cmd
    def split_by_genome(self, keyfile: Optional[FilePath] = None):
        self._parser = split.split_by_genome(self._parser, keyfile)
        return self

    def write_split_by_genome(self, outdir: Path, file: FilePath):
        split.write_splits(self._parser, outdir, file, True)
