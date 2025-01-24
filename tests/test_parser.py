import pytest

from pyfastatools import Header, Headers, Parser, Record, Records, RecordType

_test_expected_num_records = pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("protein_fasta_file", 10),
        ("gene_fasta_file", 10),
        ("genome_fasta_file", 3),
    ],
)


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("protein_fasta_file", RecordType.PROTEIN),
        ("gene_fasta_file", RecordType.GENE),
        ("genome_fasta_file", RecordType.GENOME),
        ("ambiguous_protein_fasta_file", RecordType.PROTEIN),
        ("ambiguous_gene_fasta_file", RecordType.GENE),
        ("ambiguous_genome_fasta_file", RecordType.GENOME),
    ],
)
def test_file_format(
    fixture: str, expected: RecordType, request: pytest.FixtureRequest
) -> None:
    """Test that the file format is correctly detected."""
    file: str = request.getfixturevalue(fixture)

    parser = Parser(file)
    # for the ambiguous fasta files, parser always returns NUCL format...
    assert parser.format == expected

    for record in parser:
        assert record.type == parser.format


def test_iter(parser: Parser) -> None:
    """Test that iter() returns the Parser object"""
    assert iter(parser) is parser


def test_next(parser: Parser) -> None:
    """Test that next() returns the next record"""
    # parser fixture uses the protein fasta file
    record = next(parser)
    assert isinstance(record, Record)

    assert (
        record.header.name
        == "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_1"
    )

    assert (
        record.header.desc
        == "# 143 # 1474 # -1 # ID=1_1;partial=00;start_type=ATG;rbs_motif=AGxAGG/AGGxGG;rbs_spacer=5-10bp;gc_cont=0.371"
    )

    assert record.seq[:20] == "MAFWNKFPFTNFHEMNLDWL"
    assert record.seq[-20:] == "LSCDIYIHDLKTDWERTAS*"

    assert record.type == RecordType.PROTEIN


@_test_expected_num_records
def test_parser_len(fixture: str, expected: int, request: pytest.FixtureRequest):
    """Test that the number of sequences is correct using len()"""
    file: str = request.getfixturevalue(fixture)

    parser = Parser(file)
    assert len(parser) == expected


@_test_expected_num_records
def test_num_records(fixture: str, expected: int, request: pytest.FixtureRequest):
    """Test that the number of sequences is correct using len()"""
    file: str = request.getfixturevalue(fixture)

    parser = Parser(file)
    assert parser.num_records == expected


@pytest.mark.parametrize(
    "fixture",
    ["protein_fasta_file", "gene_fasta_file", "genome_fasta_file"],
)
def test_parser_len_equals_num_records(fixture: str, request: pytest.FixtureRequest):
    """Test that the number of sequences is correct using len()"""
    file: str = request.getfixturevalue(fixture)

    parser = Parser(file)
    assert len(parser) == parser.num_records


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("protein_fasta_file", ".faa"),
        ("gene_fasta_file", ".ffn"),
        ("genome_fasta_file", ".fna"),
        ("ambiguous_protein_fasta_file", ".faa"),
        ("ambiguous_gene_fasta_file", ".ffn"),
        ("ambiguous_genome_fasta_file", ".fna"),
    ],
)
def test_extension(fixture: str, expected: str, request: pytest.FixtureRequest) -> None:
    """Test that the file format is correctly detected."""
    file: str = request.getfixturevalue(fixture)

    parser = Parser(file)
    assert parser.extension == expected


def test_all(parser: Parser) -> None:
    """Test the Parser.all method"""
    # parser fixture uses the protein fasta file

    records = parser.all()
    assert isinstance(records, Records)
    assert len(records) == 10

    for record in records:
        assert isinstance(record, Record)
        assert record.type == RecordType.PROTEIN


@pytest.mark.parametrize("n", [1, 3, 20])
def test_take(parser: Parser, n: int) -> None:
    """Test the Parser.take method"""
    # parser fixture uses the protein fasta file

    records = parser.take(n)
    expected_num = min(len(parser), n)
    assert len(records) == expected_num


def test_refresh(parser: Parser) -> None:
    """Test the Parser.refresh method"""
    # parser fixture uses the protein fasta file

    records = parser.take(3)

    parser.refresh()
    new_records = parser.take(3)

    for x, y in zip(records, new_records):
        assert x == y


def test_next_header(parser: Parser) -> None:
    """Test the Parser.next_header method"""
    # parser fixture uses the protein fasta file

    header = parser.next_header()
    assert isinstance(header, Header)

    assert header.name == "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_1"
    assert (
        header.desc
        == "# 143 # 1474 # -1 # ID=1_1;partial=00;start_type=ATG;rbs_motif=AGxAGG/AGGxGG;rbs_spacer=5-10bp;gc_cont=0.371"
    )


def test_headers(parser: Parser) -> None:
    headers: list[Header] = []

    for header in parser.headers():
        assert isinstance(header, Header)
        headers.append(header)

    assert len(headers) == 10


def test_headers_refreshes(parser: Parser) -> None:
    # parser fixture uses the protein fasta file

    headers = parser.headers()

    # advance one to check if it refreshes
    first_header = next(headers)
    remaining_headers = list(headers)

    new_headers = parser.headers()
    first_new_header = next(new_headers)
    remaining_new_headers = list(new_headers)

    assert first_header == first_new_header

    # BUG: cannot have 2 active iterators at the same time...
    # since there is only 1 underlying file buffer
    # however, not sure if that is a realistic use case
    # another strategy is to create separate parser objects
    for x, y in zip(remaining_headers, remaining_new_headers):
        assert x == y


