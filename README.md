# C++ bindings for FASTA file parsing

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
    print(record.name, record.seq)
```

which will print:

```python
>>> 'seq_1 MSKFKKIPL'
>>> 'seq_2 MQSSSKTCN'
>>> 'seq_3 MEDNMITIY'
```
