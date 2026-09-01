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
from functools import cached_property, total_ordering
from typing import Any, ClassVar, Iterator

from dwave.graphs.topologies.common.shape import TopologyShape

__all__ = ["Coord", "CoordKind"]


class CoordKind(Enum):
    """Kinds of coordinates of nodes in topologies."""

    CARTESIAN = auto()
    TOPOLOGY = auto()
    LINEAR = auto()


@total_ordering
class Coord(ABC):
    """A class to represent the coordinate of a topology node.

    Every concrete subclass must set the class variables ``topology_name``
    (the name of the topology it belongs to, e.g. ``"zephyr"``) and ``kind``
    (the :class:`CoordKind` it represents).
    """

    #: Name of the topology the class is designed for. Must be set by
    #: every concrete subclass, e.g. ``topology_name = "zephyr"``.
    topology_name: ClassVar[str]

    #: The kind of coordinate the class represents. Must be set by
    #: every concrete subclass, e.g. ``kind = CoordKind.CARTESIAN``.
    kind: ClassVar[CoordKind]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @abstractmethod
    def _args_valid_topology(self, *args, **kwargs) -> None:
        """Verifies the given coordinate is a valid coordinate."""

    @abstractmethod
    def is_shape_consistent(self, shape: TopologyShape) -> bool:
        """Tells whether the coordinate is consistent with a topology shape.

        Args:
            shape: The shape to check the consistency of the coordinate with.

        Returns:
            Whether the coordinate is consistent with the shape.
        """

    @abstractmethod
    def is_quotient(self) -> bool:
        """Whether the given coordinate is a quotient coordinate."""

    @abstractmethod
    def to_quotient(
        self,
    ) -> Coord:
        """Converts the coordinate to its corresponding coordinate in a quotient graph."""

    @abstractmethod
    def to_non_quotient(
        self,
        shape: TopologyShape,
        **kwargs,
    ) -> list[Coord]:
        """Expands the coordinate to a non-quotient shape; i.e. it gives
        all coordinates in a non-quotient graph whose quotient is the coordinate.

        Args:
            shape: The non-quotient shape to expand the coordinate to.

        Returns:
            The expansion of the coordinate into non-quotient.
        """

    @abstractmethod
    def convert(self, coord_kind: CoordKind) -> Coord:
        """Converts the coordinate to other kinds of coordinate in the same topology.

        Args:
            coord_kind: The coordinate kind to convert the coordinate to.

        Returns:
            The converted coordinate.
        """

    @abstractmethod
    def to_tuple(self) -> tuple:
        """Returns the tuple cooresponding to the coordinate."""

    @cached_property
    def _tuple_format(self) -> tuple[Any, ...]:
        """The tuple associated with the object."""
        return self.to_tuple()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return (
            self.is_quotient() == other.is_quotient() and self._tuple_format == other._tuple_format
        )

    def __lt__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return (self.is_quotient(), self._tuple_format) < (other.is_quotient(), other._tuple_format)

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
