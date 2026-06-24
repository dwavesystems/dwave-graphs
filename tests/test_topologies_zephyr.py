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
from dwave.graphs.topologies.zephyr import Zephyr


class TestZephyrTopology(unittest.TestCase):
    def test_basic(self):
        Zephyr()

    @parameterized.expand(
        [((4, 2), ), ((6, 1), ), ((12, 4), )]
    )
    def test_num_nodes(self, shape):
        zeph = Zephyr()

        self.assertEqual(len(zeph.nodes(shape=shape)), len(
            Zephyr.create_graph(shape=shape).nodes()))

    @parameterized.expand(
        [((4, 2), ), ((6, 1), ), ((12, 3), )]
    )
    def test_num_edges(self, shape):
        zeph = Zephyr()
        self.assertEqual(len(zeph.edges(shape=shape)), len(
            Zephyr.create_graph(shape=shape).edges()))
