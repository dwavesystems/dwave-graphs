# Copyright 2026 D-Wave
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from functools import cached_property
from typing import Any, ClassVar, Iterator

__all__ = [
    "_Quotient",
    "_Infinite",
    "TopologyShape",
]


class _Quotient(Enum):
    QUOTIENT = auto()

    def __repr__(self):
        return "<QUOTIENT>"


class _Infinite(Enum):
    INFINITE = auto()

    def __repr__(self):
        return "<INFINITE>"


QUOTIENT = _Quotient.QUOTIENT
INFINITE = _Infinite.INFINITE


class TopologyShape(ABC):
    """A class to represent the shape parameters associated with a topology.

    Every concrete subclass must set the class variable ``topology_name``
    (the name of the topology it belongs to, e.g. ``"zephyr"``).

    Args:
        m: The grid size of topology. Defaults to ``_Infinite.INFINITE``.
        t: The tile size of topology. Defaults to ``_Quotient.QUOTIENT``.
        check_shape_valid: Flag to whether to check the
            parameters are valid on instantiation. Defaults to ``True``.
    """

    #: Name of the topology the class is designed for. Must be set by
    #: every concrete subclass, e.g. ``topology_name = "zephyr"``.
    topology_name: ClassVar[str]

    def __init__(
        self,
        m: int | _Infinite = _Infinite.INFINITE,
        t: int | _Quotient = _Quotient.QUOTIENT,
        check_shape_valid: bool = True,
        *args,
        **kwargs,
    ) -> None:
        if check_shape_valid:
            self._args_are_valid(m, t, *args, **kwargs)
        self.m = m
        self.t = t

    @abstractmethod
    def _args_are_valid(self, m: int | _Infinite, t: int | _Quotient, *args, **kwargs) -> None:
        """Checks whether the given parameters are valid for a topology shape.

        Args:
            m: The grid size of topology.
            t: The tile size of topology.
        """

    @abstractmethod
    def to_quotient(self) -> TopologyShape:
        """Converts the shape to its corresponding quotient shape.

        Returns:
            TopologyShape: The shape converted to its corresponding quotient shape.
        """

    @abstractmethod
    def is_quotient(self) -> bool:
        """Tells whether the shape represents a quotient shape.

        Returns:
            bool: Whether the shape is quotient.
        """

    @abstractmethod
    def to_infinite(self) -> TopologyShape:
        """Converts the shape to its corresponding infinite grid size shape.

        Returns:
            TopologyShape: The shape converted to its corresponding infinite grid size shape.
        """

    @abstractmethod
    def is_infinite(self) -> bool:
        """Tells whether the shape represents a shape with infinite grid size.

        Returns:
            bool: Whether the shape represents a shape with infinite grid size.
        """

    @abstractmethod
    def to_tuple(self) -> tuple[int, int]:
        """Returns the pair of values that uniquely identifies the shape."""

    @cached_property
    def _tuple_format(self) -> tuple[Any, ...]:
        """The tuple associated with the object."""
        return self.to_tuple()

    def __eq__(self, value: object) -> bool:
        if type(self) is not type(value):
            return NotImplemented
        return self._tuple_format == value._tuple_format

    def __hash__(self) -> int:
        return hash((type(self), self._tuple_format))

    def __iter__(self) -> Iterator[Any]:
        return iter(self._tuple_format)

    def __len__(self) -> int:
        return len(self._tuple_format)

    def __getitem__(self, i: int) -> Any:
        return self._tuple_format[i]

    def __repr__(self) -> str:
        return f"{type(self).__name__}{self._tuple_format}"

    def __str__(self) -> str:
        return f"{self._tuple_format}"
