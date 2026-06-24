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

from abc import ABC
from enum import Enum, auto
from functools import total_ordering
from typing import Any, Callable, ClassVar, Generator, Iterable, Type

from dwave.graphs.topologies.common.coord import Coord, CoordKind
from dwave.graphs.topologies.common.planeshift import TopologyPlaneShift
from dwave.graphs.topologies.common.shape import TopologyShape, _Infinite, _Quotient

__all__ = [
    "NodeKind",
    "TopologyNode",
    "EdgeKind",
    "Edge",
    "TopologyEdge",
    "NeighborContributorMixin",
    "HasInternalNeighborsMixin",
    "HasExternalNeighborsMixin",
    "HasOddNeighborsMixin",
]


class NodeKind(Enum):
    """Kinds of nodes in D-Wave topologies."""
    VERTICAL = auto()
    HORIZONTAL = auto()


class EdgeKind(Enum):
    """Kinds of edges in D-Wave topologies."""
    INVALID = auto()  # to represent non-valid edges in a given topology
    INTERNAL = auto()
    EXTERNAL = auto()
    ODD = auto()


# Note to developer:
# Any future additional EdgeKind requires its own corresponding
# subclass of :class:`NeighborContributorMixin` which has
# a method that generates neighbors of that kind.
# The EdgeKind togther with name of that method should be included in the dictionary.
EDGE_KINDS_CONTRIBUTOR_MAP = {
    EdgeKind.INTERNAL: "internal_neighbors",
    EdgeKind.EXTERNAL: "external_neighbors",
    EdgeKind.ODD: "odd_neighbors",
}


class Edge:
    """Represents an edge of a graph in a canonical order.

    Args:
        x: One endpoint of edge.
        y: Another endpoint of edge.

    ..note:: ``x`` and ``y`` must be mutually comparable.
    """

    def __init__(self, x: Any, y: Any) -> None:
        self._edge = self._set_edge(x, y)

    def _set_edge(self, x: Any, y: Any) -> tuple[Any, Any]:
        """Returns a canonical representation of the edge between x, y.

        Args:
        x: One endpoint of edge.
        y: Another endpoint of edge.

        Raises:
            NotImplementedError: To be implemented in the subclasses.

        Returns:
            tuple[Any, Any]: A canonical representation of the edge between x, y.
        """
        raise NotImplementedError

    def __hash__(self) -> int:
        return hash(self._edge)

    def __getitem__(self, index: int) -> int:
        return self._edge[index]

    def __eq__(self, other: object) -> bool:
        if not type(self) is type(other):
            return NotImplemented
        return self._edge == other._edge

    def __str__(self) -> str:
        return "(" + str(self._edge[0]) + ", " + str(self._edge[1]) + ")"

    def __repr__(self) -> str:
        return f"{type(self).__name__}{self._edge}"


