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
from itertools import combinations

from parameterized import parameterized

from dwave.graphs.topologies.zephyr import ZephyrPlaneShift


class TestZephyrPlaneShift(unittest.TestCase):
    def setUp(self) -> None:
        self.shifts = [
            (0, 2),
            (-3, -1),
            (-2, 0),
            (1, 1),
            (1, -3),
            (-4, 6),
            (10, 4),
            (0, 0),
        ]

    def test_construction(self) -> None:
        for shift in self.shifts:
            zps = ZephyrPlaneShift(*shift)
            self.assertEqual(shift, (zps.x, zps.y))

    @parameterized.expand(
        [
            (0,),
            (1,),
            (2,),
            (5,),
            (10,),
            (-3,),
        ]
    )
    def test_multiply(self, scale) -> None:
        for shift in self.shifts:
            self.assertEqual(
                ZephyrPlaneShift(shift[0] * scale, shift[1] * scale),
                ZephyrPlaneShift(*shift) * scale,
            )
            self.assertEqual(
                ZephyrPlaneShift(shift[0] * scale, shift[1] * scale),
                scale * ZephyrPlaneShift(*shift),
            )

    def test_add(self) -> None:
        for s0, s1 in combinations(self.shifts, 2):
            self.assertEqual(
                ZephyrPlaneShift(*s0) + ZephyrPlaneShift(*s1),
                ZephyrPlaneShift(s0[0] + s1[0], s0[1] + s1[1]),
            )

    @parameterized.expand(
        [
            (-1, ZephyrPlaneShift(0, -4), ZephyrPlaneShift(0, 4)),
            (3, ZephyrPlaneShift(2, 10), ZephyrPlaneShift(6, 30)),
        ]
    )
    def test_mul(self, c, ps, expected) -> None:
        self.assertEqual(c * ps, expected)

    @parameterized.expand(
        [
            (5, TypeError),
            ("NE", TypeError),
            ((0, 2, None), TypeError),
            ((2, 0.5), ValueError),
            ((4, 1), ValueError),
            ((0, 1), ValueError),
        ]
    )
    def test_invalid_input_gives_error(self, invalid, expected_err) -> None:
        with self.assertRaises(expected_err):
            ZephyrPlaneShift(*invalid)
