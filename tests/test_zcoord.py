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


from unittest import TestCase

from parameterized import parameterized

from dwave.graphs.topologies.common import CoordKind, _Infinite, _Quotient
from dwave.graphs.topologies.zephyr import (
    ZephyrCartesianCoord,
    ZephyrCoord,
    ZephyrShape,
    zephyr_coordinates,
)


class TestZephyrShape(TestCase):
    @parameterized.expand(
        [
            ((-1, 2),),
            ((0, 3),),
            ((3, -1),),
            ((_Quotient.QUOTIENT, 3),),
            ((3, _Infinite.INFINITE),),
            ((3, 0),),
        ]
    )
    def test_invalid_raises_error(self, bad_input):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrShape(*bad_input)

    @parameterized.expand(
        [
            ((4, 6),),
            ((1, 1),),
            ((1, 10),),
            ((),),
            ((_Infinite.INFINITE, _Quotient.QUOTIENT),),
            ((_Infinite.INFINITE, 1),),
            ((3, _Quotient.QUOTIENT),),
        ]
    )
    def test_valid_runs(self, good_shape):
        ZephyrShape(*good_shape)

    @parameterized.expand(
        [
            ((2, _Quotient.QUOTIENT), True),
            ((_Infinite.INFINITE, _Quotient.QUOTIENT), True),
            ((_Infinite.INFINITE, 1), False),
            ((4, 6), False),
            ((1, 1), False),
        ]
    )
    def test_is_quotient(self, shape, expected):
        self.assertEqual(ZephyrShape(*shape).is_quotient(), expected)

    @parameterized.expand(
        [
            ((2, 3), (2, _Quotient.QUOTIENT)),
            ((1, _Quotient.QUOTIENT), (1, _Quotient.QUOTIENT)),
            ((_Infinite.INFINITE, 3), (_Infinite.INFINITE, _Quotient.QUOTIENT)),
        ]
    )
    def test_to_quotient(self, shape, shape_quo):
        self.assertEqual(ZephyrShape(*shape).to_quotient(), ZephyrShape(*shape_quo))

    @parameterized.expand(
        [
            ((2, 3), (_Infinite.INFINITE, 3)),
            ((1, _Quotient.QUOTIENT), (_Infinite.INFINITE, _Quotient.QUOTIENT)),
            ((_Infinite.INFINITE, 4), (_Infinite.INFINITE, 4)),
        ]
    )
    def test_to_infinite(self, shape, shape_inf):
        self.assertEqual(ZephyrShape(*shape).to_infinite(), ZephyrShape(*shape_inf))

    @parameterized.expand(
        [
            ((_Infinite.INFINITE, 2), True),
            ((_Infinite.INFINITE, _Quotient.QUOTIENT), True),
            ((1, _Quotient.QUOTIENT), False),
            ((4, 6), False),
            ((1, 1), False),
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
            ((0, 1, -2),),
            ((-1, 2, _Quotient.QUOTIENT),),
        ]
    )
    def test_invalid_input_raises_error(self, xyk):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCartesianCoord(*xyk)

    @parameterized.expand(
        [
            ((0, 17, 4),),
            ((1, 0, _Quotient.QUOTIENT),),
            ((1, 2, 10),),
        ]
    )
    def test_valid_input_runs(self, xyk):
        ZephyrCartesianCoord(*xyk)

    @parameterized.expand(
        [
            ((17, 0, 0), (4, 1), False),
            ((0, 17, 0), (4, _Quotient.QUOTIENT), False),
            ((0, 3, 3), (1,), False),
            ((5, 2, 1), (6, _Quotient.QUOTIENT), False),
            ((5, 2, 1), (6, 1), False),
            ((5, 2, 1), (6, 2), True),
            ((16, 1, _Quotient.QUOTIENT), (4,), True),
            ((1, 12, 1), (3, 2), True),
            ((3, 0, _Quotient.QUOTIENT), (4,), True),
            ((6, 3, 10), (2, 12), True),
            ((5, 2, _Quotient.QUOTIENT), (6, 2), False),
        ]
    )
    def test_is_shape_consistent(self, xyk, shape, expected):
        self.assertEqual(
            ZephyrCartesianCoord(*xyk).is_shape_consistent(ZephyrShape(*shape)), expected
        )

    @parameterized.expand(
        [
            (
                (5, 2, 1),
                (6, 1),
            ),
            (
                (5, 2, 1),
                (6, _Quotient.QUOTIENT),
            ),
            ((17, 0, _Quotient.QUOTIENT), (4, 2)),
        ]
    )
    def test_to_non_quotient_raises_error(self, xyk, shape):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCartesianCoord(*xyk).to_non_quotient(ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((5, 2, 1), (6, 10), 1),
            ((5, 2, _Quotient.QUOTIENT), (6, 2), 2),
            ((1, 2, _Quotient.QUOTIENT), (1, 10), 10),
        ]
    )
    def test_to_non_quotient(self, xyk, shape, expected_len):
        self.assertEqual(
            len(ZephyrCartesianCoord(*xyk).to_non_quotient(ZephyrShape(*shape))), expected_len
        )

    @parameterized.expand([((0, 1, _Quotient.QUOTIENT),), ((12, 3, _Quotient.QUOTIENT),)])
    def test_cartesian_to_zephyr_runs(self, xyk):
        ccoord = ZephyrCartesianCoord(*xyk)
        self.assertIs(ccoord.convert(CoordKind.TOPOLOGY).kind, CoordKind.TOPOLOGY)
        self.assertIs(ccoord.convert(CoordKind.CARTESIAN).kind, CoordKind.CARTESIAN)

    @parameterized.expand(
        [
            ((0, 0, _Quotient.QUOTIENT, 0, 0), (0, 1, _Quotient.QUOTIENT)),
            ((1, 0, _Quotient.QUOTIENT, 0, 0), (1, 0, _Quotient.QUOTIENT)),
            ((1, 6, 3, 0, 1), (5, 12, 3)),
        ]
    )
    def test_cartesian_to_zephyr(self, zcoord, ccoord):
        self.assertEqual(
            ZephyrCoord(*zcoord), ZephyrCartesianCoord(*ccoord).convert(CoordKind.TOPOLOGY)
        )
        self.assertEqual(
            ZephyrCartesianCoord(*ccoord), (ZephyrCoord(*zcoord)).convert(CoordKind.CARTESIAN)
        )
        self.assertEqual(ZephyrCoord(*zcoord), (ZephyrCoord(*zcoord)).convert(CoordKind.TOPOLOGY))
        self.assertEqual(
            ZephyrCartesianCoord(*ccoord),
            (ZephyrCartesianCoord(*ccoord)).convert(CoordKind.CARTESIAN),
        )

    def test_eq_and_hash(self):
        a = ZephyrCartesianCoord(0, 1, 2)
        b = ZephyrCartesianCoord(0, 1, 2)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_quotient_orders_after_nonquotient(self):
        nonq = ZephyrCartesianCoord(0, 1, 2)
        quo = ZephyrCartesianCoord(0, 1, _Quotient.QUOTIENT)
        # (is_quotient, tuple): False < True, so non-quotient sorts first
        self.assertLess(nonq, quo)

    def test_iter_getitem_len(self):
        c = ZephyrCartesianCoord(0, 1, 2)
        self.assertEqual(tuple(c), (0, 1, 2))
        self.assertEqual(c[1], 1)
        self.assertEqual(len(c), 3)

    def test_cross_type_eq_is_notimplemented(self):
        self.assertNotEqual(ZephyrCartesianCoord(0, 1, 2), (0, 1, 2))

    def test_to_quotient(self):
        self.assertEqual(
            ZephyrCartesianCoord(5, 2, 1).to_quotient(),
            ZephyrCartesianCoord(5, 2, _Quotient.QUOTIENT),
        )

    @parameterized.expand([((6, _Quotient.QUOTIENT),), ((_Infinite.INFINITE, 2),)])
    def test_convert_to_linear_raises_error(self, shape):
        with self.assertRaises(ValueError):
            ZephyrCartesianCoord(5, 2, 1).convert(CoordKind.LINEAR, ZephyrShape(*shape))

    def test_convert_invalid_kind_raises_error(self):
        with self.assertRaises(ValueError):
            ZephyrCartesianCoord(5, 2, 1).convert("invalid_coord_kind")


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
            ((1, 0, _Quotient.QUOTIENT, 0, 0),),
            ((1, 2, 10, 1, 23),),
        ]
    )
    def test_valid_input_runs(self, uwkjz):
        ZephyrCoord(*uwkjz)

    @parameterized.expand(
        [
            ((1, 24, 0, 1, 12), (12, 2), False),  # All good except z_val
            ((1, 20, 3, 1, 12), (12, 6), False),  # All good except z_val
            ((0, 0, 0, 0, 0), (1, 1), True),
            ((0, 0, 0, 0, 0), (1, _Quotient.QUOTIENT), False),
            ((0, 15, 2, 0, 0), (6, 4), False),
            ((0, 3, _Quotient.QUOTIENT, 0, 2), (6, 4), False),
        ]
    )
    def test_is_shape_consistent(self, uwkjz, shape, expected):
        self.assertEqual(ZephyrCoord(*uwkjz).is_shape_consistent(ZephyrShape(*shape)), expected)

    @parameterized.expand(
        [
            (
                (0, 0, 0, 0, 0),
                (6, _Quotient.QUOTIENT),
            ),
            (
                (0, 15, 2, 0, 0),
                (6, 4),
            ),
            ((0, 15, _Quotient.QUOTIENT, 0, 0), (6, 4)),
        ]
    )
    def test_to_non_quotient_raises_error(self, uwkjz, shape):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCoord(*uwkjz).to_non_quotient(ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((0, 3, 1, 0, 5), (6, 10), 1),
            ((1, 12, _Quotient.QUOTIENT, 1, 5), (6, 2), 2),
            ((0, 2, _Quotient.QUOTIENT, 1, 0), (1, 10), 10),
        ]
    )
    def test_to_non_quotient(self, uwkjz, shape, expected_len):
        self.assertEqual(
            len(ZephyrCoord(*uwkjz).to_non_quotient(ZephyrShape(*shape))), expected_len
        )

    @parameterized.expand(
        [((0, 2, 4, 1, 5),), ((1, 3, 3, 0, 0),), ((1, 2, _Quotient.QUOTIENT, 1, 5),)]
    )
    def test_zephyr_to_cartesian_runs(self, uwkjz):
        zcoord = ZephyrCoord(*uwkjz)
        self.assertIs(zcoord.convert(CoordKind.CARTESIAN).kind, CoordKind.CARTESIAN)
        self.assertIs(zcoord.convert(CoordKind.TOPOLOGY).kind, CoordKind.TOPOLOGY)

    @parameterized.expand(
        [((0, 2, 4, 1, 5),), ((1, 3, 3, 0, 0),), ((1, 2, _Quotient.QUOTIENT, 1, 5),)]
    )
    def test_ccoord_to_zcoord(self, uwkjz):
        zcoord = ZephyrCoord(*uwkjz)
        ccoord = zcoord.convert(CoordKind.CARTESIAN)
        self.assertEqual(zcoord, ccoord.convert(CoordKind.TOPOLOGY))

    @parameterized.expand(
        [
            ((0, 1, _Quotient.QUOTIENT),),
            ((1, 0, _Quotient.QUOTIENT),),
            ((12, 3, _Quotient.QUOTIENT),),
        ]
    )
    def test_zcoord_to_ccoord(self, xyk):
        ccoord = ZephyrCartesianCoord(*xyk)
        zcoord = ccoord.convert(CoordKind.TOPOLOGY)
        self.assertEqual(ccoord, zcoord.convert(CoordKind.CARTESIAN))

    def test_to_quotient(self):
        self.assertEqual(
            ZephyrCoord(0, 3, 1, 0, 2).to_quotient(),
            ZephyrCoord(0, 3, _Quotient.QUOTIENT, 0, 2),
        )

    def test_convert_invalid_kind_raises_error(self):
        with self.assertRaises(ValueError):
            ZephyrCoord(0, 3, 1, 0, 2).convert("invalid_coord_kind")

    @parameterized.expand(
        [
            (ZephyrCartesianCoord(0, 1, _Quotient.QUOTIENT),),  # different Coord subclass
            (5,),  # non-Coord
            ((0, 0, _Quotient.QUOTIENT, 0, 0),),  # plain tuple
        ]
    )
    def test_eq_lt_notimplemented(self, other):
        coord = ZephyrCoord(0, 0, _Quotient.QUOTIENT, 0, 0)
        self.assertIs(coord.__eq__(other), NotImplemented)
        self.assertIs(coord.__lt__(other), NotImplemented)