class TopologyEdge(Edge):
    """A blueprint class to represent an edge of a D-Wave's topology graph in a canonical order.

    Args:
        x: One endpoint of edge.
        y: Another endpoint of edge.
        check_edge_valid:
            Flag to check whether the edge is a valid edge in the topology. Defaults to ``True``.

    Raises:
        TypeError: If an endpoint of edge does not belong to the
            topology node class associated with this class.
    """

    associated_topology_node: ClassVar[Type[TopologyNode]]

    @property
    def topology_name(cls) -> str:
        """Returns the name of the topology associated with the class.

        Raises:
            NotImplementedError: To be implemented in subclasses for
            specific topologies.

        Returns:
            str: The name of the topology the class is designed for.
        """
        if hasattr(cls, "_topology_name"):
            return cls._topology_name
        raise NotImplementedError

    def __init__(
        self,
        x: TopologyNode,
        y: TopologyNode,
        check_edge_valid: bool = True,
    ) -> None:
        self._edge_kind = None
        if check_edge_valid:
            self._check_edge_valid(x, y)
        super().__init__(x, y)

    def _check_edge_valid(self, x: TopologyNode, y: TopologyNode) -> None:
        """Checks whether the edge is a valid edge in the topology.

        Args:
            x: One endpoint of edge.
            y: Another endpoint of edge. Must have the same type as ``x``.

        Raises:
            TypeError: If the endpoints have different types.
            ValueError: If the endpoints of the edge have different shapes.
            ValueError: If the edge is not a valid edge in the topology.
        """
        if x.shape != y.shape:
            raise ValueError(
                f"Expected x, y to have the same shape, got {x.shape, y.shape}")

        self._edge_kind = self._find_edge_kind(x, y)
        if self._edge_kind is EdgeKind.INVALID:
            raise ValueError(
                f"{x, y} are not neighbors in {self.topology_name}")

    def _find_edge_kind(self, x: TopologyNode, y: TopologyNode) -> EdgeKind:
        """Finds the kind of edge in the topology.

        Args:
            x: One endpoint of edge.
            y: Another endpoint of edge.

        Returns:
            EdgeKind: The kind of edge in the topology.
        """
        for kind in self.associated_topology_node.supported_edgekinds():
            if x.is_neighbor(y, nbr_kind=kind):
                return kind
        return EdgeKind.INVALID

    @property
    def edge_kind(self) -> EdgeKind:
        """The kind of edge in the topology."""
        if self._edge_kind is None:
            self._edge_kind = self._find_edge_kind(*self._edge)
        return self._edge_kind


