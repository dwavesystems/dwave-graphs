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

from itertools import product
from typing import Callable, Generator

from dwave.graphs.topologies.common.coords import CoordKind
from dwave.graphs.topologies.common.node_edge import (
    EdgeKind,
    ExternalNeighborsMixin,
    InternalNeighborsMixin,
    NodeKind,
    OddNeighborsMixin,
    TopologyEdge,
    TopologyNode,
)
from dwave.graphs.topologies.common.shape import Infinite, Quotient, QUOTIENT
from dwave.graphs.topologies.zephyr.coords import ZephyrCartesianCoord, ZephyrCoord
from dwave.graphs.topologies.zephyr.planeshift import ZephyrPlaneShift
from dwave.graphs.topologies.zephyr.shape import ZephyrShape

__all__ = ["ZephyrEdge", "ZephyrNode"]


class ZephyrEdge(TopologyEdge):
    """Represents an edge in a graph with Zephyr topology in a canonical order.

    Args:
        x: Endpoint of edge. Must have same shape as ``y``.
        y: Another endpoint of edge. Must have same shape as ``x``
        check_edge_valid: Flag to whether check the validity of values and types of ``x``, ``y``.
            Defaults to ``True``.
        edge_kind: The kind of the edge, for callers that already know it.
            If ``None``, the kind is derived from the endpoints on first
            access to :attr:`edge_kind`. Defaults to ``None``.

    Raises:
        TypeError: If either of x or y is not an instance of :class:`ZephyrNode`.
        ValueError: If x, y do not have the same shape.
        ValueError: If x, y are not neighbors in a perfect yield (quotient)
            Zephyr graph.

    Example 1:
        >>> from dwave.graphs import ZephyrNode, ZephyrEdge
        >>> e = ZephyrEdge(ZephyrNode((3, 2)), ZephyrNode((7, 2)))
        >>> print(e)
        (((3, 2, <QUOTIENT>), (<INFINITE>, <QUOTIENT>)), ((7, 2, <QUOTIENT>), (<INFINITE>, <QUOTIENT>)))

    Example 2:
        Endpoints that are not neighbors in the topology raise an error.

        >>> from dwave.graphs import ZephyrNode, ZephyrEdge
        >>> ZephyrEdge(ZephyrNode((2, 3)), ZephyrNode((6, 3)))
        Traceback (most recent call last):
            ...
        ValueError: ... are not neighbors in zephyr
    """

    topology_name = "zephyr"

    def __init__(
        self,
        x: ZephyrNode,
        y: ZephyrNode,
        check_edge_valid: bool = True,
        edge_kind: EdgeKind | None = None,
    ) -> None:
        super().__init__(x, y, check_edge_valid, edge_kind)


def _neighbor_ccoords(
    ccoord: ZephyrCartesianCoord,
    shape: ZephyrShape,
    edge_kind: EdgeKind,
) -> Generator[ZephyrCartesianCoord, None, None]:
    """Generates the Cartesian coordinates adjacent to ``ccoord`` by ``edge_kind``.

    This is the single definition of Zephyr adjacency; :class:`ZephyrNode`'s
    neighbor generators and
    :class:`~dwave.graphs.topologies.zephyr.zephyr.Zephyr`'s edge generators
    both derive from it.

    Args:
        ccoord: The Cartesian coordinate to generate the neighbors of.
        shape: The shape of the Zephyr graph the coordinate belongs to.
        edge_kind: The kind of coupler to follow.

    Raises:
        NotImplementedError: If ``edge_kind`` has no adjacency rule.

    Yields:
        The neighbors of ``ccoord`` that are consistent with ``shape``.
    """
    x, y, k = ccoord
    match edge_kind:
        case EdgeKind.INTERNAL:
            # The four diagonally adjacent positions, across every tile index.
            k_vals = [QUOTIENT] if shape.t is QUOTIENT else range(shape.t)
            candidates = (
                (x + dx, y + dy, k_val) for dx, dy in product((-1, 1), (-1, 1)) for k_val in k_vals
            )
        case EdgeKind.EXTERNAL | EdgeKind.ODD:
            # Four (external) or two (odd) positions along the parallel direction.
            step = 4 if edge_kind is EdgeKind.EXTERNAL else 2
            offsets = ((0, -step), (0, step)) if x % 2 == 0 else ((-step, 0), (step, 0))
            candidates = ((x + dx, y + dy, k) for dx, dy in offsets)
        case _:
            raise NotImplementedError(f"No Zephyr adjacency rule for {edge_kind}")

    for new_x, new_y, k_val in candidates:
        if new_x < 0 or new_y < 0:
            continue
        neighbor = ZephyrCartesianCoord(x=new_x, y=new_y, k=k_val, check_coord=False)
        if neighbor.is_shape_consistent(shape):
            yield neighbor


