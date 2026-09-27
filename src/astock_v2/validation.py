"""Time-ordered walk-forward validation primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence, TypeVar

T=TypeVar("T")

@dataclass(frozen=True)
class WalkForwardWindow:
    train: tuple[T,...]
    test: tuple[T,...]
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def walk_forward_windows(items: Sequence[T], *, train_size: int, test_size: int, step: int | None = None) -> tuple[WalkForwardWindow,...]:
    if train_size<=0 or test_size<=0: raise ValueError("train_size and test_size must be positive")
    step=test_size if step is None else step
    if step<=0: raise ValueError("step must be positive")
    windows=[]; start=0
    while start+train_size+test_size<=len(items):
        train_end=start+train_size; test_end=train_end+test_size
        windows.append(WalkForwardWindow(tuple(items[start:train_end]),tuple(items[train_end:test_end]),start,train_end,train_end,test_end))
        start+=step
    return tuple(windows)
