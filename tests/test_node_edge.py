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
# ================================================================================================
import unittest

from parameterized import parameterized

from dwave.graphs.topologies.common import EdgeKind, _Quotient
from dwave.graphs.topologies.zephyr import ZephyrCartesianCoord, ZephyrEdge, ZephyrNode, ZephyrShape


class TestEdge(unittest.TestCase):
    def test_canonical_order(self) -> None:
        # x > y forces the (y, x) swap branch in Edge._set_edge.
        hi = ZephyrNode((0, 3))
        lo = ZephyrNode((0, 1))
        e = ZephyrEdge(hi, lo)
        self.assertLess(e[0], e[1])
        self.assertEqual(e[0], lo)
        self.assertEqual(e[1], hi)

    def test_eq(self) -> None:
        e1 = ZephyrEdge(ZephyrNode((0, 1)), ZephyrNode((0, 3)))
        e2 = ZephyrEdge(ZephyrNode((0, 3)), ZephyrNode((0, 1)))
        e3 = ZephyrEdge(ZephyrNode((0, 1)), ZephyrNode((1, 0)))
        self.assertEqual(e1, e2)
        self.assertNotEqual(e1, e3)

    def test_eq_non_edge(self) -> None:
        e = ZephyrEdge(ZephyrNode((0, 1)), ZephyrNode((0, 3)))
        self.assertNotEqual(e, 5)

    def test_str_repr(self) -> None:
        e = ZephyrEdge(ZephyrNode((0, 1)), ZephyrNode((0, 3)))
        self.assertIsInstance(str(e), str)
        self.assertIn("ZephyrEdge", repr(e))


class TestZephyrNodeQuotient(unittest.TestCase):
    @parameterized.expand(
        [
            (ZephyrNode((0, 1)), True),
            (ZephyrNode((0, 1, 2), ZephyrShape(t=4)), False),
        ]
    )
    def test_is_quotient(self, zn, expected) -> None:
        self.assertEqual(zn.is_quotient(), expected)

    def test_to_quotient(self) -> None:
        zn = ZephyrNode((0, 1, 2), ZephyrShape(t=4))
        self.assertEqual(zn.to_quotient(), ZephyrNode((0, 1)))

    @parameterized.expand(
        [
            ((5, 2, 1), (6, 10), 1),
            ((5, 2), (6, 2), 2),
            ((1, 2), (1, 10), 10),
        ]
    )
    def test_to_non_quotient(self, coord, shape, expected_len) -> None:
        zn = ZephyrNode(coord, ZephyrShape(*shape) if len(coord) == 3 else None)
        self.assertEqual(len(zn.to_non_quotient(ZephyrShape(*shape))), expected_len)


class TestZephyrNodeCoord(unittest.TestCase):
    def test_coord_cartesian(self) -> None:
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        self.assertEqual(zn.coord, ZephyrCartesianCoord(5, 2, _Quotient.QUOTIENT))

    def test_coord_topology(self) -> None:
        from dwave.graphs.topologies.common import CoordKind

        zn = ZephyrNode((11, 12, 4), ZephyrShape(t=6), coord_kind=CoordKind.TOPOLOGY)
        self.assertEqual(zn.coord, zn.zcoord)

    def test_str_repr(self) -> None:
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        self.assertIsInstance(str(zn), str)
        self.assertIn("ZephyrNode", repr(zn))


class TestZephyrNodeOrdering(unittest.TestCase):
    def test_lt_different_shapes_raises(self) -> None:
        zn0 = ZephyrNode((5, 2), ZephyrShape(6))
        zn1 = ZephyrNode((5, 2), ZephyrShape(4))
        with self.assertRaises(TypeError):
            zn0 < zn1

    def test_eq_non_node(self) -> None:
        self.assertNotEqual(ZephyrNode((5, 2), ZephyrShape(6)), 5)

    def test_lt_non_node_raises(self) -> None:
        with self.assertRaises(TypeError):
            ZephyrNode((5, 2), ZephyrShape(6)) < 5


class TestZephyrNodeNeighborHelpers(unittest.TestCase):
    def test_is_neighbor_where(self) -> None:
        zn = ZephyrNode((0, 1))
        other = ZephyrNode((0, 3))
        self.assertTrue(zn.is_neighbor(other, where=lambda c: c.y == 3))
        self.assertFalse(zn.is_neighbor(other, where=lambda c: c.y == 99))

    def test_incident_edges(self) -> None:
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        edges = set(zn.incident_edges())
        self.assertEqual(len(edges), zn.degree())
        self.assertTrue(all(isinstance(e, ZephyrEdge) for e in edges))

    def test_incident_edges_filtered(self) -> None:
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        edges = set(zn.incident_edges(nbr_kind=EdgeKind.ODD))
        self.assertEqual(len(edges), zn.degree(nbr_kind=EdgeKind.ODD))

    @parameterized.expand(
        [
            ("is_internal_neighbor", (1, 0), True),
            ("is_internal_neighbor", (0, 5), False),
            ("is_external_neighbor", (0, 5), True),
            ("is_external_neighbor", (1, 0), False),
            ("is_odd_neighbor", (0, 3), True),
            ("is_odd_neighbor", (1, 0), False),
        ]
    )
    def test_is_kind_neighbor(self, method, other_xy, expected) -> None:
        zn = ZephyrNode((0, 1))
        other = ZephyrNode(other_xy)
        self.assertEqual(getattr(zn, method)(other), expected)
