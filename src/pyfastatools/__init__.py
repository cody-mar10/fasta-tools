from pyfastatools._fastatools import Header, Headers, Record, Records, RecordType
from pyfastatools._parser import Parser
from pyfastatools._simple import PyParser
from pyfastatools.utils import write_fasta

__all__ = [
    "Parser",
    "Record",
    "Records",
    "RecordType",
    "Header",
    "Headers",
    "write_fasta",
]
