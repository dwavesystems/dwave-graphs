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
from typing import Callable, Iterable

from dwave.graphs.topologies.common.coords import Coord, CoordKind
from dwave.graphs.topologies.common.node_edge import EdgeKind, TopologyEdge, TopologyNode
from dwave.graphs.topologies.common.shape import TopologyShape

__all__ = ["Topology"]


class Topology(ABC):
    """A class to access various classes associated with a topology."""

    @abstractmethod
    def nodes(
        self,
        shape: TopologyShape,
        coord_kind: CoordKind | None = None,
    ) -> set[TopologyNode]:
        """Returns the nodes of the topology graph with a shape.

        Args:
            shape: The shape of topology graph.
            coord_kind: The kind of coordinate the nodes are represented with.
                Defaults to ``None``.

        Returns:
            set[TopologyNode]: The nodes of the topology graph with the given
            shape and coordinate kind.
        """

    @abstractmethod
    def edges(
        self,
        shape: TopologyShape,
        edge_kind: EdgeKind | Iterable[EdgeKind] | None = None,
        where: Callable[[Coord], bool] | None = None,
        coord_kind: CoordKind | None = None,
    ) -> set[TopologyEdge]:
        """Returns the edges of the topology graph with a shape and optional
            coordinate and edge kind.

        Args:
            shape: The shape of topology graph.
            edge_kind: Edge kind filter. Restricts edges to the given edge kind(s).
                If ``None``, no filtering is applied. Defaults to ``None``.
            where: A coordinate filter. Defaults to ``None``.
            coord_kind: The kind of coordinate the edges endpoints are represented with.
                Defaults to ``None``.

        Returns:
            set[TopologyEdge]: The edges of the topology graph with the given
                shape, coordinate and edge kind.
        """
