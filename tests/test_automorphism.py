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

from dwave.experimental.automorphism import schreier_rep, sample_automorphisms


class ChimeraAutomorphisms(unittest.TestCase):
    def test_chimera_one(self):
        """Check the number of automorphisms, vertex orbits, and edge orbits of a chimera-1 graph"""
        
        graph = dnx.chimera_graph(1)
        result = schreier_rep(graph)

        self.assertEqual(result.num_automorphisms, 1152)
        self.assertEqual(result.vertex_orbits, [[0, 1, 2, 3, 4, 5, 6, 7]])
        self.assertEqual(
            result.edge_orbits,
            [[(0, 4), (0, 5), (0, 6), (0, 7), (1, 4), (1, 5),(1, 6), (1, 7),
              (2, 4), (2, 5), (2, 6), (2, 7), (3, 4), (3, 5), (3, 6), (3, 7)]])

    def test_zephyr_defect(self):
        """Check the number of automorphisms of a zephyr graph with defects"""
        
        graph = dnx.zephyr_graph(3)
        defect_fraction = 0.04
        num_delete = int(defect_fraction * graph.number_of_nodes())
        random.seed(42)
        to_remove = random.sample(range(0, graph.number_of_nodes()), num_delete)

        for node in to_remove:
            graph.remove_node(node)

        # Relabel nodes to be continuous
        label_mapping = {list(graph.nodes)[j]:j for j in range(graph.number_of_nodes())}
        graph = nx.relabel_nodes(graph, label_mapping) 

        result = schreier_rep(graph)

        self.assertEqual(result.num_automorphisms, 4458050224128)

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