class TestConvertToLinear(TestCase):

    def test_zephyr_to_linear_matches_converter(self):
        m, t = 2, 4
        coords = zephyr_coordinates(m, t)
        zc = ZephyrCoord(0, 1, 2, 1, 0)
        expected = coords.zephyr_to_linear(zc.to_tuple())
        # This will surface the is_quoutient typo as AttributeError today.
        self.assertEqual(zc.convert(CoordKind.LINEAR, ZephyrShape(m, t)), expected)

    def test_cartesian_to_linear_matches_converter(self):
        m, t = 2, 4
        coords = zephyr_coordinates(m, t)
        cc = ZephyrCartesianCoord(0, 1, 2)
        expected = coords.cartesian_to_linear(cc.to_tuple())
        self.assertEqual(cc.convert(CoordKind.LINEAR, ZephyrShape(m, t)), expected)

    def test_linear_requires_shape(self):
        with self.assertRaises(ValueError):
            ZephyrCoord(0, 1, 2, 1, 0).convert(CoordKind.LINEAR)
        with self.assertRaises(ValueError):
            ZephyrCartesianCoord(0, 1, 2).convert(CoordKind.LINEAR)

    def test_linear_rejects_quotient_and_infinite_shape(self):
        for shape in (ZephyrShape(2, _Quotient.QUOTIENT), ZephyrShape(_Infinite.INFINITE, 4)):
            with self.assertRaises(ValueError):
                ZephyrCoord(0, 1, 2, 1, 0).convert(CoordKind.LINEAR, shape)


class TestZephyrCoordinatesConverters(TestCase):

    @parameterized.expand([(2, 4), (3, 2), (1, 6)])
    def test_linear_zephyr_roundtrip(self, m, t):
        coords = zephyr_coordinates(m, t)
        n = 4 * t * m * (2 * m + 1)
        for r in range(0, n, max(1, n // 50)):
            self.assertEqual(coords.zephyr_to_linear(coords.linear_to_zephyr(r)), r)

    @parameterized.expand([(2, 4), (3, 2)])
    def test_linear_cartesian_roundtrip(self, m, t):
        coords = zephyr_coordinates(m, t)
        n = 4 * t * m * (2 * m + 1)
        for r in range(0, n, max(1, n // 50)):
            self.assertEqual(coords.cartesian_to_linear(coords.linear_to_cartesian(r)), r)

    def test_zephyr_cartesian_roundtrip(self):
        for uwkjz in [(0, 1, 2, 1, 0), (1, 3, 0, 0, 1), (0, 0, 3, 1, 2)]:
            c = zephyr_coordinates.zephyr_to_cartesian(uwkjz)
            self.assertEqual(zephyr_coordinates.cartesian_to_zephyr(c), uwkjz)
