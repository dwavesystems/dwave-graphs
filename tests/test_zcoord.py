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
from dwave.graphs.topologies.common import (QUOTIENT, INFINITE, CoordKind,)
from dwave.graphs.topologies.zephyr import (ZephyrShape, ZephyrCartesianCoord,
                                            ZephyrCoord, )


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


class TestZephyrCartesianCoord(TestCase):
    @parameterized.expand(
        [
            ((-1, 2, 2),),
            ((6, -1, 2),),
            ((1, 3, -2),),
            ((1, 1, 1),),
            ((2, 4, 1),),
            ((0, 0, 0),),
            ((-1, 2, 2),),
            ((-1, 2, QUOTIENT),),
        ]
    )
    def test_invalid_input_raises_error(self, xyk):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCartesianCoord(*xyk)

    @parameterized.expand(
        [
            ((0, 17, 4),),
            ((1, 0, QUOTIENT),),
            ((1, 2, 10),),
        ]
    )
    def test_valid_input_runs(self, xyk):
        ZephyrCartesianCoord(*xyk)

    @parameterized.expand([
        ((17, 0, 0), (4, 1), False),
        ((0, 17, 0), (4, QUOTIENT), False),
        ((0, 3, 3), (1, ), False),
        ((5, 2, 1), (6, QUOTIENT), False),
        ((5, 2, 1), (6, 1), False),
        ((5, 2, 1), (6, 2), True),
        ((16, 1, QUOTIENT), (4, ), True),
        ((1, 12, 1), (3, 2), True),
        ((3, 0, QUOTIENT), (4, ), True),
        ((6, 3, 10), (2, 12), True),
    ])
    def test_is_shape_consistent(self, xyk, shape, expected):
        self.assertEqual(ZephyrCartesianCoord(
            *xyk).is_shape_consistent(ZephyrShape(*shape)), expected)

    @parameterized.expand(
        [
            ((5, 2, 1), (6, 1),),
            ((5, 2, 1), (6, QUOTIENT),)
        ]
    )
    def test_to_non_quotient_raises_error(self, xyk, shape):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCartesianCoord(*xyk).to_non_quotient(ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((5, 2, 1), (6, 10), 1),
            ((5, 2, QUOTIENT), (6, 2), 2),
            ((1, 2, QUOTIENT), (1, 10), 10)
        ]
    )
    def test_to_non_quotient(self, xyk, shape, expected_len):
        self.assertEqual(
            len(ZephyrCartesianCoord(*xyk).to_non_quotient(ZephyrShape(*shape))),
            expected_len
        )

    @parameterized.expand([((0, 1, QUOTIENT), ), ((12, 3, QUOTIENT), )])
    def test_cartesian_to_zephyr_runs(self, xyk):
        ccoord = ZephyrCartesianCoord(*xyk)
        self.assertIs(ccoord.convert(
            CoordKind.TOPOLOGY).kind(), CoordKind.TOPOLOGY)
        self.assertIs(ccoord.convert(CoordKind.CARTESIAN).kind(),
                      CoordKind.CARTESIAN)

    @parameterized.expand(
        [
            ((0, 0, QUOTIENT, 0, 0), (0, 1, QUOTIENT)),
            ((1, 0, QUOTIENT, 0, 0), (1, 0, QUOTIENT)),
            ((1, 6, 3, 0, 1), (5, 12, 3)),
        ]
    )
    def test_cartesian_to_zephyr(self, zcoord, ccoord):
        self.assertEqual(
            ZephyrCoord(*zcoord), ZephyrCartesianCoord(*
                                                       ccoord).convert(CoordKind.TOPOLOGY)
        )
        self.assertEqual(ZephyrCartesianCoord(*ccoord),
                         (ZephyrCoord(*zcoord)).convert(CoordKind.CARTESIAN))
        self.assertEqual(
            ZephyrCoord(*zcoord), (ZephyrCoord(*zcoord)
                                   ).convert(CoordKind.TOPOLOGY)
        )
        self.assertEqual(
            ZephyrCartesianCoord(
                *ccoord), (ZephyrCartesianCoord(*ccoord)).convert(CoordKind.CARTESIAN)
        )


