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


from itertools import product
from typing import Generator, Iterable

import networkx as nx

from dwave.graphs.topologies.common import CoordKind, EdgeKind, Topology, _Infinite, _Quotient
from dwave.graphs.topologies.zephyr.coords import ZephyrCartesianCoord, ZephyrCoord
from dwave.graphs.topologies.zephyr.graphs import zephyr_graph
from dwave.graphs.topologies.zephyr.node_edge import ZephyrEdge, ZephyrNode
from dwave.graphs.topologies.zephyr.planeshift import ZephyrPlaneShift
from dwave.graphs.topologies.zephyr.shape import ZephyrShape

__all__ = ["Zephyr"]


class Zephyr(Topology):
    """A class to access various classes associated with D-Wave's Zephyr topology."""

    _planeshift_class = ZephyrPlaneShift
    _shape_class = ZephyrShape
    _node_class = ZephyrNode
    _edge_class = ZephyrEdge

    def __init__(self, coord_kind: CoordKind = CoordKind.TOPOLOGY):

        match coord_kind:
            case CoordKind.TOPOLOGY:
                self._coord_class = ZephyrCoord
            case CoordKind.CARTESIAN:
                self._coord_class = ZephyrCartesianCoord
            case CoordKind.LINEAR:
                raise NotImplementedError("Zephyr does not support linear coordinates")
            case _:
                raise ValueError("invalid coord kind")

        super().__init__()

    @staticmethod
    def create_graph(
        shape: tuple[int, int] | ZephyrShape,
        create_using: nx.Graph | None = None,
        node_list: Iterable | None = None,
        edge_list: Iterable | None = None,
        data: bool = True,
        coordinates: bool = False,
        check_node_list: bool = False,
        check_edge_list: bool = False,
    ) -> nx.Graph:
        """Creates a Zephyr graph with a given shape.

        Args:
            shape: The shape of the Zephyr graph, given either as a
                ``(m, t)`` tuple or a :class:`ZephyrShape` instance.
            create_using: If provided, this graph is cleared of nodes and
                edges and filled with the new graph. Usually used to set
                the type of the graph. Defaults to ``None``.
            node_list: Iterable of nodes in the graph. If not specified,
                calculated from ``shape`` and ``coordinates``. Defaults to ``None``.
            edge_list: Iterable of edges in the graph. If not specified,
                calculated from ``shape``, ``node_list``, and ``coordinates``.
                Defaults to ``None``.
            data: If ``True``, adds a ``'zephyr_index'`` or ``'linear_index'``
                attribute to each node, depending on ``coordinates``.
                Defaults to ``True``.
            coordinates: If ``True``, node labels are 5-tuple Zephyr indices
                instead of linear indices. Defaults to ``False``.
            check_node_list: If ``True``, checks ``node_list`` elements for
                compatibility with the graph topology and node labeling
                conventions. Defaults to ``False``.
            check_edge_list: If ``True``, checks ``edge_list`` elements for
                compatibility with the graph topology and node labeling
                conventions. Defaults to ``False``.

        Returns:
            A Zephyr graph with the given shape.
        """
        return zephyr_graph(*shape, create_using, node_list, edge_list, data, coordinates,
                            check_node_list, check_edge_list)

    def _find_shape(
        self, shape: ZephyrShape | tuple[int | _Infinite, int | _Quotient]
    ) -> ZephyrShape:
        """Finds the Zephyr shape of the graph.

        Args:
            shape: The shape of Zephyr graph.

        Raises:
            ValueError: If shape is not a valid Zephyr shape.

        Returns:
            The shape of the Zephyr graph.
        """
        if not isinstance(shape, ZephyrShape):
            try:
                shape = ZephyrShape(*shape)
            except (ValueError, TypeError):
                raise ValueError(
                    f"{shape} cannot be an instance of ZephyrShape")
        return shape

    def nodes(
        self,
        shape: ZephyrShape | tuple[int | _Infinite, int | _Quotient],
        coord_kind: CoordKind = CoordKind.CARTESIAN,
    ) -> set[ZephyrNode]:
        """Returns the nodes of a Zephyr graph.

        Args:
            shape: The shape of the Zephyr graph.
            coord_kind: The kind of coordinate the edges endpoints are represented with.
                Defaults to ``CoordKind.CARTESIAN``.
        Raises:
            ValueError: If the grid size of the shape is ``_Infinite.INFINITE``.

        Returns:
            The nodes of the Zephyr graph.
        """
        if coord_kind is CoordKind.LINEAR:
            raise NotImplementedError("Zephyr does not support linear coordinates")

        shape = self._find_shape(shape)
        if shape.m is _Infinite.INFINITE:
            raise ValueError(
                "Cannot generate infinite number of nodes!\nProvide a finite grid size."
            )
        m, t = shape
        nodes = set()
        range_x = range(4 * m + 1)
        range_t = [_Quotient.QUOTIENT] if t is _Quotient.QUOTIENT else range(t)
        for x in range_x:
            if x % 2 == 0:
                range_y = range(1, 4 * m + 1, 2)
            else:
                range_y = range(0, 4 * m + 1, 2)
            for y, k in product(range_y, range_t):
                nodes.add(
                    ZephyrNode(
                        coord=ZephyrCartesianCoord(x, y, k),
                        shape=shape,
                        coord_kind=coord_kind,
                        check_node_valid=False,
                    )
                )
        return nodes

    def edges(
        self,
        shape: ZephyrShape | tuple[int | _Infinite, int | _Quotient],
        edge_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        coord_kind: CoordKind = CoordKind.CARTESIAN,
    ) -> set[ZephyrEdge]:
        """Returns the edges of a Zephyr graph with a shape and optional
            coordinate and edge kind.

        Args:
            shape: The shape of Zephyr graph.
            edge_kind: Edge kind filter. Restricts edges to the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            coord_kind: The kind of coordinate the edges endpoints are represented with.
                Defaults to ``CoordKind.CARTESIAN``.

        Returns:
            The edges of the Zephyr graph.
        """

        if coord_kind is CoordKind.LINEAR:
            raise NotImplementedError("Zephyr does not support linear coordinates")

        shape = self._find_shape(shape)
        if shape.m is _Infinite.INFINITE:
            raise ValueError(
                "Cannot generate infinite number of nodes!\nProvide a finite grid size."
            )
        if edge_kind is None:
            _edge_kinds = {EdgeKind.INTERNAL, EdgeKind.EXTERNAL, EdgeKind.ODD}
        elif isinstance(edge_kind, EdgeKind):
            _edge_kinds = {edge_kind}
        else:
            _edge_kinds = set(edge_kind)
        edges = set()
        if EdgeKind.INTERNAL in _edge_kinds:
            edges.update(self._internal_edges(shape, coord_kind))
        if EdgeKind.EXTERNAL in _edge_kinds:
            edges.update(self._external_edges(shape, coord_kind))
        if EdgeKind.ODD in _edge_kinds:
            edges.update(self._odd_edges(shape, coord_kind))

        return edges

    def _k_values(self, t: int | _Quotient) -> Iterable[int | _Quotient]:
        """Gives the ``k`` values of a tile with tile size ``t``.

        Args:
            t: The tile size of the Zephyr graph.

        Returns:
            The ``k`` values within a tile.
        """
        return [_Quotient.QUOTIENT] if t is _Quotient.QUOTIENT else range(t)

    def _internal_edges(
        self,
        shape: ZephyrShape,
        coord_kind: CoordKind,
    ) -> Generator[ZephyrEdge, None, None]:
        """Generates the internal edges of a Zephyr graph.

        Args:
            shape: The shape of the Zephyr graph.
            coord_kind: The kind of coordinate the edges endpoints are represented with.

        Yields:
            The internal edges of the Zephyr graph.
        """
        m, t = shape
        k_vals = self._k_values(t)
        for x in range(0, 4 * m, 2):
            for y in range(1, 4 * m, 2):
                square = [(x, y), (x + 1, y - 1), (x + 2, y),
                          (x + 1, y + 1), (x, y)]
                for i, sq_e in enumerate(square):
                    if i == 4:
                        continue
                    for k1, k2 in product(k_vals, k_vals):
                        coord1 = ZephyrCartesianCoord(*sq_e, k=k1)
                        node1 = ZephyrNode(
                            coord1, shape=shape, coord_kind=coord_kind, check_node_valid=False
                        )
                        coord2 = ZephyrCartesianCoord(*square[i + 1], k=k2)
                        node2 = ZephyrNode(
                            coord2, shape=shape, coord_kind=coord_kind, check_node_valid=False
                        )
                        yield ZephyrEdge(x=node1, y=node2, check_edge_valid=False)

    def _external_edges(
        self,
        shape: ZephyrShape,
        coord_kind: CoordKind,
    ) -> Generator[ZephyrEdge, None, None]:
        """Generates the external edges of a Zephyr graph.

        Args:
            shape: The shape of the Zephyr graph.
            coord_kind: The kind of coordinate the edges endpoints are represented with.

        Yields:
            The external edges of the Zephyr graph.
        """
        m, t = shape
        k_vals = self._k_values(t)
        for x in range(1, 4 * m - 4, 2):
            for y in range(0, 4 * m + 1, 2):
                ccoord = (x, y)
                ccoord_ext = (x + 4, y)
                for k in k_vals:
                    for step in (-1, 1):
                        coord1 = ZephyrCartesianCoord(
                            *ccoord[::step], k, check_coord=False)
                        node1 = ZephyrNode(
                            coord1, shape=shape, coord_kind=coord_kind, check_node_valid=False
                        )
                        coord2 = ZephyrCartesianCoord(
                            *ccoord_ext[::step], k, check_coord=False)
                        node2 = ZephyrNode(
                            coord2, shape=shape, coord_kind=coord_kind, check_node_valid=False
                        )
                        yield ZephyrEdge(x=node1, y=node2, check_edge_valid=False)

    def _odd_edges(
        self,
        shape: ZephyrShape,
        coord_kind: CoordKind,
    ) -> Generator[ZephyrEdge, None, None]:
        """Generates the odd edges of a Zephyr graph.

        Args:
            shape: The shape of the Zephyr graph.
            coord_kind: The kind of coordinate the edges endpoints are represented with.

        Yields:
            The odd edges of the Zephyr graph.
        """
        m, t = shape
        k_vals = self._k_values(t)
        for x in range(1, 4 * m - 2, 2):
            for y in range(0, 4 * m + 1, 2):
                ccoord = (x, y)
                ccoord_odd = (x + 2, y)
                for k in k_vals:
                    for step in (-1, 1):
                        coord1 = ZephyrCartesianCoord(
                            *ccoord[::step], k, check_coord=False)
                        node1 = ZephyrNode(
                            coord1, shape=shape, coord_kind=coord_kind, check_node_valid=False
                        )
                        coord2 = ZephyrCartesianCoord(
                            *ccoord_odd[::step], k, check_coord=False)
                        node2 = ZephyrNode(
                            coord2, shape=shape, coord_kind=coord_kind, check_node_valid=False
                        )
                        yield ZephyrEdge(x=node1, y=node2, check_edge_valid=False)
