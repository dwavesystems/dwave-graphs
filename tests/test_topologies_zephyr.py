# Copyright 2021 D-Wave Systems Inc.
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


import unittest

from parameterized import parameterized

from dwave.graphs.topologies.common import CoordKind, EdgeKind, INFINITE, QUOTIENT
from dwave.graphs.topologies.zephyr import (Zephyr, ZephyrCartesianCoord, ZephyrCoord,
                                            ZephyrShape)


class TestZephyr(unittest.TestCase):
    def test_basic(self):
        Zephyr()

    @parameterized.expand([(CoordKind.TOPOLOGY,), (CoordKind.CARTESIAN,)])
    def test_valid_coord_kind_is_exposed(self, coord_kind):
        self.assertIs(Zephyr(coord_kind=coord_kind).coord_kind, coord_kind)

    def test_default_coord_kind_is_topology(self):
        self.assertIs(Zephyr().coord_kind, CoordKind.TOPOLOGY)

    def test_invalid_coord_kind_raises(self):
        with self.assertRaises(ValueError):
            Zephyr(coord_kind="not a coord kind")

    def test_linear_coord_kind_raises(self):
        with self.assertRaises(NotImplementedError):
            Zephyr(coord_kind=CoordKind.LINEAR)

    @parameterized.expand(
        [
            (CoordKind.TOPOLOGY, ZephyrCoord),
            (CoordKind.CARTESIAN, ZephyrCartesianCoord),
        ]
    )
    def test_coord_kind_is_used_by_nodes_and_edges(self, coord_kind, expected_class):
        zeph = Zephyr(coord_kind=coord_kind)
        node = next(iter(zeph.nodes(shape=(1, 1))))
        self.assertIsInstance(node.coord, expected_class)
        self.assertIs(node.coord_kind, coord_kind)

        edge = next(iter(zeph.edges(shape=(1, 1))))
        for endpoint in edge:
            self.assertIsInstance(endpoint.coord, expected_class)

    @parameterized.expand(
        [
            (CoordKind.TOPOLOGY, CoordKind.CARTESIAN, ZephyrCartesianCoord),
            (CoordKind.CARTESIAN, CoordKind.TOPOLOGY, ZephyrCoord),
        ]
    )
    def test_explicit_coord_kind_overrides_constructor(self, ctor_kind, call_kind, expected_class):
        zeph = Zephyr(coord_kind=ctor_kind)
        node = next(iter(zeph.nodes(shape=(1, 1), coord_kind=call_kind)))
        self.assertIsInstance(node.coord, expected_class)

        edge = next(iter(zeph.edges(shape=(1, 1), coord_kind=call_kind)))
        for endpoint in edge:
            self.assertIsInstance(endpoint.coord, expected_class)

    def test_accepts_zephyr_shape_instance(self):
        # Passing a ZephyrShape instance skips the tuple-conversion branch and
        # must produce the same result as the equivalent tuple.
        zeph = Zephyr()
        self.assertEqual(zeph.nodes(shape=ZephyrShape(4, 2)), zeph.nodes(shape=(4, 2)))

    @parameterized.expand(
        [
            ((0, 3),),  # m must be a positive int
            ((3, 0),),  # t must be a positive int
            (5,),  # not unpackable -> TypeError caught, re-raised as ValueError
        ]
    )
    def test_invalid_shape_raises(self, bad_shape):
        with self.assertRaises(ValueError):
            Zephyr().nodes(shape=bad_shape)

    @parameterized.expand([((4, 2),), ((6, 1),), ((12, 4),)])
    def test_num_nodes(self, shape):
        zeph = Zephyr()
        self.assertEqual(len(zeph.nodes(shape=shape)),
                         len(Zephyr.create_graph(shape=shape).nodes()))

    @parameterized.expand([((4, 2),), ((6, 1),), ((12, 3),)])
    def test_num_edges(self, shape):
        zeph = Zephyr()
        self.assertEqual(len(zeph.edges(shape=shape)),
                         len(Zephyr.create_graph(shape=shape).edges()))

    def test_nodes_infinite_grid_raises(self):
        with self.assertRaises(ValueError):
            Zephyr().nodes(shape=(INFINITE, 2))

    def test_edges_infinite_grid_raises(self):
        with self.assertRaises(ValueError):
            Zephyr().edges(shape=(INFINITE, 2))

    def test_nodes_quotient_tile(self):
        # Quotient tile size collapses the k-index to a single sentinel value,
        # so the node count must match the t=1 graph.
        zeph = Zephyr()
        quotient = zeph.nodes(shape=(4, QUOTIENT))
        self.assertEqual(len(quotient), len(zeph.nodes(shape=(4, 1))))
        self.assertEqual(len(quotient), 4 * 4 * (2 * 4 + 1))

    def test_edges_quotient_tile(self):
        zeph = Zephyr()
        quotient = zeph.edges(shape=(4, QUOTIENT))
        self.assertEqual(len(quotient), len(zeph.edges(shape=(4, 1))))

    def test_single_edge_kind_partitions_all_edges(self):
        # Covers the ``isinstance(edge_kind, EdgeKind)`` branch and the
        # False sides of the per-kind ``if ... in _edge_kinds`` checks.
        zeph = Zephyr()
        shape = (4, 2)
        all_edges = zeph.edges(shape=shape)
        internal = zeph.edges(shape=shape, edge_kind=EdgeKind.INTERNAL)
        external = zeph.edges(shape=shape, edge_kind=EdgeKind.EXTERNAL)
        odd = zeph.edges(shape=shape, edge_kind=EdgeKind.ODD)

        self.assertEqual(all_edges, internal | external | odd)
        self.assertEqual(len(all_edges), len(internal) + len(external) + len(odd))

    def test_iterable_edge_kind(self):
        # Covers the ``else: _edge_kinds = set(edge_kind)`` branch.
        zeph = Zephyr()
        shape = (4, 2)
        external = zeph.edges(shape=shape, edge_kind=EdgeKind.EXTERNAL)
        odd = zeph.edges(shape=shape, edge_kind=EdgeKind.ODD)
        combined = zeph.edges(shape=shape, edge_kind=[EdgeKind.EXTERNAL, EdgeKind.ODD])
        self.assertEqual(combined, external | odd)

    def test_where_none_matches_unfiltered(self) -> None:
        zeph, shape = Zephyr(coord_kind=CoordKind.CARTESIAN), (2, 1)
        self.assertEqual(zeph.edges(shape=shape, where=None), zeph.edges(shape=shape))

    def test_where_accept_all_gives_everything(self) -> None:
        zeph, shape = Zephyr(coord_kind=CoordKind.CARTESIAN), (2, 1)
        self.assertEqual(zeph.edges(shape=shape, where=lambda c: True), zeph.edges(shape=shape))

    def test_where_reject_all_gives_empty(self) -> None:
        zeph, shape = Zephyr(coord_kind=CoordKind.CARTESIAN), (2, 1)
        self.assertEqual(zeph.edges(shape=shape, where=lambda c: False), set())

    def test_where_restricts_both_endpoints(self) -> None:
        zeph, shape = Zephyr(coord_kind=CoordKind.CARTESIAN), (2, 1)
        filtered = zeph.edges(shape=shape, where=lambda c: c.x <= 2)
        self.assertTrue(filtered)
        self.assertTrue(all(e.coord.x <= 2 for edge in filtered for e in edge))
        self.assertLess(len(filtered), len(zeph.edges(shape=shape)))
        self.assertLessEqual(filtered, zeph.edges(shape=shape))

    def test_where_combines_with_edge_kind(self) -> None:
        zeph, shape = Zephyr(coord_kind=CoordKind.CARTESIAN), (2, 1)
        filtered = zeph.edges(shape=shape, edge_kind=EdgeKind.ODD, where=lambda c: c.x <= 2)
        self.assertLessEqual(filtered, zeph.edges(shape=shape, edge_kind=EdgeKind.ODD))
        self.assertTrue(all(e.coord.x <= 2 for edge in filtered for e in edge))
