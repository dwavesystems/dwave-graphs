# Copyright 2018 D-Wave Systems Inc.
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

import dimod
import networkx as nx
import parameterized

import dwave.graphs


@parameterized.parameterized_class(
    'graph',
    [[nx.Graph()],
     [nx.path_graph(10)],
     [nx.complete_graph(4)],
     [nx.Graph([(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 4), (3, 5)])],
     [nx.Graph([(0, 1), (0, 2), (1, 2), (1, 3), (1, 4), (1, 5)])],
     [nx.Graph([(0, 1), (0, 2), (1, 2), (1, 3), (2, 4), (3, 4)])],
     [nx.Graph({0: [], 1: [6], 2: [5], 3: [4], 4: [3], 2: [5], 6: [1]})]
     # [nx.Graph([(0, 3), (0, 5), (0, 6), (1, 2), (1, 3), (1, 4), (1, 7),
     #            (2, 4), (2, 6), (3, 6), (3, 7), (4, 7), (6, 7)])],  # slow
     ]
    )
class TestMatching(unittest.TestCase):
    def test_maximal_matching(self):
        matching = dwave.graphs.algorithms.maximal_matching(
            self.graph, dimod.ExactSolver())
        self.assertTrue(nx.is_maximal_matching(self.graph, matching))

    def test_min_maximal_matching(self):
        matching = dwave.graphs.algorithms.min_maximal_matching(
            self.graph, dimod.ExactSolver())
        self.assertTrue(nx.is_maximal_matching(self.graph, matching))


def is_valid_matching(matching, edges):
    """A matching is valid iff every pair is a real edge and every vertex
    (on either side) is used at most once."""
    if len(set(matching.values())) != len(matching):
        return False  # some y used twice
    return all(y in edges.get(x, ()) for x, y in matching.items())


class TestMaximumBipartiteMatching(unittest.TestCase):
    def test_empty_graph(self):
        self.assertEqual(
            dwave.graphs.algorithms.maximum_bipartite_matching([], [], {}), {}
        )

    def test_no_edges(self):
        self.assertEqual(
            dwave.graphs.algorithms.maximum_bipartite_matching(
                ["a", "b"], ["c", "d"], {}
            ),
            {},
        )

    def test_perfect_matching_possible(self):
        X = ["a1", "a2", "a3"]
        Y = ["b1", "b2", "b3"]
        edges = {
            "a1": ["b1", "b2"],
            "a2": ["b1"],
            "a3": ["b2", "b3"],
        }
        matching = dwave.graphs.algorithms.maximum_bipartite_matching(X, Y, edges)
        self.assertEqual(len(matching), 3)
        self.assertTrue(is_valid_matching(matching, edges))

    def test_no_matching_possible_isolated_x(self):
        X = ["a1", "a2"]
        Y = ["b1"]
        edges = {"a1": ["b1"]}  # a2 has no edges at all
        matching = dwave.graphs.algorithms.maximum_bipartite_matching(X, Y, edges)
        self.assertEqual(len(matching), 1)
        self.assertTrue(is_valid_matching(matching, edges))

    def test_bottleneck_shared_neighbor(self):
        # Both a1 and a2 only connect to b1 -> max matching size 1.
        X = ["a1", "a2"]
        Y = ["b1", "b2"]
        edges = {"a1": ["b1"], "a2": ["b1"]}
        matching = dwave.graphs.algorithms.maximum_bipartite_matching(X, Y, edges)
        self.assertEqual(len(matching), 1)
        self.assertTrue(is_valid_matching(matching, edges))

    def test_larger_random_like_graph(self):
        X = [f"x{i}" for i in range(6)]
        Y = [f"y{i}" for i in range(6)]
        edges = {
            "x0": ["y0", "y1"],
            "x1": ["y0"],
            "x2": ["y1", "y2"],
            "x3": ["y2", "y3"],
            "x4": ["y3", "y4"],
            "x5": ["y4", "y5"],
        }
        matching = dwave.graphs.algorithms.maximum_bipartite_matching(X, Y, edges)
        self.assertEqual(len(matching), 6)  # perfect matching exists
        self.assertTrue(is_valid_matching(matching, edges))

    def test_result_omits_unmatched_vertices(self):
        X = ["a1", "a2"]
        Y = ["b1"]
        edges = {"a1": ["b1"], "a2": []}
        matching = dwave.graphs.algorithms.maximum_bipartite_matching(X, Y, edges)
        self.assertNotIn("a2", matching)