@total_ordering
class TopologyNode(ABC):
    """
    A blueprint class to represent the node of a topology.

    ..note:: For a subclass, the methods that have to do with the edges
        incident with a node, such as neighbors, degree, ... require that
        the subclass is also a subclass of a subclass of :class:`NeighborContributorMixin`.

    Args:
        coord: Coordinate of the node.
        shape: Shape of the topology graph the node belongs to.
            Defaults to ``None``.
        coord_kind:
            The kind of coordinate the node is represented with.
                - Defaults to ``None``.
                - If ``None``, it is set based on ``coord``.
        check_node_valid:
            Flag to check whether the node is a valid node in the topology. Defaults to ``True``.
    """

    associated_topology_edge: ClassVar[Type[TopologyEdge]]

    def __init__(
        self,
        coord: Coord | tuple[int | _Quotient, ...],
        shape: TopologyShape | tuple[int |
                                     _Quotient | _Infinite, ...] | None = None,
        coord_kind: CoordKind | None = None,
        check_node_valid: bool = True,
    ) -> None:
        self._shape = self._set_shape(
            shape=shape, check_shape_valid=check_node_valid)

        self._coord_kind = self._set_coord_kind(
            coord=coord,
            coord_kind=coord_kind,
        )

        self._ccoord = self._set_ccoord(
            coord=coord, check_coord_valid=check_node_valid)

    @classmethod
    def topology_name(cls) -> str:
        """Returns the name of the topology associated with the class.

        Raises:
            NotImplementedError: To be implemented in subclasses for
            specific topology nodes.

        Returns:
            str: The name of the topology the class is designed for.
        """
        if hasattr(cls, "_topology_name"):
            return cls._topology_name
        raise NotImplementedError

    @classmethod
    def supported_edgekinds(cls) -> dict[EdgeKind, type]:
        """Gives the edge kinds incident with the nodes of this class.

        Returns:
            dict[EdgeKind, type]: A dictionary whose
                - keys are edge kinds incident with a typical node.
                - Values are subclasses of :class:`NeighborContributor`
                    whose associated_edgekind is the given key.
        """
        edgekind_cls_map: dict[EdgeKind, type] = {}
        for parent_class in cls.__mro__:
            if NeighborContributorMixin in parent_class.__bases__ and hasattr(
                parent_class, "associated_edgekind"
            ):
                edgekind_cls_map[parent_class.associated_edgekind] = parent_class
        return edgekind_cls_map

    def _set_shape(
        self,
        shape: TopologyShape | tuple[int | _Quotient | _Infinite, ...] | None,
        check_shape_valid: bool,
    ) -> TopologyShape:
        """Sets the shape of the topology graph the node belongs to.

        Args:
            shape: Shape of the topology graph the node belongs to.
            check_shape_valid:
                Flag to check whether the shape is a valid shape for the topology.

        Raises:
            NotImplementedError: To be implemented in subclasses for
                specific topology nodes.

        Returns:
            TopologyShape: Shape of the topology graph the node belongs to.
        """
        raise NotImplementedError

    def _set_coord_kind(
        self, coord: Coord | tuple[int | _Quotient, ...], coord_kind: CoordKind | None
    ) -> CoordKind:
        """Gives the coordinate kind that the node is represented with.

        Args:
            coord: Coordinate of the node.
            coord_kind: The coordinate kind to represent the node with.

        Raises:
            NotImplementedError: To be implemented in subclasses for
                specific topology nodes.

        Returns:
            CoordKind: The coordinate kind that the node is represented with.
        """
        raise NotImplementedError

    def _set_ccoord(
        self,
        coord: Coord | tuple[int | _Quotient, ...],
        check_coord_valid: bool,
    ) -> Coord:
        """Gives the canonical coordinate of the node to use in class methods' computations.

        Args:
            coord: Coordinate of the node.
            check_coord_valid: Flag to check whether the coordinate is valid in the topology.

        Raises:
            NotImplementedError: To be implemented in subclasses.

        Returns:
            Coord: The canonical coordinate of the node.
        """
        raise NotImplementedError

    @property
    def coord_kind(self) -> CoordKind:
        """The kind of coordinate the node is represented with."""
        return self._coord_kind

    @property
    def topology_coord(self) -> Coord:
        """The topology coordinate of the node.

        Raises:
            NotImplementedError: To be implemented in subclasses.

        Returns:
            Coord: The topology coordinate of the node.
        """
        raise NotImplementedError

    @property
    def shape(self) -> TopologyShape:
        """The shape of the topology graph the node belongs to."""
        return self._shape

    @property
    def node_kind(self) -> NodeKind:
        """The kind of node."""
        raise NotImplementedError

    @property
    def direction(self) -> int:
        """The direction of the qubit the node is representing."""
        _node_kind = self.node_kind
        if _node_kind is NodeKind.VERTICAL:
            return 0
        elif _node_kind is NodeKind.HORIZONTAL:
            return 1
        else:
            raise AssertionError(f"Unhandled NodeKind value: {_node_kind}")

    def is_quotient(self) -> bool:
        """Tells if the node is quotient."""
        return self._ccoord.is_quotient() and self._shape.is_quotient()

    def to_quotient(self) -> TopologyNode:
        """Returns the quotient node corresponding to the node."""
        return self.__class__(
            coord=self._ccoord.to_quotient(),
            shape=self._shape.to_quotient(),
            coord_kind=self.coord_kind,
            check_node_valid=False,
        )

    def to_non_quotient(self, shape: TopologyShape) -> list[TopologyNode]:
        """Gives all nodes in a non-quotient graph whose quotient is the node.

        Args:
            shape: The non-quotient shape to expand the node to.

        Returns:
            list[TopologyNode]: The expansion of the node into non-quotient.
        """
        non_quo_coords = self._ccoord.to_non_quotient(shape=shape)
        return [
            self.__class__(coord=coord, shape=shape,
                           coord_kind=self.coord_kind)
            for coord in non_quo_coords
        ]

    @property
    def coord(self) -> Coord:
        """Coordinate of the node, expressed in the coordinate system the node is represented with to the user."""
        return (self._ccoord).convert(self.coord_kind)

    def is_vertical(self) -> bool:
        """Tells if the node represents a vertical qubit."""
        return self.node_kind is NodeKind.VERTICAL

    def is_horizontal(self) -> bool:
        """Tells if the node represents a horizontal qubit."""
        return self.node_kind is NodeKind.HORIZONTAL

    def neighbor_edge_kind(
        self,
        other: TopologyNode,
    ) -> EdgeKind:
        """Returns the kind of edge between two nodes.

        Args:
            other: Another topology node.

        Returns:
            EdgeKind: The edge kind between the two nodes in perfect yield topology.
        """
        if type(self) is not type(other):
            return NotImplemented
        try:
            return self.associated_topology_edge(self, other).edge_kind
        except ValueError:
            return EdgeKind.INVALID

    def neighbors(
        self,
        nbr_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> Generator[TopologyNode, None, None]:
        """Generates neighbors of the node when restricted by
            the kind of edge between the node and the neighbors and coordinate.

        Args:
            nbr_kind:
                Edge kind filter. Restricts yielded neighbors to those connected
                    by the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            where: A coordinate filter. Defaults to always.

        Yields:
            TopologyNode: Neighbors of the node when restricted by ``nbr_kind`` and ``where``.
        """

        edgekind_cls_map = self.supported_edgekinds()

        base_edgekinds = {kind for kind in edgekind_cls_map}
        if nbr_kind is None:
            output_edgekinds = base_edgekinds
        else:
            if isinstance(nbr_kind, EdgeKind):
                nbr_kind = {nbr_kind}
            output_edgekinds = set(nbr_kind).intersection(base_edgekinds)
        for kind in output_edgekinds:
            if kind not in EDGE_KINDS_CONTRIBUTOR_MAP:
                raise NotImplementedError(
                    f"Edge contributor class not implemented for {kind}")
            else:
                method_name = EDGE_KINDS_CONTRIBUTOR_MAP[kind]
                method = getattr(self, method_name)
                yield from method(where=where)

    def is_neighbor(
        self,
        other: TopologyNode,
        nbr_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> bool:
        """Tells whether another node is a neighbor of the node
            when restricted by edge kind and coordinate.

        Args:
            other: Another node.
            nbr_kind:
                Edge kind filter. Restricts neighbor to be connected to the node
                    by the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            where:
                A coordinate filter. Defaults to always.

        Returns:
            bool: Whether ``other`` is a neighbor of the node when
                restricted by ``nbr_kind`` and ``where``.
        """
        return other in self.neighbors(nbr_kind=nbr_kind, where=where)

    def incident_edges(
        self,
        nbr_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> Generator[TopologyEdge, None, None]:
        """Returns the edges incident with the node when restricted
            by edge kind and coordinate.

        Args:
            nbr_kind:
                Edge kind filter. Restricts returned edges to those having the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            where: A coordinate filter. Defaults to always.

        Returns:
            list[TopologyEdge]: List of edges incident with self when restricted by ``nbr_kind`` and ``where``.
        """
        for v in self.neighbors(nbr_kind=nbr_kind, where=where):
            yield self.associated_topology_edge(self, v)

    def degree(
        self,
        nbr_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> int:
        """Returns degree of the node when restricted by edge kind and coordinate.

        Args:
            nbr_kind:
                Edge kind filter. Restricts counting the neighbors to those connected by the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            where:
                A coordinate filter. Defaults to always.

        Returns:
            int: degree of the node when restricted by ``nbr_kind`` and ``where``.
        """
        return len(list(self.neighbors(nbr_kind=nbr_kind, where=where)))

    def __add__(self, shift: TopologyPlaneShift | tuple[int, int]) -> TopologyNode:
        """Shifts the node in the Cartesian plane.

        Args:
            shift: Shift to be applied to the node.

        Raises:
            NotImplementedError: To be implemented in subclasses.

        Returns:
            TopologyNode: The shifted node.
        """
        raise NotImplementedError

    def __sub__(self, other: TopologyNode) -> TopologyPlaneShift:
        """Finds the displacement between the node and another node.

        Args:
            other: The node to find the displacement with.

        Raises:
            NotImplementedError: To be implemented in subclasses.

        Returns:
            TopologyPlaneShift: The displacement whose application to the node moves it to the other node.
        """
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if not (type(self) is type(other) and self._shape == other._shape):
            return NotImplemented
        return self._ccoord == other._ccoord

    def __lt__(self, other: object) -> bool:
        if not (type(self) is type(other) and self._shape == other._shape):
            return NotImplemented
        return self._ccoord < other._ccoord

    def __hash__(self) -> int:
        return hash((type(self), self._shape, self._ccoord))

    def __repr__(self) -> str:
        coord = (self._ccoord).convert(self._coord_kind)
        return f"{type(self).__name__}{coord, self._shape, self._coord_kind}"

    def __str__(self) -> str:
        coord = (self._ccoord).convert(self._coord_kind)
        return f"{coord.to_tuple(), self._shape.to_tuple()}"


class NeighborContributorMixin:
    """A blueprint for a neighbor contributor class for a topology node."""

    associated_edgekind: EdgeKind


class HasInternalNeighborsMixin(NeighborContributorMixin):
    """A class to encapsulate methods for internal coupler featuring topologies."""

    associated_edgekind = EdgeKind.INTERNAL

    def internal_neighbors(
        self,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> Generator[TopologyNode, None, None]:
        """Generates internal neighbors of a node when restricted by coordinate.

        Args:
            where: A coordinate filter. Defaults to always.

        Raises:
            NotImplementedError: To be implemented in subclasses.

        Yields:
            TopologyNode: Internal neighbors of the node when restricted by ``where``.
        """
        raise NotImplementedError

    def is_internal_neighbor(
        self,
        other: TopologyNode,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> bool:
        """Tells whether a node is an internal neighbor of the node
            when restricted by coordinate.

        Args:
            other: The other node to check whether the node is
                an internal neighbor of.
            where: A coordinate filter. Defaults to always.

        Returns:
            bool: Whether the other node is an internal neighbor
                of the node when restricted by ``where``.
        """
        return other in self.internal_neighbors(where=where)


class HasExternalNeighborsMixin(NeighborContributorMixin):
    """A class to encapsulate methods for external coupler featuring topologies."""

    associated_edgekind = EdgeKind.EXTERNAL

    def external_neighbors(
        self,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> Generator[TopologyNode, None, None]:
        """Generates external neighbors of a node when restricted by coordinate.

        Args:
            where: A coordinate filter. Defaults to always.

        Raises:
            NotImplementedError: To be implemented in subclasses.

        Yields:
            TopologyNode: External neighbors of the node when restricted by ``where``.
        """
        raise NotImplementedError

    def is_external_neighbor(
        self,
        other: TopologyNode,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> bool:
        """Tells whether a node is an external neighbor of the node
            when restricted by coordinate.

        Args:
            other: The other node to check whether the node is
                an external neighbor of.
            where: A coordinate filter. Defaults to always.

        Returns:
            bool: Whether the other node is an external neighbor
                of the node when restricted by ``where``.
        """
        return other in self.external_neighbors(where=where)


class HasOddNeighborsMixin(NeighborContributorMixin):
    """A class to encapsulate methods for odd coupler featuring topologies."""

    associated_edgekind = EdgeKind.ODD

    def odd_neighbors(
        self,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> Generator[TopologyNode, None, None]:
        """Generates odd neighbors of a node when restricted by coordinate.

        Args:
            where : A coordinate filter. Defaults to always.

        Raises: NotImplementedError: To be implemented in subclasses.

        Yields:
            TopologyNode: Odd neighbors of the node when restricted by ``where``.
        """
        raise NotImplementedError

    def is_odd_neighbor(
        self,
        other: TopologyNode,
        where: Callable[[Coord], bool] = lambda coord: True,
    ) -> bool:
        """Tells whether a node is an odd neighbor of the node
            when restricted by coordinate.

        Args:
            other: The other node to check whether the node is
                an odd neighbor of.
            where: A coordinate filter. Defaults to always.

        Returns:
            bool: Whether the other node is an odd neighbor
                of the node when restricted by ``where``.
        """
        return other in self.odd_neighbors(where=where)
