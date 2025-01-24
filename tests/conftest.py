import os

import pytest

from pyfastatools import Parser


@pytest.fixture
def datadir() -> str:
    cwd = os.path.dirname(__file__)
    return os.path.join(cwd, "data")


@pytest.fixture
def protein_fasta_file(datadir: str) -> str:
    file = "test.faa"
    return os.path.join(datadir, file)


@pytest.fixture
def gene_fasta_file(datadir: str) -> str:
    file = "test.ffn"
    return os.path.join(datadir, file)


@pytest.fixture
def genome_fasta_file(datadir: str) -> str:
    file = "test.fna"
    return os.path.join(datadir, file)


@pytest.fixture
def ambiguous_protein_fasta_file(datadir: str) -> str:
    file = "protein.fasta"
    return os.path.join(datadir, file)


@pytest.fixture
def ambiguous_gene_fasta_file(datadir: str) -> str:
    file = "genes.fasta"
    return os.path.join(datadir, file)


@pytest.fixture
def ambiguous_genome_fasta_file(datadir: str) -> str:
    file = "genome.fasta"
    return os.path.join(datadir, file)


@pytest.fixture
def duplicate_fasta_file(datadir: str) -> str:
    file = "test_duplicate.faa"
    return os.path.join(datadir, file)


@pytest.fixture
def parser(protein_fasta_file: str) -> Parser:
    return Parser(protein_fasta_file)
