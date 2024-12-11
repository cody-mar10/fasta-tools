from pathlib import Path

from pydantic import BaseModel, Field, FilePath


class _IOArgs(BaseModel):
    input: FilePath = Field(description="input fasta file")


class SingleOutputArgs(_IOArgs):
    output: Path = Field(description="output fasta file")


class MultipleOutputArgs(_IOArgs):
    outdir: Path = Field(description="output directory")
