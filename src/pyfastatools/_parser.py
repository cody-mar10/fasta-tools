from functools import cached_property
from pathlib import Path
from typing import Iterator, Optional

from pyfastatools._fastatools import Header, Headers, Record, Records, RecordType
from pyfastatools._fastatools import Parser as _Parser
from pyfastatools._types import FilePath

RecordIterator = Iterator[Record]
HeaderIterator = Iterator[Header]


class Parser:
    def __init__(self, file: FilePath):

        self.file = file
        if isinstance(file, Path):
            # C++ parser expects a string, not a Path object
            file = file.as_posix()

        self._parser = _Parser(file)

    def __iter__(self):
        return self

    def __next__(self) -> Record:
        return self._parser.py_next()

    @cached_property
    def num_records(self) -> int:
        """Get the number of records in the file."""
        return self._parser.count()

    @property
    def format(self) -> RecordType:
        """Get the format of the file."""
        return self._parser.type

    @property
    def extension(self) -> str:
        """Get the file extension based on the record type."""
        return self._parser.extension()

    def __len__(self) -> int:
        """Get the number of records in the file."""
        return self.num_records

    def all(self) -> Records:
        """Get all records in the file as a list-like object.

        Returns:
            Records: A list-like object storing all records in the file.
        """
        return self._parser.all()

    def take(self, n: int) -> Records:
        """Get the next n records in the file.

        Args:
            n (int): The number of records to take.

        Returns:
            Records: A list-like object storing the next n records in the file. If there are fewer
                than n records in the file, the returned list will be shorter than n.
        """
        return self._parser.take(n)

    def refresh(self):
        """Reset the file pointer to the beginning of the file."""
        self._parser.refresh()

    def next_header(self) -> Header:
        """Get the next header in the file."""
        return self._parser.next_header()

    def headers(self) -> HeaderIterator:
        """Iterate over all headers in the file."""
        self.refresh()
        while True:
            try:
                yield self._parser.py_next_header()
            except StopIteration:
                break

    def all_headers(self) -> Headers:
        """Get all headers in the file as a list-like object."""
        return self._parser.headers()

    ### SUBSET METHODS ###

    def _keep(self, subset: set[str], unique_headers: bool) -> RecordIterator:
        num_to_keep = len(subset)
        num_kept = 0

        for record in self:
            if (record.header.name in subset) or (record.header.to_string() in subset):
                yield record
                num_kept += 1

            if unique_headers and num_kept == num_to_keep:
                # early stopping if all records have been included
                break

    def _remove(self, subset: set[str], unique_headers: bool) -> RecordIterator:
        num_to_exclude = len(subset)
        num_excluded = 0

        for record in self:
            # stop checking str equality if we've already excluded all records requested
            if (unique_headers and num_excluded == num_to_exclude) or (
                record.header.name not in subset
                and record.header.to_string() not in subset
            ):
                yield record
            else:
                num_excluded += 1

    def filter(
        self,
        include: Optional[set] = None,
        exclude: Optional[set] = None,
        unique_headers: bool = False,
    ) -> RecordIterator:
        """Filter records based on the provided include or exclude sets.

        Args:
            include (Optional[set], optional): A set of headers to include. Defaults to None.
            exclude (Optional[set], optional): A set of headers to exclude. Defaults to None.
            unique_headers (bool, optional): whether it is assumed that the headers are unique.
                If True, this will enable shortcircuiting when the total number of records have been included or excluded. Defaults to False.

        Returns:
            RecordIterator: An iterator over the filtered records.

        Raises:
            ValueError: If both include and exclude are None or if both are provided.
        """
        if include is None and exclude is None:
            raise ValueError("At least one of include or exclude must be provided")
        elif include is not None and exclude is not None:
            raise ValueError("Only one of include or exclude can be provided")

        self.refresh()

        if include is not None:
            return self._keep(include, unique_headers)

        if exclude is not None:
            return self._remove(exclude, unique_headers)

        raise RuntimeError("UNREACHABLE")

    def first(self) -> Record:
        """Get the first record in the file."""
        self.refresh()
        return next(self)

    def last(self) -> Record:
        """Get the last record in the file."""
        for record in self:
            pass
        self.refresh()
        return record

    ### EDIT METHODS ###

    def deduplicate(self) -> RecordIterator:
        """Iterate over all records in the file, removing duplicates, BASED ONLY ON THE HEADER."""
        seen: set[str] = set()
        for record in self:
            if record.header.name not in seen:
                yield record
            seen.add(record.header.name)

    def clean(self) -> RecordIterator:
        """Iterate over all records in the file, cleaning the headers.

        This removes all characters after the first space.
        """
        for record in self:
            record.clean_header()
            yield record

    def remove_stops(self) -> RecordIterator:
        """Iterate over all records in the file, removing stop codons."""
        for record in self:
            record.remove_stops()
            yield record

    # TODO: for subsetting
    # add method to read subset file...?
    # actually can just have that be defined elsewhere
    # - rename method?

    # TODO: add split methods
    # - into n files
    # - into n seqs per file
    # - split by genome