class TestZephyrCoord(TestCase):
    @parameterized.expand(
        [
            ((1, 24, 0, 1, None),),  # All good except z_val
            ((2, 0, 0, 0, 0),),  # All good except u_val
            ((None, 3, 0, 0, 4),),  # All good except u_val
            ((0, -1, 1, 1, 3),),  # All good except w_val
            ((1, 23, -1, 1, 5),),  # All good except k_val
            ((1, 24, 1, 3.5, 9),),  # All good except j_val
        ]
    )
    def test_invalid_input_raises_error(self, uwkjz):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCoord(*uwkjz)

    @parameterized.expand(
        [
            ((0, 17, 4, 1, 0),),
            ((1, 0, QUOTIENT, 0, 0),),
            ((1, 2, 10, 1, 23),),
        ]
    )
    def test_valid_input_runs(self, uwkjz):
        ZephyrCoord(*uwkjz)

    @parameterized.expand([
        ((1, 24, 0, 1, 12), (12, 2), False),  # All good except z_val
        ((1, 20, 3, 1, 12), (12, 6), False),  # All good except z_val
        ((0, 0, 0, 0, 0), (1, 1), True),
        ((0, 0, 0, 0, 0), (1, QUOTIENT), False),
        ((0, 15, 2, 0, 0), (6, 4), False)
    ])
    def test_is_shape_consistent(self, uwkjz, shape, expected):
        self.assertEqual(ZephyrCoord(
            *uwkjz).is_shape_consistent(ZephyrShape(*shape)), expected)

    @parameterized.expand(
        [
            ((0, 0, 0, 0, 0), (6, QUOTIENT),),
            ((0, 15, 2, 0, 0), (6, 4),)
        ]
    )
    def test_to_non_quotient_raises_error(self, uwkjz, shape):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCoord(*uwkjz).to_non_quotient(ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((0, 3, 1, 0, 5), (6, 10), 1),
            ((1, 12, QUOTIENT, 1, 5), (6, 2), 2),
            ((0, 2, QUOTIENT, 1, 0), (1, 10), 10)
        ]
    )
    def test_to_non_quotient(self, uwkjz, shape, expected_len):
        self.assertEqual(
            len(ZephyrCoord(*uwkjz).to_non_quotient(ZephyrShape(*shape))),
            expected_len
        )

    @parameterized.expand([((0, 2, 4, 1, 5), ), ((1, 3, 3, 0, 0), ), ((1, 2, QUOTIENT, 1, 5), )])
    def test_zephyr_to_cartesian_runs(self, uwkjz):
        zcoord = ZephyrCoord(*uwkjz)
        self.assertIs(zcoord.convert(CoordKind.CARTESIAN).kind(),
                      CoordKind.CARTESIAN)
        self.assertIs(zcoord.convert(
            CoordKind.TOPOLOGY).kind(), CoordKind.TOPOLOGY)

    @parameterized.expand([((0, 2, 4, 1, 5), ), ((1, 3, 3, 0, 0), ), ((1, 2, QUOTIENT, 1, 5), )])
    def test_ccoord_to_zcoord(self, uwkjz):
        zcoord = ZephyrCoord(*uwkjz)
        ccoord = zcoord.convert(CoordKind.CARTESIAN)
        self.assertEqual(zcoord, ccoord.convert(CoordKind.TOPOLOGY))

    @parameterized.expand([((0, 1, QUOTIENT), ), ((1, 0, QUOTIENT), ), ((12, 3, QUOTIENT), )])
    def test_zcoord_to_ccoord(self, xyk):
        ccoord = ZephyrCartesianCoord(*xyk)
        zcoord = ccoord.convert(CoordKind.TOPOLOGY)
        self.assertEqual(ccoord, zcoord.convert(CoordKind.CARTESIAN))
