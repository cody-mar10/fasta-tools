import os
from itertools import chain, cycle, groupby, islice, tee
from math import ceil
from operator import itemgetter
from typing import (
    Any,
    Dict,
    Generic,
    Iterator,
    Optional,
    Sequence,
    Set,
    TextIO,
    Tuple,
    TypeVar,
    Union,
)

from more_itertools import ichunked, peekable

import pyfastatools as ft
from pyfastatools.record import FastaFormat, FastaRecord, FastaRecordModifier
from pyfastatools._types import FilePath

_FastaIterator = Iterator[FastaRecord]
_T = TypeVar("_T")
_LabeledFastaIterator = Iterator[Tuple[_T, FastaRecord]]


class FastaIterator:
    def __init__(self, it: _FastaIterator) -> None:
        self._iter = it
        self._total = 0

    @property
    def total(self) -> int:
        return self._total

    @total.setter
    def total(self, value: int):
        if value < 0:
            raise ValueError("Cannot have a negative number of elements.")
        # 0 is reserved for unknown length
        self._total = value

    def __iter__(self) -> _FastaIterator:
        return self._iter

    #### SUBSET METHODS ####
    def take(self, n: int):
        ctx = self._iter
        self.total = n
        self._iter = islice(ctx, n)
        return self

    def fetch(self, keep: Set[str]):
        ctx = self._iter
        # TODO: set total here? could be wrong
        self._iter = (record for record in ctx if record.header.name in keep)
        return self

    def remove(self, remove: Set[str]):
        ctx = self._iter
        self._iter = (record for record in ctx if record.header.name not in remove)
        return self

    #######################

    def _split_into_chunks_unordered(self, n: int) -> _LabeledFastaIterator[int]:
        n_chunks = cycle(range(n))
        yield from zip(n_chunks, self)

    def _split_into_chunks_ordered(self, n: int) -> _LabeledFastaIterator[int]:
        # if self.total is 0 for unknown length, all chunks will be 1 seq
        # should use unordered method instead
        chunk_size = ceil(self.total / n)

        current_chunk = 0
        seqs_seen = 0
        for record in self:
            seqs_seen += 1

            if seqs_seen > chunk_size:
                seqs_seen = 1
                current_chunk += 1

            yield current_chunk, record

    def _split_into_chunks(
        self, n: int, ordered: bool = True
    ) -> Tuple[_LabeledFastaIterator[int], bool]:
        if ordered and self.total != 0:
            return self._split_into_chunks_ordered(n), True
        return self._split_into_chunks_unordered(n), False

    def split_into_chunks(
        self, n: int, ordered: bool = True
    ) -> "LabeledFastaIterator[int]":
        iterator, was_ordered = self._split_into_chunks(n, ordered)
        if was_ordered:
            return OrderedLabeledFastaIterator.from_packed_iterator(iterator)
        return LabeledFastaIterator.from_packed_iterator(iterator)

    def _split_uniformly(self, n: int) -> _LabeledFastaIterator[int]:
        for idx, subparser in enumerate(ichunked(self, n)):
            for record in subparser:
                yield idx, record

    def split_uniformly(self, n: int) -> "LabeledFastaIterator[int]":
        return LabeledFastaIterator.from_packed_iterator(self._split_uniformly(n))

    def _split_by_genome(self) -> _LabeledFastaIterator[str]:
        # TODO: take key file to map MAG names to single genome
        p = peekable(self)
        record = p.peek()
        if record is FastaFormat.GENOME:
            raise ValueError(
                f"{self.__class__.__name__} is parsing a genome file. "
                "Should be a protein or gene orf file."
            )

        for record in p:
            # use private method that does not check GENOME format since already checked
            genome, orf = record.header._split_genome_and_orf()
            yield genome, record

    def split_by_genome(self) -> "LabeledFastaIterator[str]":
        return OrderedLabeledFastaIterator.from_packed_iterator(self._split_by_genome())

    #######################

    #### EDIT METHODS ####
    @staticmethod
    def _deduplicate(ctx: _FastaIterator) -> _FastaIterator:
        seen: Set[str] = set()

        for record in ctx:
            if record.header.name not in seen:
                seen.add(record.header.name)
                yield record

    def deduplicate(self):
        ctx = self._iter
        self._iter = self._deduplicate(ctx)
        return self

    @staticmethod
    def _clean(ctx: _FastaIterator) -> _FastaIterator:
        for record in ctx:
            record.clean()
            yield record

    def clean(self):
        ctx = self._iter
        self._iter = self._clean(ctx)
        return self

    @staticmethod
    def _remove_stops(ctx: _FastaIterator) -> _FastaIterator:
        for record in ctx:
            record.remove_stops()
            yield record

    def remove_stops(self):
        ctx = self._iter
        self._iter = self._remove_stops(ctx)
        return self

    @staticmethod
    def _rename(
        ctx: _FastaIterator, mapping: Dict[str, str], keep_description: bool = False
    ) -> _FastaIterator:
        for record in ctx:
            # default just return same name
            record.header.name = mapping.get(record.header.name, record.header.name)
            if not keep_description:
                record.clean()
            yield record

    def rename(self, mapping: Dict[str, str], keep_description: bool = False):
        ctx = self._iter
        self._iter = self._rename(ctx, mapping, keep_description)
        return self

    @staticmethod
    def _map(
        ctx: _FastaIterator,
        funcs: Sequence[FastaRecordModifier],
        args: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> _FastaIterator:
        if args is None:
            args = [dict()] * len(funcs)
        for record in ctx:
            for func, arg in zip(funcs, args):
                func(record, **arg)
            yield record

    def map(
        self,
        funcs: Sequence[FastaRecordModifier],
        args: Optional[Sequence[Dict[str, Any]]] = None,
    ):
        ctx = self._iter
        self._iter = self._map(ctx, funcs, args)
        return self

    def write(self, fobj: TextIO, width: int = 75):
        for record in self._iter:
            record.write(fobj, width=width)

    def _cleanup(self):
        # prevent advancing iterator
        self._iter = iter([])

    def __add__(self, other: "FastaIterator") -> "FastaIterator":
        new = self.__class__(chain(self._iter, other._iter))
        self._cleanup()
        other._cleanup()
        return new

    def __iadd__(self, other: "FastaIterator") -> "FastaIterator":
        self._iter = chain(self._iter, other._iter)
        other._cleanup()
        return self

    def concat(self, other: Union["FastaIterator", "ft.FastaFile"]) -> "FastaIterator":
        if isinstance(other, ft.FastaFile):
            other = other.parse()

        self += other
        return self


class LabeledFastaIterator(FastaIterator, Generic[_T]):
    _iter: _FastaIterator
    _labels: Iterator[_T]

    def __init__(self, it: _FastaIterator, labels: Iterator[_T]):
        super().__init__(it)
        self._labels = labels

    @classmethod
    def from_packed_iterator(cls, it: _LabeledFastaIterator[_T]):
        it1, it2 = tee(it)
        fasta_iter = (record for _, record in it1)
        label_iter = (label for label, _ in it2)
        return cls(fasta_iter, label_iter)

    def __iter__(self):
        return zip(self._labels, self._iter)

    def write(self, outdir: FilePath = ".", width: int = 75):
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        for label, record in self:
            file = os.path.join(outdir, f"{label}.{record.format.extension}")
            with open(file, "a") as fp:
                record.write(fp, width=width)

    def fetch(self, keep: Set[str]):
        ctx = iter(self)
        it1, it2 = tee(
            ((label, record) for label, record in ctx if record.header.name in keep)
        )
        self._iter = (record for _, record in it1)
        self._labels = (label for label, _ in it2)
        return self

    def remove(self, remove: Set[str]):
        ctx = iter(self)
        it1, it2 = tee(
            (
                (label, record)
                for label, record in ctx
                if record.header.name not in remove
            )
        )
        self._iter = (record for _, record in it1)
        self._labels = (label for label, _ in it2)
        return self

    def _cleanup(self):
        # prevent advancing iterators
        self._iter = iter([])
        self._labels = iter([])

    def __add__(self, other: "LabeledFastaIterator") -> "LabeledFastaIterator":
        new = self.__class__(
            chain(self._iter, other._iter), chain(self._labels, other._labels)
        )
        self._cleanup()
        other._cleanup()
        return new

    def __iadd__(self, other: "LabeledFastaIterator") -> "LabeledFastaIterator":
        self._iter = chain(self._iter, other._iter)
        self._labels = chain(self._labels, other._labels)
        other._cleanup()
        return self

    def concat(self, other: "LabeledFastaIterator") -> "LabeledFastaIterator":
        self += other
        return self

    def split_into_chunks(self, n: int, ordered: bool = True):
        raise NotImplementedError()

    def split_uniformly(self, n: int):
        raise NotImplementedError()

    def split_by_genome(self):
        raise NotImplementedError()


class OrderedLabeledFastaIterator(LabeledFastaIterator):
    def write(self, outdir: FilePath = ".", width: int = 75):
        # slightly more efficient than base method since
        # we only need to open each file once

        if not os.path.exists(outdir):
            os.mkdir(outdir)

        # peek and get file ext
        self._iter = peekable(self._iter)
        extension = self._iter.peek().format.extension

        # groupby label
        groups = groupby(self, key=itemgetter(0))
        for label, group in groups:
            file = os.path.join(outdir, f"{label}.{extension}")
            with open(file, "w") as fp:
                for _, record in group:
                    record.write(fp, width=width)
