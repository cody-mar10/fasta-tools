from functools import cached_property
from pathlib import Path
from typing import Iterator, Literal, Optional

from pyfastatools._fastatools import (
    Header,
    Headers,
    ProdigalHeader,
    ProdigalHeaders,
    Record,
    Records,
    RecordType,
)
from pyfastatools._fastatools import Parser as _Parser
from pyfastatools._types import FilePath
from pyfastatools.utils import write_fasta

RecordIterator = Iterator[Record]
HeaderIterator = Iterator[Header]
ProdigalHeaderIterator = Iterator[ProdigalHeader]


class Parser:
    file: Path

    def __init__(self, file: FilePath):
        if isinstance(file, Path):
            self.file = file

            # C++ parser expects a string, not a Path object
            file = file.as_posix()
        else:
            self.file = Path(file)

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
        """Get the file extension based on the record type.

        Note: This includes the . in the extension.
        """
        return self._parser.extension()

    @property
    def is_prodigal(self) -> bool:
        """Check if the file is a Prodigal-formatted protein FASTA file."""
        return self._parser.is_prodigal

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

    def next_prodigal_header(self) -> ProdigalHeader:
        """Get the next prodigal header in the file.

        Raises:
            RuntimeError: If the file is not prodigal formatted.
        """
        return self._parser.next_prodigal_header()

    def prodigal_headers(self) -> ProdigalHeaderIterator:
        """Iterate over all prodigal headers in the file.

        Raises:
            RuntimeError: If the file is not prodigal formatted.
            StopIteration: If there are no more headers.
        """
        self.refresh()
        while True:
            try:
                yield self._parser.py_next_prodigal_header()
            except StopIteration:
                break

    def all_prodigal_headers(self) -> ProdigalHeaders:
        """Get all prodigal headers in the file as a list-like object.

        Raises:
            RuntimeError: If the file is not prodigal formatted.
        """
        return self._parser.prodigal_headers()

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

        raise RuntimeError("UNREACHABLE")  # pragma: no cover

    def first(self) -> Record:
        """Get the first record in the file."""
        self.refresh()
        return next(self)

    def last(self) -> Record:
        """Get the last record in the file."""

        # reset if at EOF, otherwise we don't need to refresh
        # initially to get the last record quicker
        if not self._parser.has_next():  # pragma: no cover <- this is tested
            self.refresh()

        for record in self:
            pass

        self.refresh()

        # this works without an UnboundLocalError since empty files will raise TypeErrors
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

    ### SPLIT METHODS ###
    def _split_by_genome(self, outdir: Path):
        if self.format not in {RecordType.GENE, RecordType.PROTEIN}:
            raise ValueError(
                "Cannot split by genome for this file format. Must be a gene or protein file."
            )

        # check first record for header format
        header = self.first().header.name
        fields = header.rsplit("_", 1)
        if len(fields) == 1:
            raise ValueError(
                f"ORF headers must be in this format: <genome>_<ORF number>. Found: {header}"
            )

        self.refresh()
        ext = self.extension
        for record in self:
            header = record.header.name
            genome = header.rsplit("_", 1)[0]
            outpath = outdir / f"{genome}{ext}"
            with open(outpath, "a") as fdst:
                write_fasta(record, fdst)

    def _write_n_seqs_to_file(self, outpath: Path, n: int):
        records = self.take(n)
        with open(outpath, "w") as fdst:
            for record in records:
                write_fasta(record, fdst)

    def _split_into_n_files(self, outdir: Path, n: int):
        """Writes sequences in order to n files."""
        ext = self.extension
        base_name = self.file.stem

        num_records = self.num_records
        even_seqs_per_file, rem = divmod(num_records, n)
        num_per_file = [even_seqs_per_file] * n

        # distribute the remainder
        for i in range(rem):
            num_per_file[i] += 1

        for file_idx, num_seqs in enumerate(num_per_file):
            outpath = outdir / f"{base_name}_{file_idx}{ext}"
            self._write_n_seqs_to_file(outpath, num_seqs)

    def _split_n_seqs_per_file(self, outdir: Path, n: int):
        """Writes n sequences to each file in order."""
        ext = self.extension
        base_name = self.file.stem

        num_records = self.num_records
        num_files, rem = divmod(num_records, n)
        if rem:
            # write remaining records to a new file so that each file has no more than n records
            num_files += 1

        for file_idx in range(num_files):
            outpath = outdir / f"{base_name}_{file_idx}{ext}"
            self._write_n_seqs_to_file(outpath, n)

    def split(
        self,
        outdir: FilePath,
        method: Literal["genome", "n_files", "n_seqs_per_file"],
        n: Optional[int] = None,
    ):
        """Split the file into multiple files.

        Args:
            outdir (FilePath): The directory to write the split files to.
            method (Literal["genome", "n_files", "n_seqs_per_file"]): The method to use for
                splitting the file.
            n (Optional[int], optional): The number of files or sequences per file. Defaults to
                None. This will raise a ValueError if not provided for the "n_files" and
                "n_seqs_per_file" methods.

        Raises:
            ValueError: If the method is not recognized or if n is not provided when required.
        """
        if not isinstance(outdir, Path):
            outdir = Path(outdir)

        outdir.mkdir(exist_ok=True, parents=True)

        if method == "genome":
            self._split_by_genome(outdir)
            return

        if n is None:
            raise ValueError(
                "n must be provided for the 'n_files' and 'n_seqs_per_file' methods."
            )

        if method == "n_files":
            self._split_into_n_files(outdir, n)
            return

        if method == "n_seqs_per_file":
            self._split_n_seqs_per_file(outdir, n)
            return

        raise ValueError(f"Unrecognized method: {method}")

    # TODO: need to figure out a way to write from python with C++

    # TODO: for subsetting
    # add method to read subset file...?
    # actually can just have that be defined elsewhere
    # - rename method?
