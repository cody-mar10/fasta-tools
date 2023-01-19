from fastatools import edit, split, subset, utils
from fastatools.edit import clean_headers, deduplicate, remove_stops, rename
from fastatools.fastaparser import FastaParser, ORFFastaParser
from fastatools.fastaparser import fastaparser as parse_fasta
from fastatools.fastaparser import write_fasta, write_fastafile
from fastatools.split import split as split_seqs
from fastatools.split import split_by_genome, split_partition, split_uniformly
from fastatools.subset import fetch_seqs, remove_seqs
from fastatools.subset import subset as subset_seqs
from fastatools.subset import take_seqs
