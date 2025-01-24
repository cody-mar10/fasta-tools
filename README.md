# FASTA file parsing written in C++ with Python bindings

## Installation

```bash
pip install pyfastatools
```

## Usage

The `pyfastatools.Parser` object is the primary API that parses FASTA files and yields `pyfastatools.Record` objects.

If you have a FASTA file called `proteins.faa` that looks like this:

```txt
>seq_1
MSKFKKIPL
>seq_2
MQSSSKTCN
>seq_3
MEDNMITIY
```

Then you can parse this file in python like this:

```python
from pyfastatools import Parser

for record in Parser("proteins.faa"):
    print(record.header.name, record.seq)
```

which will print:

```python
>>> 'seq_1 MSKFKKIPL'
>>> 'seq_2 MQSSSKTCN'
>>> 'seq_3 MEDNMITIY'
```

## API

This library has a very simple API that can be displayed in a few lines:

### Parser

This is the main class that will satisfy 99% of user needs. While parsing FASTA files, it produces `Record` objects. Only the name of a FASTA file is needed:

```python
pyfastatools.Parser("my_fasta.fasta")
```

The parser will attempt to auto-detect the `RecordType` of the file by checking the input file extension and the first 5 sequences.

However, the record type can optionally be specified:

```python
pyfastatools.Parser("my_fasta.fasta", pyfastatools.RecordType.PROTEIN)
```

The parser can be iterated over to yield one `Record` at a time:

```python
parser = pyfastatools.Parser("my_fasta.fasta")
for record in parser:
    ...
```

#### Methods

There are also other convenience methods:

- `all` - Read all records into a list-like object.
- `take` - Take up to n records into a list-like object.
- `filter` - Keep/exclude sequences based on the sequence name.
- `remove_stops` - Yield sequences without a `*` stop codon character if the sequences are proteins.
- `clean_header` - Yield sequences while cleaning the header to not have a description.
- `headers` - Yield `Header` objects only without parsing the sequence itself.
- `all_headers` - Return all headers into a list-like object.

#### Properties

- `num_records` - Returns the number of sequences in the FASTA file. This is cached after the first time it is called. Note: This can also be computed using `len(parser)`
- `format` - Returns the `RecordType` enum that corresponds to the FASTA file's record type
- `extension` - Returns the file extension based on the `format`

### Record

A single FASTA record. It has the following fields:

- `header` - A `Header` object that has the fields `name` and `desc`
- `seq` - A `str` storing the entire sequence

#### Methods

- `empty` - Checks if the `Header` and sequence are empty
- `clear` - Sets the `Header` and sequence to empty strings
- `to_string` - Returns the record as a string representation identical to what was parsed from the file
- `clean_header` - Sets the `Header` description to an empty string
- `remove_stops` - Removes `*` stop codon characters from the sequence if they are present