class ZephyrNode(
    TopologyNode,
    InternalNeighborsMixin,
    ExternalNeighborsMixin,
    OddNeighborsMixin,
):
    """Represents a node of a graph with Zephyr topology with coordinate and optional shape,
    coordinate kind representation and node validation.

    Args:
        coord: Coordinate in (quotient) Zephyr graph.
        shape: shape of Zephyr graph containing the node.
            Defaults to ``None``.
        coord_kind: The kind of coordinate the node is represented with.
            If ``None``, it is inferred from ``coord``.
            Defaults to ``None``.
        check_node_valid: Flag to whether check the validity of values and types of ``coord``
            and ``shape``. Defaults to ``True``.

    ..note::

        If the given coord has non-None ``k`` value (in either Cartesian or Zephyr coordinates),
        ``shape = None`` raises ValueError. In this case the tile size of Zephyr, t,
        must be provided.

    Example:
        >>> from dwave.graphs import ZephyrNode, ZephyrShape
        >>> from dwave.graphs.topologies.common import EdgeKind
        >>> zn1 = ZephyrNode((5, 2), ZephyrShape(m=5))
        >>> list(zn1.neighbors())  # doctest: +SKIP
        [ZephyrNode(ZephyrCartesianCoord(1, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(9, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(4, 1, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(4, 3, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(6, 1, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(6, 3, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(3, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(7, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>)]
        >>> list(zn1.neighbors(nbr_kind=EdgeKind.ODD))  # doctest: +SKIP
        [ZephyrNode(ZephyrCartesianCoord(3, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>),
        ZephyrNode(ZephyrCartesianCoord(7, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 1>)]
    """

    associated_topology_edge = ZephyrEdge

    topology_name = "zephyr"

    def __init__(
        self,
        coord: (
            ZephyrCartesianCoord
            | ZephyrCoord
            | tuple[int, int, int | Quotient]
            | tuple[int, int, int | Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
        shape: ZephyrShape | tuple[int | Infinite, int | Quotient] | None = None,
        coord_kind: CoordKind | None = None,
        check_node_valid: bool = True,
    ) -> None:
        super().__init__(
            coord=coord,
            shape=shape,
            coord_kind=coord_kind,
            check_node_valid=check_node_valid,
        )

    def _find_shape(
        self,
        shape: ZephyrShape | tuple[int | Quotient | Infinite, ...] | None,
        check_shape_valid: bool,
    ) -> ZephyrShape:
        """Finds the shape of the Zephyr graph the node belongs to.

        Args:
            shape: Shape of the Zephyr graph the node belongs to.
            check_shape_valid: Flag to check whether the shape is valid for Zephyr.

        Raises:
            ValueError: If the shape is not a valid Zephyr shape.

        Returns:
            Shape of the Zephyr graph the node belongs to.
        """
        if shape is None:
            return ZephyrShape()
        if isinstance(shape, ZephyrShape):
            return shape
        try:
            return ZephyrShape(*shape, check_shape_valid=check_shape_valid)
        except (ValueError, TypeError) as e:
            raise ValueError(f"{shape} cannot be converted to :class:`ZephyrShape`") from e

    def _find_coord_kind(
        self,
        coord: (
            ZephyrCartesianCoord
            | ZephyrCoord
            | tuple[int, int, int | Quotient]
            | tuple[int, int, int | Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
        coord_kind: CoordKind | None,
    ) -> CoordKind:
        """Finds the coordinate kind that the node is represented with.

        Args:
            coord: Coordinate of the node.
            coord_kind:The coordinate kind to represent the node with.

        Returns:
            The coordinate kind that the node is represented with.
        """
        if coord_kind is not None:
            return coord_kind
        if len(coord) in [2, 3]:
            return CoordKind.CARTESIAN
        return CoordKind.TOPOLOGY

    def _tuple_to_coord(
        self,
        coord: (
            tuple[int, int, int | Quotient]
            | tuple[int, int, int | Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
    ) -> ZephyrCoord | ZephyrCartesianCoord:
        """Converts a coordinate to a Zephyr coordinate.

        Args:
            coord: A coordinate.

        Raises:
            ValueError: If the length of tuple is 2 or 3 and
                it cannot be converted to a :class:`ZephyrCartesianCoord`.
            ValueError: If the length of tuple is 4 or 5 and
                it cannot be converted to a :class:`ZephyrCoord`.

        Returns:
            The Zephyr coordinate the coordinate corresponds to.
        """
        if len(coord) == 2:
            coord = (coord[0], coord[1], QUOTIENT)
        elif len(coord) == 4:
            coord = (coord[0], coord[1], QUOTIENT, coord[2], coord[3])

        if len(coord) == 3:
            try:
                return ZephyrCartesianCoord(*coord)
            except (ValueError, TypeError):
                raise ValueError(f"{coord} cannot be converted to :class:`ZephyrCartesianCoord`.")
        try:
            return ZephyrCoord(*coord)
        except (ValueError, TypeError):
            raise ValueError(f"{coord} cannot be converted to :class:`ZephyrCoord`.")

    def _find_ccoord(
        self,
        coord: (
            ZephyrCartesianCoord
            | ZephyrCoord
            | tuple[int, int, int | Quotient]
            | tuple[int, int, int | Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
        check_coord_valid: bool,
    ) -> ZephyrCartesianCoord:
        """Finds the Cartesian coordinate of the node as a canonical coordinate
            to use in class methods' computations.

        Args:
            coord: Coordinate of the node.
            check_coord_valid: Flag to check whether the coordinate is valid in Zephyr.

        Returns:
            The Cartesian coordinate of the node.
        """
        if isinstance(coord, tuple):
            coord = self._tuple_to_coord(coord)
        if isinstance(coord, ZephyrCoord):
            coord = coord.convert(CoordKind.CARTESIAN)
        if check_coord_valid:
            coord._args_valid_topology(*coord)
            if not coord.is_shape_consistent(self._shape):
                raise ValueError(f"{coord} is not consistent with {self._shape}")
        return coord

    @property
    def ccoord(self) -> ZephyrCartesianCoord:
        """The Cartesian coordinate of the node."""
        return self._ccoord

    @property
    def zcoord(self) -> ZephyrCoord:
        """The Zephyr coordinate of the node."""
        return (self._ccoord).convert(CoordKind.TOPOLOGY)

    @property
    def topology_coord(self) -> ZephyrCoord:
        """The topology (Zephyr) coordinate of the node."""
        return self.zcoord

    @property
    def node_kind(self) -> NodeKind:
        """The kind of the node."""
        if self._ccoord.x % 2 == 0:
            return NodeKind.VERTICAL
        return NodeKind.HORIZONTAL

    def internal_neighbors(
        self,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord], bool] | None = None,
    ) -> Generator[ZephyrNode, None, None]:
        """Generator of internal neighbors of a Zephyr node when
            restricted by coordinate.
        Args:
            where: A coordinate filter. Applies to
                -``ccoord`` if :py:attr:`self.coord_kind` is ``CoordKind.CARTESIAN``,
                -``zcoord`` if :py:attr:`self.coord_kind` is ``CoordKind.TOPOLOGY``.
                - Defaults to ``None``.
        Yields:
            Internal neighbors of the node when restricted by ``where``.
        """
        yield from self._neighbors_of_kind(EdgeKind.INTERNAL, where=where)

    def _neighbors_of_kind(
        self,
        edge_kind: EdgeKind,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord], bool] | None = None,
    ) -> Generator[ZephyrNode, None, None]:
        """Turns the coordinates from :func:`_neighbor_ccoords` into nodes.

        Args:
            edge_kind: The kind of coupler to follow.
            where: A coordinate filter. Defaults to ``None``.

        Yields:
            The neighbors joined by ``edge_kind``, when restricted by ``where``.
        """
        for ccoord in _neighbor_ccoords(self._ccoord, self._shape, edge_kind):
            coord = ccoord.convert(self._coord_kind)
            if (where is not None) and (not where(coord)):
                continue
            yield ZephyrNode(
                coord=coord,
                shape=self._shape,
                coord_kind=self._coord_kind,
            )

    def external_neighbors(
        self,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord], bool] | None = None,
    ) -> Generator[ZephyrNode, None, None]:
        """Generator of external neighbors of a Zephyr node when
            restricted by coordinate.
        Args:
            where: A coordinate filter. Applies to
                -``ccoord`` if :py:attr:`self.coord_kind` is ``CoordKind.CARTESIAN``,
                -``zcoord`` if :py:attr:`self.coord_kind` is ``CoordKind.TOPOLOGY``.
                - Defaults to ``None``.
        Yields:
            External neighbors of node when restricted by ``where``.
        """
        yield from self._neighbors_of_kind(EdgeKind.EXTERNAL, where=where)

    def odd_neighbors(
        self,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord], bool] | None = None,
    ) -> Generator[ZephyrNode, None, None]:
        """Generator of odd neighbors of of a Zephyr node when
            restricted by ``where``.
        Args:
            where: A coordinate filter. Applies to
                -``ccoord`` if :py:attr:`self.coord_kind` is ``CoordKind.CARTESIAN``,
                -``zcoord`` if :py:attr:`self.coord_kind` is ``CoordKind.TOPOLOGY``.
                - Defaults to ``None``.
        Yields:
            Odd neighbors of node when restricted by ``where``.
        """
        yield from self._neighbors_of_kind(EdgeKind.ODD, where=where)

    def __add__(self, shift: ZephyrPlaneShift | tuple[int, int]) -> ZephyrNode:
        """Shifts the node in the Zephyr Cartesian plane.

        Args:
            shift: Shift to be applied to the node.

        Raises:
            ValueError: If the shift cannot be converted to a :class:`ZephyrPlaneShift` object.

        Returns:
            The shifted node.
        """
        if not isinstance(shift, ZephyrPlaneShift):
            try:
                shift = ZephyrPlaneShift(*shift)
            except (ValueError, TypeError) as e:
                raise ValueError(f"{shift} cannot be converted to :class:`ZephyrPlaneShift`") from e
        x, y, k = self._ccoord
        new_x = x + shift[0]
        new_y = y + shift[1]

        return ZephyrNode(
            coord=ZephyrCartesianCoord(x=new_x, y=new_y, k=k),
            shape=self._shape,
            coord_kind=self._coord_kind,
        )

    def __sub__(self, other: ZephyrNode) -> ZephyrPlaneShift:
        """Finds the displacement between the node and another node.

        Args:
            other: The node to find the displacement with.

        Raises:
            ValueError: If there is no valid shift in Zephyr Cartesian plane
                that moves the other node to this node.

        Returns:
            The displacement that when added to the other node moves it to
            this node; that is, ``other + (self - other) == self``.

        Example:
            >>> from dwave.graphs import ZephyrNode, ZephyrShape
            >>> a, b = ZephyrNode((7, 4), ZephyrShape(6)), ZephyrNode((5, 2), ZephyrShape(6))
            >>> a - b
            ZephyrPlaneShift(2, 2)
            >>> b + (a - b) == a
            True
        """
        x_shift: int = self._ccoord.x - other._ccoord.x
        y_shift: int = self._ccoord.y - other._ccoord.y
        try:
            return ZephyrPlaneShift(x=x_shift, y=y_shift)
        except ValueError as e:
            raise ValueError(f"{other} cannot be subtracted from {self}") from e


ZephyrEdge.associated_topology_node = ZephyrNode
