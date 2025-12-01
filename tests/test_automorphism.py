# Copyright 2025 D-Wave
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import random

import numpy as np
import networkx as nx
import dwave_networkx as dnx

from dwave.experimental.automorphism import (
    schreier_rep,
    sample_automorphisms,
    vertex_orbits,
    edge_orbits,
    SchreierContext
)


class Automorphisms(unittest.TestCase):
    def test_chimera_one(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a chimera-1 graph"""

        graph = dnx.chimera_graph(1)
        result = schreier_rep(graph)

        self.assertEqual(result.num_automorphisms, 1152)
        self.assertEqual(result.vertex_orbits, [[0, 1, 2, 3, 4, 5, 6, 7]])
        self.assertEqual(
            result.edge_orbits,
            [[(0, 4), (0, 5), (0, 6), (0, 7), (1, 4), (1, 5),(1, 6), (1, 7),
              (2, 4), (2, 5), (2, 6), (2, 7), (3, 4), (3, 5), (3, 6), (3, 7)]]
        )

    def test_zephyr_defect(self):
        """Check the number of automorphisms of a zephyr graph with defects"""

        graph = dnx.zephyr_graph(3)
        defect_fraction = 0.04
        num_delete = int(defect_fraction * graph.number_of_nodes())
        random.seed(42)
        to_remove = random.sample(range(0, graph.number_of_nodes()), num_delete)
        for node in to_remove:
            graph.remove_node(node)

        result = schreier_rep(graph)
        self.assertEqual(result.num_automorphisms, 4458050224128)

    def test_pegasus_one(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a chimera-1 graph"""

        graph = dnx.pegasus_graph(2)
        result = schreier_rep(graph)

        self.assertEqual(result.num_automorphisms, 2097152)
        self.assertEqual(
            result.vertex_orbits,
            [[0, 1, 38, 39], [2, 3, 36, 37], [4, 5, 34, 35], [6, 7, 32, 33],
             [8, 9, 30, 31], [10, 11, 28, 29], [12, 13, 26, 27], [14, 15, 24, 25],
             [16, 17, 22, 23], [18, 19, 20, 21]]
        )
        self.assertEqual(
            result.edge_orbits,
            [[(0, 1), (38, 39)],
            [(0, 22), (0, 23), (1, 22), (1, 23), (16, 38), (16, 39), (17, 38), (17, 39)],
            [(0, 24), (0, 25), (1, 24), (1, 25), (14, 38), (14, 39), (15, 38), (15, 39)],
            [(2, 3), (36, 37)],
            [(2, 34), (2, 35), (3, 34), (3, 35), (4, 36), (4, 37), (5, 36), (5, 37)],
            [(2, 36), (2, 37), (3, 36), (3, 37)],
            [(4, 5), (34, 35)],
            [(4, 30), (4, 31), (5, 30), (5, 31), (8, 34), (8, 35), (9, 34), (9, 35)],
            [(4, 32), (4, 33), (5, 32), (5, 33), (6, 34), (6, 35), (7, 34), (7, 35)],
            [(4, 34), (4, 35), (5, 34), (5, 35)],
            [(6, 7), (32, 33)],
            [(6, 30), (6, 31), (7, 30), (7, 31), (8, 32), (8, 33), (9, 32), (9, 33)],
            [(6, 32), (6, 33), (7, 32), (7, 33)],
            [(6, 24), (6, 25), (7, 24), (7, 25), (14, 32), (14, 33), (15, 32), (15, 33)],
            [(8, 9), (30, 31)],
            [(8, 30), (8, 31), (9, 30), (9, 31)],
            [(8, 24), (8, 25), (9, 24), (9, 25), (14, 30), (14, 31), (15, 30), (15, 31)],
            [(8, 26), (8, 27), (9, 26), (9, 27), (12, 30), (12, 31), (13, 30), (13, 31)],
            [(8, 28), (8, 29), (9, 28), (9, 29), (10, 30), (10, 31), (11, 30), (11, 31)],
            [(10, 11), (28, 29)],
            [(10, 20), (10, 21), (11, 20), (11, 21), (18, 28), (18, 29), (19, 28), (19, 29)],
            [(10, 22), (10, 23), (11, 22), (11, 23), (16, 28), (16, 29), (17, 28), (17, 29)],
            [(10, 24), (10, 25), (11, 24), (11, 25), (14, 28), (14, 29), (15, 28), (15, 29)],
            [(10, 26), (10, 27), (11, 26), (11, 27), (12, 28), (12, 29), (13, 28), (13, 29)],
            [(10, 28), (10, 29), (11, 28), (11, 29)],
            [(12, 13), (26, 27)],
            [(12, 20), (12, 21), (13, 20), (13, 21), (18, 26), (18, 27), (19, 26), (19, 27)],
            [(12, 26), (12, 27), (13, 26), (13, 27)],
            [(14, 15), (24, 25)],
            [(16, 17), (22, 23)],
            [(18, 19), (20, 21)]]
        )

    def test_automorphism_sampling(self):
        """Check the random sampling of automorphisms from the Schreier-Sims representation"""

        graph = nx.cycle_graph(8)

        result = schreier_rep(graph)
        single_automorphism = sample_automorphisms(result.u_vector, seed=42)
        multiple_automorphisms = sample_automorphisms(result.u_vector, num_samples=3, seed=42)

        self.assertEqual(result.num_automorphisms, 16)
        self.assertTrue(np.array_equal(
            single_automorphism,
            [np.array([6, 7, 0, 1, 2, 3, 4, 5])]
        ))
        self.assertTrue(np.array_equal(
            multiple_automorphisms,
            [np.array([6, 7, 0, 1, 2, 3, 4, 5]),
             np.array([3, 4, 5, 6, 7, 0, 1, 2]),
             np.array([6, 7, 0, 1, 2, 3, 4, 5])]
        ))

    def test_kreher(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of the graph from
        Example 7.6 in Kreher, D. L., & Stinson, D. R. (1999). Combinatorial algorithms: 
        Generation, enumeration, and search."""

        nodes_kreher = [0, 1, 2, 3, 4, 5, 6, 7]
        edges_kreher = [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
            (6, 7), (7, 0), (0, 3), (1, 4), (2, 6), (5, 7)]
        graph_kreher = nx.Graph()
        graph_kreher.add_nodes_from(nodes_kreher)
        graph_kreher.add_edges_from(edges_kreher)
        result_kreher = schreier_rep(graph_kreher)
        self.assertEqual(result_kreher.num_automorphisms, 12)
        self.assertEqual(result_kreher.vertex_orbits, [[0, 2, 4], [1, 3], [5, 6, 7]])
        self.assertEqual(result_kreher.edge_orbits,
            [[(0, 1), (0, 3), (1, 2), (1, 4), (2, 3), (3, 4)],
            [(0, 7), (2, 6), (4, 5)],
            [(5, 6), (5, 7), (6, 7)]]
        )

    def test_null_zero(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a
        null (edgeless) graph with zero nodes."""

        graph_null_zero = nx.Graph()
        result_null_zero = schreier_rep(graph_null_zero)
        self.assertEqual(result_null_zero.num_automorphisms, 1)
        self.assertEqual(result_null_zero.vertex_orbits, [])
        self.assertEqual(result_null_zero.edge_orbits, [])

    def test_null_one(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a
        null (edgeless) graph with one node."""

        graph_null_one = nx.Graph()
        graph_null_one.add_nodes_from([0])
        result_null_one = schreier_rep(graph_null_one)
        self.assertEqual(result_null_one.num_automorphisms, 1)
        self.assertEqual(result_null_one.vertex_orbits, [[0]])
        self.assertEqual(result_null_one.edge_orbits, [])

    def test_null_two_noncontiguous(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a
        null (edgeless) graph with two nodes. Also tests that non-contiguous node 
        labels are accepted."""

        graph_null_two = nx.Graph()
        graph_null_two.add_nodes_from([0, 2])
        result_null_two = schreier_rep(graph_null_two)
        self.assertEqual(result_null_two.num_automorphisms, 2)
        self.assertEqual(result_null_two.vertex_orbits, [[0, 1]])
        self.assertEqual(result_null_two.edge_orbits, [])

    def test_path_two(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a
        path graph with two nodes."""

        graph_path_two = nx.Graph()
        graph_path_two.add_nodes_from([0, 1])
        graph_path_two.add_edges_from([(0, 1)])
        result_path_two = schreier_rep(graph_path_two)
        self.assertEqual(result_path_two.num_automorphisms, 2)
        self.assertEqual(result_path_two.vertex_orbits, [[0, 1]])
        self.assertEqual(result_path_two.edge_orbits, [[(0, 1)]])

    def test_cycle_8(self):
        """Check the number of automorphisms and vertex orbits of a cycle graph
        with eight nodes."""

        graph_cycle_8 = nx.cycle_graph(8)
        result_cycle_8 = schreier_rep(graph_cycle_8)
        self.assertEqual(result_cycle_8.num_automorphisms, 16)
        self.assertEqual(result_cycle_8.vertex_orbits, [list(range(8))])

    def test_biclique_6(self):
        """Check the number of automorphisms and vertex orbits of a biclique
        graph with six nodes."""

        nodes_biclique_6 = [0, 1, 2, 3, 4, 5]
        edges_biclique_6 = [(0, 3), (0, 4), (0, 5), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5)]
        graph_biclique_6 = nx.Graph()
        graph_biclique_6.add_nodes_from(nodes_biclique_6)
        graph_biclique_6.add_edges_from(edges_biclique_6)
        result_biclique_6 = schreier_rep(graph_biclique_6)
        self.assertEqual(result_biclique_6.num_automorphisms, 72)
        self.assertEqual(result_biclique_6.vertex_orbits, [list(range(6))])

    def test_regular_6(self):
        """Check the number of automorphisms of a regular graph with six nodes."""

        graph_regular_6 = nx.random_regular_graph(5, 6)
        result_regular_6 = schreier_rep(graph_regular_6)
        self.assertEqual(result_regular_6.num_automorphisms, 720)

    def test_petersen(self):
        """Check the number of automorphisms and vertex orbits of a petersen graph."""

        graph_petersen = nx.petersen_graph()
        result_petersen = schreier_rep(graph_petersen)
        self.assertEqual(result_petersen.num_automorphisms, 120)
        self.assertEqual(result_petersen.vertex_orbits, [list(range(10))])

    def test_orbits_kreher(self):
        """Test the vertex and edge orbit functions directly."""

        u_vector_kreher = [
            [np.array([0, 1, 4, 3, 2, 6, 5, 7])],
            [np.array([2, 1, 4, 3, 0, 7, 5, 6]), np.array([4, 1, 0, 3, 2, 6, 7, 5])],
            [np.array([0, 3, 2, 1, 4, 5, 6, 7])]]
        nodes_kreher = list(range(8))
        edges_kreher = [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
            (6, 7), (7, 0), (0, 3), (1, 4), (2, 6), (5, 7)]
        vertex_orbits_kreher = vertex_orbits(u_vector_kreher, nodes_kreher)
        edge_orbits_kreher = edge_orbits(u_vector_kreher, edges_kreher)
        self.assertEqual(edge_orbits_kreher,
            [[(0, 1), (0, 3), (1, 2), (1, 4), (2, 3), (3, 4)],
            [(0, 7), (2, 6), (4, 5)],
            [(5, 6), (5, 7), (6, 7)]]
        )
        self.assertEqual(vertex_orbits_kreher, [[0, 2, 4], [1, 3], [5, 6, 7]])

    def test_orbits_kreher_numpy(self):
        """Test the vertex and edge orbit functions directly, using 
        a list of lists for ``u_vector`` instead of a list of NumPy arrays,
        and a NumPy array for ``nodes`` instead of a list."""

        u_vector_kreher2 = [
            [[0, 1, 4, 3, 2, 6, 5, 7]],
            [[2, 1, 4, 3, 0, 7, 5, 6], [4, 1, 0, 3, 2, 6, 7, 5]],
            [[0, 3, 2, 1, 4, 5, 6, 7]]]
        nodes_kreher2 = np.arange(8)
        vertex_orbits_kreher2 = vertex_orbits(u_vector_kreher2, nodes_kreher2)
        self.assertEqual(vertex_orbits_kreher2, [[0, 2, 4], [1, 3], [5, 6, 7]])

    def test_schreier_null_zero(self):
        """Test the initialization of SchreierContext on a null (edgeless) graph with zero nodes."""

        graph = nx.Graph()
        ctx = SchreierContext(graph)
        assert ctx._nodes == []
        assert ctx._num_nodes == 0
        assert ctx._graph_edges == []

    def test_schreier_null_two(self):
        """Test the initialization of SchreierContext on a null (edgeless) graph with two nodes."""

        graph = nx.Graph([(0,1)])
        ctx = SchreierContext(graph)
        assert ctx._nodes == [0,1]
        assert ctx._graph_edges == [(0,1)]
        assert ctx._neighbours[0] == {1}
        assert ctx._neighbours[1] == {0}
