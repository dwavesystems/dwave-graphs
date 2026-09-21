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


import unittest

from parameterized import parameterized

from dwave.graphs.topologies.common.node_edge import Edge


class TestEdge(unittest.TestCase):
    @parameterized.expand(
        [
            ((3, 1), (1, 3)),
            ((1, 3), (1, 3)),
            ((1, 1), (1, 1)),
            (("b", "a"), ("a", "b")),
            (((0, 3), (0, 1)), ((0, 1), (0, 3))),
        ]
    )
    def test_canonical_order(self, endpoints, expected) -> None:
        edge = Edge(*endpoints)
        self.assertEqual((edge[0], edge[1]), expected)

    def test_eq_is_order_insensitive(self) -> None:
        self.assertEqual(Edge(1, 3), Edge(3, 1))
        self.assertNotEqual(Edge(1, 3), Edge(1, 4))

    def test_eq_non_edge(self) -> None:
        self.assertNotEqual(Edge(1, 3), 5)
        self.assertNotEqual(Edge(1, 3), (1, 3))

    def test_hash_is_order_insensitive(self) -> None:
        self.assertEqual(hash(Edge(1, 3)), hash(Edge(3, 1)))
        self.assertEqual(len({Edge(1, 3), Edge(3, 1)}), 1)

    def test_str_repr(self) -> None:
        edge = Edge(3, 1)
        self.assertEqual(str(edge), "(1, 3)")
        self.assertEqual(repr(edge), "Edge(1, 3)")

    def test_incomparable_endpoints_raise(self) -> None:
        with self.assertRaises(TypeError):
            Edge(1, "a")