def test_all_headers(parser: Parser) -> None:
    # parser fixture uses the protein fasta file

    headers = parser.all_headers()

    assert isinstance(headers, Headers)
    assert len(headers) == 10

    for header in headers:
        assert isinstance(header, Header)


def test_remove_stops(parser: Parser) -> None:
    """Test the Parser.remove_stops method"""
    # parser fixture uses the protein fasta file

    has_stop: dict[str, bool] = {}

    for record in parser:
        name = record.header.name
        has_stop[name] = record.seq[-1] == "*"

    parser.refresh()
    for record in parser.remove_stops():
        name = record.header.name
        if has_stop[name]:
            assert record.seq[-1] != "*"


def test_clean(parser: Parser) -> None:
    """Test the Parser.clean method"""
    # parser fixture uses the protein fasta file

    for record in parser:
        assert record.header.desc != ""

    parser.refresh()

    for record in parser.clean():
        assert record.header.desc == ""


def test_first(parser: Parser) -> None:
    """Test the Parser.first method"""
    # parser fixture uses the protein fasta file

    record = parser.first()
    assert isinstance(record, Record)

    expected = {
        "name": "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_1",
        "desc": "# 143 # 1474 # -1 # ID=1_1;partial=00;start_type=ATG;rbs_motif=AGxAGG/AGGxGG;rbs_spacer=5-10bp;gc_cont=0.371",
        "seq-start": "MAFWNKFPFTNFHEMNLDWL",
        "seq-end": "LSCDIYIHDLKTDWERTAS*",
    }

    assert record.header.name == expected["name"]
    assert record.header.desc == expected["desc"]
    assert record.seq[:20] == expected["seq-start"]
    assert record.seq[-20:] == expected["seq-end"]

    # need to check that it always refreshes
    new_record = parser.first()

    assert record == new_record


def test_last(parser: Parser) -> None:
    """Test the Parser.last method"""
    # parser fixture uses the protein fasta file

    record = parser.last()
    assert isinstance(record, Record)

    expected = {
        "name": "SAMEA2737663_a1_ct21578@circular@Microviridae__sp._cterU578_8",
        "desc": "# 4197 # 5795 # 1 # ID=3_8;partial=01;start_type=ATG;rbs_motif=GGAGG;rbs_spacer=5-10bp;gc_cont=0.460",
        "seq-start": "MNRNNERHFNQVPETHVSRT",
        "seq-end": "IARTLIVQNEPQFFGAIRVM",
    }

    assert record.header.name == expected["name"]
    assert record.header.desc == expected["desc"]
    assert record.seq[:20] == expected["seq-start"]
    assert record.seq[-20:] == expected["seq-end"]

    # need to check that it always refreshes
    new_record = parser.last()

    assert record == new_record


@pytest.mark.parametrize("unique_headers", [True, False])
def test_keep(parser: Parser, unique_headers: bool) -> None:
    """Test the Parser.keep method"""
    # parser fixture uses the protein fasta file

    # first 2 records
    keep = {
        "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_1",
        "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_2",
    }

    records = list(parser.filter(include=keep, unique_headers=unique_headers))

    assert len(records) == 2
    for record in records:
        assert record.header.name in keep


def test_keep_full_header(parser: Parser) -> None:
    # parser fixture uses the protein fasta file

    full_header = "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_2 # 1488 # 2153 # -1 # ID=1_2;partial=00;start_type=ATG;rbs_motif=GGAG/GAGG;rbs_spacer=5-10bp;gc_cont=0.366"

    name = "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_2"

    record_from_full_header = next(
        parser.filter(include={full_header}, unique_headers=False)
    )

    parser.refresh()

    record_from_name = next(parser.filter(include={name}, unique_headers=False))

    assert record_from_full_header == record_from_name


@pytest.mark.parametrize("unique_headers", [True, False])
def test_remove(parser: Parser, unique_headers: bool) -> None:
    """Test the Parser.keep method"""
    # parser fixture uses the protein fasta file

    # first 2 records
    remove = {
        "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_1",
        "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_2",
    }

    records = list(parser.filter(exclude=remove, unique_headers=unique_headers))

    assert len(records) == 8
    for record in records:
        assert record.header.name not in remove


def test_remove_full_header(parser: Parser) -> None:
    # parser fixture uses the protein fasta file

    full_header = "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_2 # 1488 # 2153 # -1 # ID=1_2;partial=00;start_type=ATG;rbs_motif=GGAG/GAGG;rbs_spacer=5-10bp;gc_cont=0.366"

    name = "SAMEA2737773_b1_ct14_vs2@Podoviridae__sp._ctp7i14@linear_2"

    records_from_full_header = list(
        parser.filter(exclude={full_header}, unique_headers=False)
    )

    parser.refresh()

    records_from_name = list(parser.filter(exclude={name}, unique_headers=False))

    assert records_from_full_header == records_from_name


def test_filter_invalid_inputs(parser: Parser) -> None:
    """Test that filter raises errors for invalid inputs"""

    # test mutually exclusive
    with pytest.raises(ValueError):
        parser.filter(include={"a"}, exclude={"b"})

    # test not providing either
    with pytest.raises(ValueError):
        parser.filter(include=None, exclude=None)


def test_deduplicate(duplicate_fasta_file: str):
    parser = Parser(duplicate_fasta_file)
    assert len(parser) == 2

    records = list(parser.deduplicate())
    assert len(records) == 1
