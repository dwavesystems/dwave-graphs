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

# Developer note: we could implement a function that creates the iter_*_to_* and
# iter_*_to_*_pairs methods just-in-time, but there are a small enough number
# that for now it makes sense to do them by hand.


from __future__ import annotations
from typing import Literal
from collections.abc import Callable, Generator, Iterable, Sequence
import networkx as nx
from dwave.graphs.topologies.common import QUOTIENT, Coord, CoordKind, _Infinite, _Quotient
from dwave.graphs.topologies.zephyr.graphs import zephyr_graph
from dwave.graphs.topologies.zephyr.shape import ZephyrShape

__all__ = ["ZephyrCartesianCoord", "ZephyrCoord", "zephyr_coordinates"]


class zephyr_coordinates:
    """Provides coordinate converters for the Zephyr indexing schemes.

    Args:
        m: Grid parameter for the Zephyr lattice.
        t: Tile parameter for the Zephyr lattice; must be even.

    See also :func:`~dwave.graphs.topologies.zephyr.graphs.zephyr_graph` for
    descriptions the various coordinate conventions.

    """

    def __init__(self, m: int, t: int = 4) -> None:
        self.args = m, 2 * m + 1, t

    def zephyr_to_linear(self, q: tuple[int, int, int, int, int]) -> int:
        """Converts a 5-term Zephyr coordinate into a linear index.

        Args:
            q: 5-term Zephyr coordinate.

        Returns:
            Linear index.

        Example:
            >>> dwave.graphs.zephyr_coordinates(2).zephyr_to_linear((0, 1, 2, 1, 0))
            26
        """
        u, w, k, j, z = q
        m, M, t = self.args
        return (((u * M + w) * t + k) * 2 + j) * m + z

    def linear_to_zephyr(self, r: int) -> tuple[int, int, int, int, int]:
        """Converts a linear index into a 5-term Zephyr coordinate.

        Args:
            r: Linear index.

        Returns:
            5-term Zephyr coordinate.

        Example:
            >>> dwave.graphs.zephyr_coordinates(2).linear_to_zephyr(137)
            (1, 3, 2, 0, 1)

        """
        m, M, t = self.args
        r, z = divmod(r, m)
        r, j = divmod(r, 2)
        r, k = divmod(r, t)
        u, w = divmod(r, M)
        return u, w, k, j, z

    def iter_zephyr_to_linear(
        self, qlist: Sequence[tuple[int, int, int, int, int]]
    ) -> Generator[int]:
        """Converts a sequence of 5-term Zephyr coordinates to linear indices.

        Args:
            qlist: Sequence of 5-term Zephyr coordinates.

        Yields:
            Linear index of each 5-term Zephyr coordinate.
        """
        m, M, t = self.args
        for (u, w, k, j, z) in qlist:
            yield (((u * M + w) * t + k) * 2 + j) * m + z

    def iter_linear_to_zephyr(
        self, rlist: Sequence[int]
    ) -> Generator[tuple[int, int, int, int, int]]:
        """Converts a sequence of linear indices to 5-term Zephyr coordinates.

        Args:
            rlist: Sequence of linear indices.

        Yields:
            5-term Zephyr coordinates of each linear index.
        """
        m, M, t = self.args
        for r in rlist:
            r, z = divmod(r, m)
            r, j = divmod(r, 2)
            r, k = divmod(r, t)
            u, w = divmod(r, M)
            yield u, w, k, j, z

    @staticmethod
    def _pair_repack(f: Callable, plist: Iterable[tuple]) -> Generator[tuple]:
        """Flattens a sequence of pairs to pass through f, and then re-pairs the result."""
        ulist = f(u for p in plist for u in p)
        for u in ulist:
            v = next(ulist)
            yield u, v

    def iter_zephyr_to_linear_pairs(self, plist: Iterable[tuple]) -> Generator[tuple]:
        """Converts pairs of 5-term Zephyr coordinates to pairs of linear indices."""
        return self._pair_repack(self.iter_zephyr_to_linear, plist)

    def iter_linear_to_zephyr_pairs(
        self,
        plist: Iterable[tuple],
    ) -> Generator[tuple]:
        """Converts pairs of linear indices to pairs of 5-term Zephyr coordinates."""
        return self._pair_repack(self.iter_linear_to_zephyr, plist)

    def graph_to_linear(self, g: nx.Graph) -> nx.Graph:
        """Returns a copy of the graph g relabeled to have linear indices.

        Args:
            g: The Zephyr graph to be relabeled.

        Returns:
            A Zephyr graph relabeled with linear indices.
        """
        labels = g.graph.get('labels')
        if labels == 'int':
            return g.copy()
        elif labels == 'coordinate':
            nodes = self.iter_zephyr_to_linear(g)
            edges = self.iter_zephyr_to_linear_pairs(g.edges)
        else:
            raise ValueError(
                f"Node labeling {labels} not recognized. "
                "Input must be generated by dwave.graphs.zephyr_graph."
            )

        return zephyr_graph(
            g.graph['rows'],
            t=g.graph['tile'],
            node_list=nodes,
            edge_list=edges,
            data=g.graph['data'],
        )

    def graph_to_zephyr(self, g: nx.Graph) -> nx.Graph:
        """Returns a copy of the graph g relabeled to have Zephyr coordinates.

        Args:
            g: The Zephyr graph to be relabeled.

        Returns:
            A Zephyr graph relabeled with Zephyr coordinates.
        """
        labels = g.graph.get('labels')
        if labels == 'int':
            nodes = self.iter_linear_to_zephyr(g)
            edges = self.iter_linear_to_zephyr_pairs(g.edges)
        elif labels == 'coordinate':
            return g.copy()
        else:
            raise ValueError(
                f"Node labeling {labels} not recognized. "
                "Input must be generated by dwave.graphs.zephyr_graph."
            )

        return zephyr_graph(
            g.graph['rows'],
            t=g.graph['tile'],
            node_list=nodes,
            edge_list=edges,
            data=g.graph['data'],
            coordinates=True,
        )

    @staticmethod
    def zephyr_to_cartesian(g: tuple[int, int, int | _Quotient, int, int] | ZephyrCoord) -> tuple[int, int, int | _Quotient]:
        """Converts a Zephyr coordinate to Cartesian coordinates.

        Args:
            g: 5-tuple Zephyr coordinate.

        Returns:
            3-tuple Cartesian coordinates.
        """
        u, w, k, j, z = g
        if u == 0:
            x = 2 * w
            y = 4 * z + 2 * j + 1
        else:
            x = 4 * z + 2 * j + 1
            y = 2 * w
        return x, y, k

    @staticmethod
    def cartesian_to_zephyr(c: tuple[int, int, int | _Quotient] | ZephyrCartesianCoord) -> tuple[int, int, int | _Quotient, int, int]:
        """Converts Cartesian coordinates to a Zephyr coordinate.

        Args:
            c: 3-tuple Cartesian coordinates.

        Returns:
            5-tuple Zephyr coordinate.
        """
        x, y, k = c
        if x % 2 == 0:
            u = 0
            w = x // 2
            j = ((y - 1) % 4) // 2
            z = y // 4
        else:
            u = 1
            w = y // 2
            j = ((x - 1) % 4) // 2
            z = x // 4
        return u, w, k, j, z

    def linear_to_cartesian(self, r: int) -> tuple[int, int, int]:
        m, M, t = self.args

        r, z = divmod(r, m)
        r, j = divmod(r, 2)
        r, k = divmod(r, t)
        u, w = divmod(r, M)

        x = 2 * w
        y = 4 * z + 2 * j + 1

        return (x, y, k) if u == 0 else (y, x, k)

    def cartesian_to_linear(self, c: tuple[int, int, int]) -> int:
        x, y, k = c
        if x % 2 == 0:
            u = 0
            w = x // 2
            j = ((y - 1) % 4) // 2
            z = y // 4
        else:
            u = 1
            w = y // 2
            j = ((x - 1) % 4) // 2
            z = x // 4

        m, M, t = self.args
        return (((u * M + w) * t + k) * 2 + j) * m + z


