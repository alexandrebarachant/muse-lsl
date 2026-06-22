"""LSL stream metadata shared by legacy Muse and Muse S Athena."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamDescriptor:
    name: str
    stype: str
    n_channels: int
    channel_names: tuple
    rate: float
    chunk: int
    unit: str
