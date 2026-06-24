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
#
# ================================================================================================


from __future__ import annotations
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any, Iterator

__all__ = [
    "_Quotient",
    "QUOTIENT",
    "_Infinite",
    "INFINITE",
    "TopologyShape",
]


class _Quotient:
    """An object to represent the Quotient graph of a topology."""

    def __new__(cls):
        raise TypeError("QUOTIENT is not to be instantiated")

    def __str__(self) -> str:
        return "<QUOTIENT>"

    def __repr__(self) -> str:
        return "<QUOTIENT>"


QUOTIENT = object.__new__(_Quotient)  # Unique instance of _Quotient


class _Infinite:
    """An object to represent an infinte grid size of the topology."""

    def __new__(cls):
        raise TypeError("INFINITE is not to be instantiated")

    def __str__(self) -> str:
        return "<INFINITE>"

    def __repr__(self) -> str:
        return "<INFINITE>"


INFINITE = object.__new__(_Infinite)  # Unique instance of _Infinite


class TopologyShape(ABC):
    """A class to represent the shape parameters associated with a topology.

    Args:
        m: The grid size of topology. Defaults to ``INFINITE``.
        t: The tile size of topology. Defaults to ``QUOTIENT``.
        check_shape_valid: Flag to whether to check the
            parameters are valid on instantiation. Defaults to ``True``.
    """

    @property
    def topology_name(cls) -> str:
        """Returns the name of the topology associated with the class.

        Returns:
            str: The name of the topology the class is designed for.
        """
        if hasattr(cls, "_topology_name"):
            return cls._topology_name
        raise NotImplementedError

    def __init__(
        self,
        m: int | _Infinite = INFINITE,
        t: int | _Quotient = QUOTIENT,
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
