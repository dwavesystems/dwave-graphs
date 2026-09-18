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
from typing import Callable, Iterable

import networkx as nx

from dwave.graphs.topologies.common import (
    CoordKind,
    EdgeKind,
    Topology,
    Infinite,
    Quotient,
    INFINITE,
    QUOTIENT,
)
from dwave.graphs.topologies.zephyr.coords import ZephyrCartesianCoord, ZephyrCoord
from dwave.graphs.topologies.zephyr.graphs import zephyr_graph
from dwave.graphs.topologies.zephyr.node_edge import ZephyrEdge, ZephyrNode, _neighbor_ccoords
from dwave.graphs.topologies.zephyr.shape import ZephyrShape

__all__ = ["Zephyr"]


class Zephyr(Topology):
    """A class to access various classes associated with D-Wave's Zephyr topology.

    Args:
        coord_kind: The kind of coordinate nodes and edge endpoints are
            represented with whenever :meth:`nodes` and :meth:`edges` are
            called without an explicit ``coord_kind``.
            Defaults to ``CoordKind.TOPOLOGY``.

    Raises:
        NotImplementedError: If ``coord_kind`` is :attr:`CoordKind.LINEAR`.
        ValueError: If ``coord_kind`` is not a valid coordinate kind.
    """

    def __init__(self, coord_kind: CoordKind = CoordKind.TOPOLOGY):

        match coord_kind:
            case CoordKind.TOPOLOGY | CoordKind.CARTESIAN:
                self._coord_kind = coord_kind
            case CoordKind.LINEAR:
                raise NotImplementedError("Zephyr does not support linear coordinates")
            case _:
                raise ValueError("invalid coord kind")

        super().__init__()

    @property
    def coord_kind(self) -> CoordKind:
        """The default kind of coordinate nodes and edge endpoints are represented with."""
        return self._coord_kind

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
        return zephyr_graph(
            *shape,
            create_using,
            node_list,
            edge_list,
            data,
            coordinates,
            check_node_list,
            check_edge_list,
        )

    def _find_shape(
        self, shape: ZephyrShape | tuple[int | Infinite, int | Quotient]
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
                raise ValueError(f"{shape} cannot be an instance of ZephyrShape")
        return shape

    def nodes(
        self,
        shape: ZephyrShape | tuple[int | Infinite, int | Quotient],
        coord_kind: CoordKind | None = None,
    ) -> set[ZephyrNode]:
        """Returns the nodes of a Zephyr graph.

        Args:
            shape: The shape of the Zephyr graph.
            coord_kind: The kind of coordinate the nodes are represented with.
                If ``None``, the kind the topology was constructed with is
                used. Defaults to ``None``.

        Raises:
            NotImplementedError: If ``coord_kind`` is :attr:`CoordKind.LINEAR`.
            ValueError: If ``shape`` is not a valid Zephyr shape.
            ValueError: If the grid size of the shape is ``INFINITE``.

        Returns:
            The nodes of the Zephyr graph.
        """
        if coord_kind is None:
            coord_kind = self._coord_kind

        if coord_kind is CoordKind.LINEAR:
            raise NotImplementedError("Zephyr does not support linear coordinates")

        shape = self._find_shape(shape)
        if shape.m is INFINITE:
            raise ValueError(
                "Cannot generate infinite number of nodes!\nProvide a finite grid size."
            )
        m, t = shape
        nodes = set()
        range_x = range(4 * m + 1)
        range_t = [QUOTIENT] if t is QUOTIENT else range(t)
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
        shape: ZephyrShape | tuple[int | Infinite, int | Quotient],
        edge_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        where: Callable[[ZephyrCartesianCoord | ZephyrCoord], bool] | None = None,
        coord_kind: CoordKind | None = None,
    ) -> set[ZephyrEdge]:
        """Returns the edges of a Zephyr graph with a shape and optional
            coordinate and edge kind.

        Args:
            shape: The shape of Zephyr graph.
            edge_kind: Edge kind filter. Restricts edges to the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            where: A coordinate filter. Restricts edges to those whose both
                endpoint coordinates satisfy it. If ``None``, no filtering is
                applied. Defaults to ``None``.
            coord_kind: The kind of coordinate the edges endpoints are represented with.
                If ``None``, the kind the topology was constructed with is
                used. Defaults to ``None``.

        Raises:
            NotImplementedError: If ``coord_kind`` is :attr:`CoordKind.LINEAR`.
            ValueError: If ``shape`` is not a valid Zephyr shape.
            ValueError: If the grid size of the shape is ``INFINITE``.

        Returns:
            The edges of the Zephyr graph.
        """
        if coord_kind is None:
            coord_kind = self._coord_kind

        if coord_kind is CoordKind.LINEAR:
            raise NotImplementedError("Zephyr does not support linear coordinates")

        shape = self._find_shape(shape)
        if shape.m is INFINITE:
            raise ValueError(
                "Cannot generate infinite number of nodes!\nProvide a finite grid size."
            )
        if edge_kind is None:
            _edge_kinds = {EdgeKind.INTERNAL, EdgeKind.EXTERNAL, EdgeKind.ODD}
        elif isinstance(edge_kind, EdgeKind):
            _edge_kinds = {edge_kind}
        else:
            _edge_kinds = set(edge_kind)
        kinds = [
            kind
            for kind in (EdgeKind.INTERNAL, EdgeKind.EXTERNAL, EdgeKind.ODD)
            if kind in _edge_kinds
        ]
        # Each edge is reached from both of its endpoints; the set dedupes them.
        edges = set()
        for node in self.nodes(shape, coord_kind):
            for kind in kinds:
                for ccoord in _neighbor_ccoords(node.ccoord, shape, kind):
                    neighbor = ZephyrNode(
                        ccoord, shape=shape, coord_kind=coord_kind, check_node_valid=False
                    )
                    edges.add(ZephyrEdge(node, neighbor, check_edge_valid=False, edge_kind=kind))

        if where is not None:
            edges = {edge for edge in edges if all(where(node.coord) for node in edge)}

        return edges