class __zephyr_coordinates_cache_dict(dict):
    """An internal-use cached factory for `zephyr_coordinates` objects."""

    def __missing__(self, key: tuple) -> zephyr_coordinates:
        self[key] = val = zephyr_coordinates(*key)
        return val


_zephyr_coordinates_cache = __zephyr_coordinates_cache_dict()


class ZephyrCartesianCoord(Coord):
    """A class to represent the node of a Zephyr graph
    in its Cartesian coordinate.

    Args:
        x: ``x`` value of the node's Cartesian coordinate.
        y: ``y`` value of the node's Cartesian coordinate.
        k: Index of node within its Zephyr tile.
        check_coord: Whether to check the coordinate is valid.
            Defaults to ``True``.
    """
    _topology_name = "zephyr"

    @classmethod
    def kind(cls) -> CoordKind:
        """Returns the kind of the coordinate associated with the class.

        Returns:
            CoordKind: The kind of class's coordinate.
        """
        return CoordKind.CARTESIAN

    def __init__(
        self,
        x: int,
        y: int,
        k: int | _Quotient,
        check_coord: bool = True,
    ) -> None:
        if check_coord:
            self._args_valid_topology(x, y, k)

        self._x: int = x
        self._y: int = y
        self._k: int | _Quotient = k

    def _args_valid_topology(self, x: int, y: int, k: int | _Quotient) -> None:
        """Verifies the coordinate is a valid Zephyr Cartesian coordinate.

        Args:
            x: x value for the node's Cartesian coordinate.
            y: y value for the node's Cartesian coordinate.
            k: Index of node within its Zephyr tile.

        Raises:
            ValueError: If ``x`` or ``y`` are negative.
            ValueError: If ``x`` and ``y`` have the same parity.
            ValueError: If ``k`` is non-quotient and negative.
        """
        if x < 0 or y < 0:
            raise ValueError(f"Expected x, y to be non-negative, got {x, y}")
        if x % 2 == y % 2:
            raise ValueError(f"Expected x, y to differ in parity, got {x, y}")
        if k is not QUOTIENT and k < 0:
            raise ValueError(f"Expected k to be non-negative, got {k}")

    def is_shape_consistent(self, shape: ZephyrShape) -> bool:
        """Tells whether the coordinate is consistent with a Zephyr shape.

        Args:
            shape: The shape to check the consistency of the coordinate with.

        Returns:
            bool: Whether the coordinate is consistent with the shape.
        """
        # check x, y value of coord is consistent with m
        shape_m, shape_t = shape
        if not isinstance(shape_m, _Infinite):
            if not all(val in range(4 * shape_m + 1) for val in (self._x, self._y)):
                return False

        # check k value of coord is consistent with t
        if isinstance(shape_t, _Quotient):
            return isinstance(self._k, _Quotient)
        elif isinstance(self._k, _Quotient):
            return False
        return self._k in range(shape_t)

    @property
    def x(self) -> int:
        """``x`` value of the coordinate."""
        return self._x

    @property
    def y(self) -> int:
        """``y`` value of the coordinate."""
        return self._y

    @property
    def k(self) -> int | _Quotient:
        """``k`` value of the coordinate."""
        return self._k

    def to_tuple(self) -> tuple[int, int, int | _Quotient]:
        """Returns the tuple cooresponding to the coordinate."""
        return (self._x, self._y, self._k)

    def is_quotient(self) -> bool:
        """Whether the given coordinate is a quotient coordinate."""
        return self.k is QUOTIENT

    def to_quotient(self) -> ZephyrCartesianCoord:
        """Converts the Cartesian coordinate to its corresponding
        Cartesian coordinate in a quotient Zephyr graph."""
        return ZephyrCartesianCoord(x=self._x, y=self._y, k=QUOTIENT, check_coord=False)

    def to_non_quotient(self, shape: ZephyrShape, **kwargs) -> list[ZephyrCartesianCoord]:
        """Expands the coordinate to non-quotient coordinates;
            i.e. it gives all coordinates in a non-quotient Zephyr graph whose
            quotient is the coordinate.

        Args:
            shape: The Zephyr graph's shape to expand the coordinate to.

        Raises:
            ValueError: If ``shape`` is quotient.
            ValueError: If the coordinate is not consistent with the shape.

        Returns:
            list[ZephyrCartesianCoord]: The expansion of the coordinate into non-quotient.
        """

        if shape.is_quotient():
            raise ValueError(f"Expected shape to be non-quotient, got {shape}")

        # Check value of the Cartesian coordinate is consistent with shape
        if not self.is_quotient():
            if not self.is_shape_consistent(shape=shape):
                raise ValueError(f"{self} is not consistent with {shape}")
            return [self]

        x, y = self.x, self.y
        if ZephyrCartesianCoord(x, y, 0, check_coord=False).is_shape_consistent(shape):
            return [ZephyrCartesianCoord(x, y, k, check_coord=False) for k in range(shape.t)]
        else:
            raise ValueError(f"{self} is not consistent with {shape}")

    def convert(self, coord_kind: CoordKind, shape: ZephyrShape | None = None) -> ZephyrCartesianCoord | ZephyrCoord:
        """Converts the coordinate to a given kind of Zephyr coordinates.

        Args:
            coord_kind: The kind of coordinate to covert into.

        Returns:
            ZephyrCartesianCoord | ZephyrCoord: The converted coordinate.
        """
        if coord_kind is CoordKind.TOPOLOGY:
            u, w, k, j, z = zephyr_coordinates.cartesian_to_zephyr(self)
            return ZephyrCoord(u=u, w=w, k=k, j=j, z=z, check_coord=False)

        elif coord_kind is CoordKind.CARTESIAN:
            return self

        elif coord_kind is CoordKind.LINEAR:
            if shape is None:
                raise ValueError(
                    "Must provide shape to convert to linear index")
            if shape.is_quoutient() or shape.is_infinite():
                raise ValueError(
                    "Must provide non-quotient, non-infinite shape to convert to linear index")
            linear_index = _zephyr_coordinates_cache[*shape.to_tuple()].cartesian_to_linear(
                self.to_tuple())
            return linear_index
        else:
            raise ValueError(f"{coord_kind} not a valid coordinate kind")


