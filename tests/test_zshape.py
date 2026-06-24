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
#
# ================================================================================================


from unittest import TestCase

from parameterized import parameterized
from dwave.graphs.topologies.common import (QUOTIENT, INFINITE)
from dwave.graphs.topologies.zephyr import ZephyrShape


class TestZephyrShape(TestCase):
    @parameterized.expand(
        [((-1, 2), ), ((0, 3), ), ((3, -1),), ((QUOTIENT, 3),), ((3, INFINITE),), ((3, 0), )])
    def test_invalid_raises_error(self, bad_input):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrShape(*bad_input)

    @parameterized.expand(
        [
            ((4, 6), ), ((1, 1), ), ((1, 10), ),  ((), ),
            ((INFINITE, QUOTIENT),), ((INFINITE, 1), ), ((3, QUOTIENT), )
        ]
    )
    def test_valid_runs(self, good_shape):
        ZephyrShape(*good_shape)

    @parameterized.expand(
        [
            ((2, QUOTIENT), True), ((INFINITE, QUOTIENT), True),
            ((INFINITE, 1), False), ((4, 6), False), ((1, 1), False),
        ]
    )
    def test_is_quotient(self, shape, expected):
        self.assertEqual(ZephyrShape(*shape).is_quotient(), expected)

    @parameterized.expand(
        [
            ((2, 3), (2, QUOTIENT)), ((1, QUOTIENT), (1, QUOTIENT)
                                      ), ((INFINITE, 3), (INFINITE, QUOTIENT))
        ]
    )
    def test_to_quotient(self, shape, shape_quo):
        self.assertEqual(ZephyrShape(*shape).to_quotient(),
                         ZephyrShape(*shape_quo))

    @parameterized.expand(
        [
            ((2, 3), (INFINITE, 3)), ((1, QUOTIENT),
                                      (INFINITE, QUOTIENT)), ((INFINITE, 4), (INFINITE, 4))
        ]
    )
    def test_to_infinite(self, shape, shape_inf):
        self.assertEqual(ZephyrShape(*shape).to_infinite(),
                         ZephyrShape(*shape_inf))

    @parameterized.expand(
        [
            ((INFINITE, 2), True), ((INFINITE, QUOTIENT), True),
            ((1, QUOTIENT), False), ((4, 6), False), ((1, 1), False),
        ]
    )
    def test_is_infinite(self, shape, expected):
        self.assertEqual(ZephyrShape(*shape).is_infinite(), expected)
