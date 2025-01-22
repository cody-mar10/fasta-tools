import bz2
import gzip
import lzma
from dataclasses import dataclass
from enum import Enum
from textwrap import wrap
from typing import Callable, Dict, TextIO, Tuple

from pyfastatools._fastatools import Record
from pyfastatools._types import FilePath

OpenFn = Callable[..., TextIO]


@dataclass
class CompresssionInfo:
    open: OpenFn
    extension: str
    signature: Tuple[int, ...]


class Compression(Enum):
    BZIP2 = CompresssionInfo(bz2.open, "bz2", (0x42, 0x5A, 0x68))
    GZIP = CompresssionInfo(gzip.open, "gz", (0x1F, 0x8B))
    XZ = CompresssionInfo(lzma.open, "xz", (0xFD, 0x37, 0x7A, 0x58, 0x5A, 0x00, 0x00))
    UNCOMPRESSED = CompresssionInfo(open, "", ())


_SIGNATURE_SIZE = 8


def detect_compression(file: FilePath) -> Compression:
    with open(file, "rb") as fp:
        signature = fp.peek(_SIGNATURE_SIZE)[:_SIGNATURE_SIZE]

    for opt in Compression:
        if opt != Compression.UNCOMPRESSED:
            siglen = len(opt.value.signature)
            if tuple(signature[:siglen]) == opt.value.signature:
                return opt
    return Compression.UNCOMPRESSED


def split_genome_and_orf(name: str) -> Tuple[str, int]:
    split = name.rsplit("_", 1)

    try:
        genome, orf = split
    except ValueError:
        genome = split[0]
        orf = 0
    else:
        orf = int(orf)

    return genome, orf


def read_rename_file(file: FilePath) -> Dict[str, str]:
    # TODO: generalize
    # TODO: use FastaHeader methods to get name
    with open(file) as fp:
        mapper = dict(line.rstrip().split("\t") for line in fp)
        return mapper


def write_fasta(record: Record, fobj: TextIO, width: int = 75):
    """Write a FASTA record to a file object.

    Args:
        record (Record): A FASTA record object.
        fobj (TextIO): A file object to write to.
        width (int, optional): The width of the sequence line. Defaults to 75.
    """

    fobj.write(f">{record.name} {record.desc}\n")
    for line in wrap(record.seq, width=width):
        fobj.write(f"{line}\n")
