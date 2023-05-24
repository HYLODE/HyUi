"""
Utility functions for web pages
"""
import numpy as np
import pandas as pd
import time
from contextlib import ContextDecorator
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Dict, Optional


def gen_id(name: str, dunder_name: str) -> str:
    module_name = dunder_name.split(".")[-2].upper()
    name = name.replace("_", "-").replace(" ", "-").replace(".", "-")
    return f"{module_name}-{name}"


def time_since(when: pd.Series, units: str = "D") -> pd.Series:
    """
    Time since 'when' in units as per np.timedelta64
    e.g.  (D)ay, (M)onth, (Y)ear, (h)ours, (m)inutes,
    or (s)econds

    Accepts a pandas series
    Returns a float in the appropriate units
    defaults to days
    """
    try:
        res = (pd.Timestamp.now() - when.apply(pd.to_datetime)) / np.timedelta64(
            1, units
        )
    except TypeError as e:
        print(e)
        res = np.NaN
    return res


def unpack_nested_baserow_dict(
    rows: list[dict],
    f2unpack: str,
    subkey: str,
    new_name: str = "",
) -> list[dict]:
    # noinspection GrazieInspection,DuplicatedCode
    """
    Unpack fields with nested dictionaries into a pipe separated string

    :param      rows:  The rows
    :param      f2unpack:  field to unpack
    :param      subkey:  key within nested dictionary to use
    :param      new_name: new name for field else overwrite if None

    :returns:   { description_of_the_return_value }
    """
    for row in rows:
        i2unpack = row.get(f2unpack, [])
        vals = [i.get(subkey, "") for i in i2unpack]
        vals_str = "|".join(vals)
        if new_name:
            row[new_name] = vals_str
        else:
            row.pop(f2unpack, None)
            row[f2unpack] = vals_str
    return rows


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


@dataclass
class Timer(ContextDecorator):
    """Time your code using a class, context manager, or decorator"""

    # via https://realpython.com/python-timer/#the-python-timer-code

    timers: ClassVar[Dict[str, float]] = {}
    name: Optional[str] = None
    text: str = "Elapsed time: {:0.4f} seconds"
    logger: Optional[Callable[[str], None]] = print
    _start_time: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialization: add timer to dict of timers"""
        if self.name:
            self.timers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None

        # Report elapsed time
        if self.logger:
            self.logger(self.text.format(elapsed_time))
        if self.name:
            self.timers[self.name] += elapsed_time

        return elapsed_time

    def __enter__(self) -> "Timer":
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        """Stop the context manager timer"""
        self.stop()