class ZephyrCoord(Coord):
    """A class to represent the node of a Zephyr graph
        in its Zephyr coordinate.

    Args:
        u: The orientation of qubit
            - u = 0 if vertical,
            - u = 1 if horizontal.
        w: The perpendicular block offset.
        k: The qubit index within tile.
        j: The shift identifier
            - j = 0 if qubit is shifted to the left/top.
            - j = 1 if qubit is shifted to the right/bottom.
        z: The parallel tile offset.
        check_coord: Whether to check the coordinate is valid. Defaults to ``True``.
    """

    @classmethod
    def topology_name(cls) -> Literal["zephyr"]:
        """Returns the name of the topology associated with the class."""
        return "zephyr"

    @classmethod
    def kind(cls) -> CoordKind:
        """Returns the kind of the coordinate associated with the class.

        Returns:
            CoordKind: The kind of class's coordinate.
        """
        return CoordKind.TOPOLOGY

    def __init__(
        self,
        u: int,
        w: int,
        k: int | _Quotient,
        j: int,
        z: int,
        check_coord: bool = True,
    ) -> None:

        if check_coord:
            self._args_valid_topology(u, w, k, j, z)
        self.u = u
        self.w = w
        self.k = k
        self.j = j
        self.z = z

    def _args_valid_topology(self, u: int, w: int, k: int | _Quotient, j: int, z: int) -> None:
        """Verifies the coordinate is a valid Zephyr coordinate.

        Args:
            u: The orientation of qubit
            w: The perpendicular block offset.
            k: The qubit index within tile.
            j: The shift identifier
            z: The parallel tile offset.

        Raises:
            ValueError: If any of ``u`` or ``j`` is not 0 or 1.
            ValueError: If any of ``w`` or ``z`` is negative.
            ValueError: If ``k`` is non-quotient and negative.
        """
        if any(par not in (0, 1) for par in (u, j)):
            raise ValueError(
                f"Expected u, j to be 0 or 1, got {(u, w, k, j, z) = }")
        if any(par < 0 for par in (w, z)):
            raise ValueError(
                f"Expected w, z to be non-negative, got {(u, w, k, j, z) = }")
        if k is not QUOTIENT and k < 0:
            raise ValueError(
                f"Expected k to be QUOTIENT or non-negative, got {k}")

    def is_shape_consistent(self, shape: ZephyrShape) -> bool:
        """Tells whether the coordinate is consistent with a Zephyr shape.

        Args:
            shape: The shape to check the consistency of the coordinate with.

        Returns:
            bool: Whether the coordinate is consistent with the shape.
        """
        # w, z value of coord is consistent with grid size
        shape_m, shape_t = shape
        if not isinstance(shape_m, _Infinite):
            if self.w not in range(2 * shape_m + 1) or self.z not in range(shape_m):
                return False

        # k value of coord is consistent with tile size
        if isinstance(shape_t, _Quotient):
            return isinstance(self.k, _Quotient)
        elif isinstance(self.k, _Quotient):
            return False
        return self.k in range(shape_t)

    def is_quotient(self) -> bool:
        """Whether the given coordinate is a quotient coordinate."""
        return self.k is QUOTIENT

    def to_tuple(self) -> tuple[int, int, int | _Quotient, int, int]:
        """Returns the tuple cooresponding to the coordinate."""
        return (self.u, self.w, self.k, self.j, self.z)

    def to_quotient(self) -> ZephyrCoord:
        """Converts the coordinate to its corresponding
        Zephyr coordinate in a quotient Zephyr graph."""
        return ZephyrCoord(u=self.u, w=self.w, k=QUOTIENT, j=self.j, z=self.z)

    def to_non_quotient(self, shape: ZephyrShape, **kwargs) -> list[ZephyrCoord]:
        """Expands the coordinate to all non-quotient coordinates;
        i.e. it gives all coordinates in a non-quotient Zephyr graph whose
        quotient is the coordinate.

        Args:
            shape: The graph's shape to expand the coordinate to.

        Raises:
            ValueError: If ``shape`` is quotient.
            ValueError: If the coordinate is not consistent with the shape.

        Returns:
            list[ZephyrCoord]: The expansion of the coordinate into non-quotient.
        """
        if shape.is_quotient():
            raise ValueError(f"Expected shape to be non-quotient, got {shape}")
        if not self.is_quotient():
            if not self.is_shape_consistent(shape):
                raise ValueError(f"{self} is not consistent with {shape}.")
            return [self]

        u, w, _, j, z = self
        if ZephyrCoord(u, w, 0, j, z, check_coord=False).is_shape_consistent(shape):
            return [
                ZephyrCoord(u, w, k, j, z, check_coord=False)
                for k in range(shape.t)
            ]
        else:
            raise ValueError(f"{self} is not consistent with {shape}")

    def convert(
        self,
        coord_kind: CoordKind,
        shape: ZephyrShape | None = None
    ) -> ZephyrCartesianCoord | ZephyrCoord:
        """Converts the coordinate to a given kind of Zephyr coordinates.

        Args:
            coord_kind: The kind of coordinate to covert into.

        Returns:
            ZephyrCartesianCoord | ZephyrCoord: The converted coordinate.
        """
        if coord_kind is CoordKind.CARTESIAN:
            x, y, k = zephyr_coordinates.zephyr_to_cartesian(self)
            return ZephyrCartesianCoord(x=x, y=y, k=k, check_coord=False)

        elif coord_kind is CoordKind.TOPOLOGY:
            return self

        elif coord_kind is CoordKind.LINEAR:
            if shape is None:
                raise ValueError(
                    "Must provide shape to convert to linear index")
            if shape.is_quoutient() or shape.is_infinite():
                raise ValueError(
                    "Must provide non-quotient, non-infinite shape to convert to linear index")
            linear_index = _zephyr_coordinates_cache[*shape.to_tuple()].zephyr_to_linear(
                self.to_tuple())
            return linear_index
        else:
            raise ValueError(f"{coord_kind} not a valid coordinate kind")
