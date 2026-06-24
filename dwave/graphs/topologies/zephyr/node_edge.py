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

from itertools import product
from typing import Callable, Generator, Literal

from dwave.graphs.topologies.common.coord import CoordKind
from dwave.graphs.topologies.common.node_edge import (
    HasExternalNeighborsMixin,
    HasInternalNeighborsMixin,
    HasOddNeighborsMixin,
    NodeKind,
    TopologyEdge,
    TopologyNode,
)
from dwave.graphs.topologies.common.shape import QUOTIENT, _Infinite, _Quotient
from dwave.graphs.topologies.zephyr.coord import ZephyrCartesianCoord, ZephyrCoord
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

    Raises:
        TypeError: If either of x or y is not an instance of :class:`ZephyrNode`.
        ValueError: If x, y do not have the same shape.
        ValueError: If x, y are not neighbors in a perfect yield (quotient)
            Zephyr graph.

    Example 1:
    >>> from dwave.graphs import ZephyrNode, ZephyrEdge
    >>> e = ZephyrEdge(ZephyrNode((3, 2)), ZephyrNode((7, 2)))
    >>> print(e)
    ZephyrEdge(ZephyrNode(ZephyrCartesianCoord(x=3, y=2, k = QUOTIENT)), ZephyrNode(ZephyrCartesianCoord(x=7, y=2, k = QUOTIENT)))
    Example 2:
    >>> from dwave.graphs import ZephyrNode, ZephyrEdge
    >>> ZephyrEdge(ZephyrNode((2, 3)), ZephyrNode((6, 3))) # raises error, since the two are not neighbors
    """

    _topology_name = "zephyr"

    def __init__(
        self,
        x: ZephyrNode,
        y: ZephyrNode,
        check_edge_valid: bool = True,
    ) -> None:
        super().__init__(x, y, check_edge_valid)

    def _set_edge(self, x: ZephyrNode, y: ZephyrNode) -> tuple[ZephyrNode, ZephyrNode]:
        """Returns a canonical representation of the edge between x, y.

        Args:
            x: Endpoint of edge.
            y: Another endpoint of edge.

        Returns:
            tuple[ZephyrNode, ZephyrNode]: An ordered tuple corresponding to the edge between x, y.
        """
        return (x, y) if x < y else (y, x)


class ZephyrNode(
    TopologyNode, HasInternalNeighborsMixin, HasExternalNeighborsMixin, HasOddNeighborsMixin
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
        check_node_valid: Flag to whether check the validity of values and types of ``coord``, ``shape``.
            Defaults to ``True``.

    ..note::

        If the given coord has non-None ``k`` value (in either Cartesian or Zephyr coordinates),
        ``shape = None`` raises ValueError. In this case the tile size of Zephyr, t,
        must be provided.

    Example:
    >>> from znode_edge import ZephyrNode, ZephyrShape
    >>> zn1 = ZephyrNode((5, 2), ZephyrShape(m=5))
    >>> list(zn1.neighbors())
    [ZephyrNode(ZephyrCartesianCoord(1, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(9, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(4, 1, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(4, 3, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(6, 1, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(6, 3, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(3, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(7, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>)]
    >>> from minorminer.utils.zephyr.node_edge import ZephyrNode, ZephyrShape
    >>> zn1 = ZephyrNode((5, 2), ZephyrShape(m=5))
    >>> list(zn1.neighbors(nbr_kind=EdgeKind.ODD))
    [ZephyrNode(ZephyrCartesianCoord(3, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>),
    ZephyrNode(ZephyrCartesianCoord(7, 2, <QUOTIENT>), ZephyrShape(5, <QUOTIENT>), <CoordKind.CARTESIAN: 0>)]
    """

    associated_topology_edge = ZephyrEdge

    _topology_name = "zephyr"

    def __init__(
        self,
        coord: (
            ZephyrCartesianCoord
            | ZephyrCoord
            | tuple[int, int, int | _Quotient]
            | tuple[int, int, int | _Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
        shape: ZephyrShape | tuple[int | _Infinite,
                                   int | _Quotient] | None = None,
        coord_kind: CoordKind | None = None,
        check_node_valid: bool = True,
    ) -> None:
        super().__init__(
            coord=coord,
            shape=shape,
            coord_kind=coord_kind,
            check_node_valid=check_node_valid,
        )

    def _set_shape(
        self,
        shape: ZephyrShape | tuple[int | _Quotient | _Infinite, ...] | None,
        check_shape_valid: bool,
    ) -> ZephyrShape:
        """Sets the shape of the Zephyr graph the node belongs to.

        Args:
            shape: Shape of the Zephyr graph the node belongs to.
            check_shape_valid: Flag to check whether the shape is valid for Zephyr.

        Raises:
            ValueError: If the shape is not a valid Zephyr shape.

        Returns:
            ZephyrShape: Shape of the Zephyr graph the node belongs to.
        """
        if shape is None:
            return ZephyrShape()
        try:
            return ZephyrShape(*shape, check_shape_valid=check_shape_valid)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"{shape} cannot be converted to :class:`ZephyrShape`") from e

    def _set_coord_kind(
        self,
        coord: (
            ZephyrCartesianCoord
            | ZephyrCoord
            | tuple[int, int, int | _Quotient]
            | tuple[int, int, int | _Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
        coord_kind: CoordKind | None,
    ) -> CoordKind:
        """Gives the coordinate kind that the node is represented with.

        Args:
            coord: Coordinate of the node.
            coord_kind:The coordinate kind to represent the node with.

        Returns:
            CoordKind: The coordinate kind that the node is represented with.
        """
        if coord_kind is not None:
            return coord_kind
        if len(coord) in [2, 3]:
            return CoordKind.CARTESIAN
        return CoordKind.TOPOLOGY

    def _tuple_to_coord(
        self,
        coord: (
            tuple[int, int, int | _Quotient]
            | tuple[int, int, int | _Quotient, int, int]
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
            ZephyrCoord | ZephyrCartesianCoord:
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
                raise ValueError(
                    f"{coord} cannot be converted to :class:`ZephyrCartesianCoord`.")
        try:
            return ZephyrCoord(*coord)
        except (ValueError, TypeError):
            raise ValueError(
                f"{coord} cannot be converted to :class:`ZephyrCoord`.")

    def _set_ccoord(
        self,
        coord: (
            ZephyrCartesianCoord
            | ZephyrCoord
            | tuple[int, int, int | _Quotient]
            | tuple[int, int, int | _Quotient, int, int]
            | tuple[int, int]
            | tuple[int, int, int, int]
        ),
        check_coord_valid: bool,
    ) -> ZephyrCartesianCoord:
        """Gives the Cartesian coordinate of the node as a canonical coordinate
            to use in class methods' computations.

        Args:
            coord: Coordinate of the node.
            check_coord_valid: Flag to check whether the coordinate is valid in Zephyr.

        Returns:
            Coord: The Cartesian coordinate of the node.
        """
        if isinstance(coord, tuple):
            coord = self._tuple_to_coord(coord)
        if isinstance(coord, ZephyrCoord):
            coord = coord.convert(CoordKind.CARTESIAN)
        if check_coord_valid:
            coord._args_valid_topology(*coord)
            if not coord.is_shape_consistent(self._shape):
                raise ValueError(
                    f"{coord} is not consistent with {self._shape}")
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
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord],
                        bool] = lambda coord: True,
    ) -> Generator[ZephyrNode, None, None]:
        """Generator of internal neighbors of a Zephyr node when
            restricted by coordinate.
        Args:
            where: A coordinate filter. Applies to
                -``ccoord`` if :py:attr:`self.coord_kind` is ``CoordKind.CARTESIAN``,
                -``zcoord`` if :py:attr:`self.coord_kind` is ``CoordKind.TOPOLOGY``.
                - Defaults to always.        Yields:
            ZephyrNode: Internal neighbors of the node when restricted by ``where``.
        """
        x, y, _ = self._ccoord
        k_vals = [QUOTIENT] if self._shape.t is QUOTIENT else range(
            self._shape.t)
        for i, j, k in product((-1, 1), (-1, 1), k_vals):
            try:
                ccoord = ZephyrCartesianCoord(
                    x=x + i, y=y + j, k=k, check_coord=True)
                # Check ccoord is consistent with shape
                if ccoord.is_shape_consistent(self._shape):
                    coord = ccoord.convert(self._coord_kind)
                    if not where(coord):
                        continue
                    yield ZephyrNode(coord=coord, shape=self._shape, coord_kind=self._coord_kind)
            except ValueError:
                continue

    def external_neighbors(
        self,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord],
                        bool] = lambda coord: True,
    ) -> Generator[ZephyrNode, None, None]:
        """Generator of external neighbors of a Zephyr node when
            restricted by coordinate.
        Args:
            where: A coordinate filter. Applies to
                -``ccoord`` if :py:attr:`self.coord_kind` is ``CoordKind.CARTESIAN``,
                -``zcoord`` if :py:attr:`self.coord_kind` is ``CoordKind.TOPOLOGY``.
                - Defaults to always.
        Yields:
            ZephyrNode: External neighbors of node when restricted by ``where``.
        """
        x, y, k = self._ccoord
        changing_index = 1 if x % 2 == 0 else 0
        for s in [-4, 4]:
            new_x = x + s if changing_index == 0 else x
            new_y = y + s if changing_index == 1 else y
            try:
                ccoord = ZephyrCartesianCoord(
                    x=new_x, y=new_y, k=k, check_coord=True)
                if ccoord.is_shape_consistent(self._shape):
                    coord = ccoord.convert(self._coord_kind)
                    if not where(coord):
                        continue
                    yield ZephyrNode(coord=coord, shape=self._shape, coord_kind=self._coord_kind)
            except ValueError:
                continue

    def odd_neighbors(
        self,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord],
                        bool] = lambda coord: True,
    ) -> Generator[ZephyrNode, None, None]:
        """Generator of odd neighbors of of a Zephyr node when
            restricted by ``where``.
        Args:
            where: A coordinate filter. Applies to
                -``ccoord`` if :py:attr:`self.coord_kind` is ``CoordKind.CARTESIAN``,
                -``zcoord`` if :py:attr:`self.coord_kind` is ``CoordKind.TOPOLOGY``.
                - Defaults to always.
        Yields:
            ZephyrNode: Odd neighbors of node when restricted by ``where``.
        """
        x, y, k = self._ccoord
        changing_index = 1 if x % 2 == 0 else 0
        for s in [-2, 2]:
            new_x = x + s if changing_index == 0 else x
            new_y = y + s if changing_index == 1 else y
            try:
                ccoord = ZephyrCartesianCoord(
                    x=new_x, y=new_y, k=k, check_coord=True)
                if ccoord.is_shape_consistent(self._shape):
                    coord = ccoord.convert(self._coord_kind)
                    if not where(coord):
                        continue
                    yield ZephyrNode(coord=coord, shape=self._shape, coord_kind=self._coord_kind)
            except ValueError:
                continue

    def __add__(self, shift: ZephyrPlaneShift | tuple[int, int]) -> ZephyrNode:
        """Shifts the node in the Zephyr Cartesian plane.

        Args:
            shift: Shift to be applied to the node.

        Raises:
            ValueError: If the shift cannot be converted to a :class:`ZephyrPlaneShift` object.

        Returns:
            ZephyrNode: The shifted node.
        """
        if not isinstance(shift, ZephyrPlaneShift):
            try:
                shift = ZephyrPlaneShift(*shift)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"{shift} cannot be converted to :class:`ZephyrPlaneShift`") from e
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
                that moves the node to the other node.

        Returns:
            ZephyrPlaneShift: The displacement that when added to the node moves it to the other node.
        """
        x_shift: int = self._ccoord.x - other._ccoord.x
        y_shift: int = self._ccoord.y - other._ccoord.y
        try:
            return ZephyrPlaneShift(x=x_shift, y=y_shift)
        except ValueError as e:
            raise ValueError(
                f"{other} cannot be subtracted from {self}") from e


ZephyrEdge.associated_topology_node = ZephyrNode
