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

from dwave.graphs.topologies.common import CoordKind, EdgeKind, _Infinite, _Quotient
from dwave.graphs.topologies.zephyr import Zephyr, ZephyrCartesianCoord, ZephyrCoord, ZephyrShape


class TestZephyrTopology(unittest.TestCase):
    def test_basic(self):
        Zephyr()

    @parameterized.expand([((4, 2),), ((6, 1),), ((12, 4),)])
    def test_num_nodes(self, shape):
        zeph = Zephyr()

        self.assertEqual(
            len(zeph.nodes(shape=shape)), len(Zephyr.create_graph(shape=shape).nodes())
        )

    @parameterized.expand([((4, 2),), ((6, 1),), ((12, 3),)])
    def test_num_edges(self, shape):
        zeph = Zephyr()
        self.assertEqual(
            len(zeph.edges(shape=shape)), len(Zephyr.create_graph(shape=shape).edges())
        )


class TestZephyrConstruction(unittest.TestCase):

    @parameterized.expand(
        [
            (CoordKind.TOPOLOGY, ZephyrCoord),
            (CoordKind.CARTESIAN, ZephyrCartesianCoord),
        ]
    )
    def test_valid_coord_kind_sets_coord_class(self, coord_kind, expected_class):
        zeph = Zephyr(coord_kind=coord_kind)
        self.assertIs(zeph._coord_class, expected_class)

    def test_invalid_coord_kind_raises(self):
        # Anything that is not a CoordKind member falls through to ``case _``.
        with self.assertRaises(ValueError):
            Zephyr(coord_kind="not a coord kind")


class TestZephyrFindShape(unittest.TestCase):
    """Covers both branches of ``Zephyr._find_shape`` (via ``nodes``)."""

    def test_accepts_zephyr_shape_instance(self):
        # Passing a ZephyrShape instance skips the tuple-conversion branch and
        # must produce the same result as the equivalent tuple.
        zeph = Zephyr()
        from_instance = zeph.nodes(shape=ZephyrShape(4, 2))
        from_tuple = zeph.nodes(shape=(4, 2))
        self.assertEqual(from_instance, from_tuple)

    @parameterized.expand(
        [
            ((0, 3),),  # m must be a positive int
            ((3, 0),),  # t must be a positive int
            (5,),  # not unpackable -> TypeError caught, re-raised as ValueError
        ]
    )
    def test_invalid_shape_raises(self, bad_shape):
        zeph = Zephyr()
        with self.assertRaises(ValueError):
            zeph.nodes(shape=bad_shape)


class TestZephyrNodes(unittest.TestCase):
    def test_infinite_grid_raises(self):
        zeph = Zephyr()
        with self.assertRaises(ValueError):
            zeph.nodes(shape=(_Infinite.INFINITE, 2))

    def test_quotient_tile(self):
        # Quotient tile size collapses the k-index to a single sentinel value,
        # so the node count must match the t=1 graph.
        zeph = Zephyr()
        quotient = zeph.nodes(shape=(4, _Quotient.QUOTIENT))
        single = zeph.nodes(shape=(4, 1))
        self.assertEqual(len(quotient), len(single))
        self.assertEqual(len(quotient), 4 * 4 * (2 * 4 + 1))


class TestZephyrEdges(unittest.TestCase):
    def test_infinite_grid_raises(self):
        zeph = Zephyr()
        with self.assertRaises(ValueError):
            zeph.edges(shape=(_Infinite.INFINITE, 2))

    def test_quotient_tile(self):
        zeph = Zephyr()
        quotient = zeph.edges(shape=(4, _Quotient.QUOTIENT))
        single = zeph.edges(shape=(4, 1))
        self.assertEqual(len(quotient), len(single))

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
