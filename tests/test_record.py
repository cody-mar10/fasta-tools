from typing import TypedDict

import pytest

from pyfastatools import Header, Record, RecordType


class RecordKwargs(TypedDict):
    name: str
    desc: str
    seq: str


_test_records = [
    {
        "name": "seq1",
        "desc": "IS_GENE",
        "seq": "ATCG",
    },
    {
        "name": "seq2",
        "desc": "IS_GENOME",
        "seq": "ATCG" * 5000,
    },
    {
        "name": "seq3",
        "desc": "IS_PROTEIN",
        "seq": "MSKFKHYP*",
    },
]


@pytest.mark.parametrize(
    ("record", "expected"),
    zip(_test_records, [RecordType.GENE, RecordType.GENOME, RecordType.PROTEIN]),
)
def test_record_type(record: RecordKwargs, expected: RecordType):
    # C++ obj doesn't handle unpacking well since the bindings don't have the same arg names
    record_obj = Record(*record.values())  # type: ignore
    assert record_obj.type == expected


_test_init_opts = [
    {
        "name": "seq",
        "desc": "desc",
        "seq": "ATCG",
        # test input type
        "type": RecordType.NUCLEOTIDE,
    },
    {
        # test only giving full header line
        "name": "seq desc",
        "seq": "ATCG",
    },
    {
        # test passing in header object
        "header": Header("seq", "desc"),
        "seq": "ATCG",
    },
]


@pytest.mark.parametrize("record", _test_init_opts)
def test_init_opts(record: dict):
    record_obj = Record(*record.values())
    assert record_obj.header.name == "seq"
    assert record_obj.header.desc == "desc"
    assert record_obj.seq == "ATCG"


def test_input_type():
    name, desc, seq = "seq", "desc", "ATCG"

    record = Record(name, desc, seq, RecordType.NUCLEOTIDE)
    assert record.type == RecordType.NUCLEOTIDE

    record = Record(name, desc, seq)
    assert record.type == RecordType.GENE


def test_remove_stop():
    name, desc, seq = "seq", "desc", "MAT*"
    record = Record(name, desc, seq)

    assert record.type == RecordType.PROTEIN
    assert record.seq == "MAT*"

    record.remove_stops()
    assert record.seq == "MAT"


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (("seq", "desc", "ATCG"), False),
        (("", "", ""), True),
    ],
)
def test_empty(record: tuple[str, str, str], expected: bool):
    record_obj = Record(*record)
    assert record_obj.empty() == expected


def test_clean_header():
    record = Record("seq", "desc", "ATCG")
    assert record.header.name == "seq"
    assert record.header.desc == "desc"

    record.clean_header()
    assert record.header.name == "seq"
    assert record.header.desc == ""


def test_to_string():
    record = Record("seq", "desc", "ATCG")
    assert record.to_string() == ">seq desc\nATCG\n"


def test_clear():
    record = Record("seq", "desc", "ATCG")
    assert record.header.name == "seq"
    assert record.header.desc == "desc"
    assert record.seq == "ATCG"
    assert not record.empty()

    record.clear()
    assert record.empty()
