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

from dwave.graphs.topologies.common import CoordKind, INFINITE, QUOTIENT
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
            ((QUOTIENT, 3),),
            ((3, INFINITE),),
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
            ((INFINITE, QUOTIENT),),
            ((INFINITE, 1),),
            ((3, QUOTIENT),),
        ]
    )
    def test_valid_runs(self, good_shape):
        ZephyrShape(*good_shape)

    @parameterized.expand(
        [
            ((2, QUOTIENT), True),
            ((INFINITE, QUOTIENT), True),
            ((INFINITE, 1), False),
            ((4, 6), False),
            ((1, 1), False),
        ]
    )
    def test_is_quotient(self, shape, expected):
        self.assertEqual(ZephyrShape(*shape).is_quotient, expected)

    @parameterized.expand(
        [
            ((2, 3), (2, QUOTIENT)),
            ((1, QUOTIENT), (1, QUOTIENT)),
            ((INFINITE, 3), (INFINITE, QUOTIENT)),
        ]
    )
    def test_to_quotient(self, shape, shape_quo):
        self.assertEqual(ZephyrShape(*shape).to_quotient(), ZephyrShape(*shape_quo))

    @parameterized.expand(
        [
            ((2, 3), (INFINITE, 3)),
            ((1, QUOTIENT), (INFINITE, QUOTIENT)),
            ((INFINITE, 4), (INFINITE, 4)),
        ]
    )
    def test_to_infinite(self, shape, shape_inf):
        self.assertEqual(ZephyrShape(*shape).to_infinite(), ZephyrShape(*shape_inf))

    @parameterized.expand(
        [
            ((INFINITE, 2), True),
            ((INFINITE, QUOTIENT), True),
            ((1, QUOTIENT), False),
            ((4, 6), False),
            ((1, 1), False),
        ]
    )
    def test_is_infinite(self, shape, expected):
        self.assertEqual(ZephyrShape(*shape).is_infinite, expected)

    @parameterized.expand([("m",), ("t",)])
    def test_shape_values_are_read_only(self, attr):
        shape = ZephyrShape(2, 4)
        with self.assertRaises(AttributeError):
            setattr(shape, attr, 7)

    def test_cached_tuple_cannot_go_stale(self):
        shape = ZephyrShape(2, 4)
        hash(shape)
        with self.assertRaises(AttributeError):
            shape.m = 7
        self.assertEqual(shape.to_tuple(), tuple(shape))
        self.assertEqual(shape, ZephyrShape(2, 4))
        self.assertNotEqual(shape, ZephyrShape(7, 4))


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

    @parameterized.expand(
        [
            ((17, 0, 0), (4, 1), False),
            ((0, 17, 0), (4, QUOTIENT), False),
            ((0, 3, 3), (1,), False),
            ((5, 2, 1), (6, QUOTIENT), False),
            ((5, 2, 1), (6, 1), False),
            ((5, 2, 1), (6, 2), True),
            ((16, 1, QUOTIENT), (4,), True),
            ((1, 12, 1), (3, 2), True),
            ((3, 0, QUOTIENT), (4,), True),
            ((6, 3, 10), (2, 12), True),
            ((5, 2, QUOTIENT), (6, 2), False),
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
                (6, QUOTIENT),
            ),
            ((17, 0, QUOTIENT), (4, 2)),
        ]
    )
    def test_to_non_quotient_raises_error(self, xyk, shape):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCartesianCoord(*xyk).to_non_quotient(ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((5, 2, 1), (6, 10), 1),
            ((5, 2, QUOTIENT), (6, 2), 2),
            ((1, 2, QUOTIENT), (1, 10), 10),
        ]
    )
    def test_to_non_quotient(self, xyk, shape, expected_len):
        self.assertEqual(
            len(ZephyrCartesianCoord(*xyk).to_non_quotient(ZephyrShape(*shape))), expected_len
        )

    @parameterized.expand([((0, 1, QUOTIENT),), ((12, 3, QUOTIENT),)])
    def test_cartesian_to_zephyr_runs(self, xyk):
        ccoord = ZephyrCartesianCoord(*xyk)
        self.assertIs(ccoord.convert(CoordKind.TOPOLOGY).kind, CoordKind.TOPOLOGY)
        self.assertIs(ccoord.convert(CoordKind.CARTESIAN).kind, CoordKind.CARTESIAN)

    @parameterized.expand(
        [
            ((0, 0, QUOTIENT, 0, 0), (0, 1, QUOTIENT)),
            ((1, 0, QUOTIENT, 0, 0), (1, 0, QUOTIENT)),
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
        quo = ZephyrCartesianCoord(0, 1, QUOTIENT)
        # (is_quotient, tuple): False < True, so non-quotient sorts first
        self.assertLess(nonq, quo)

    def test_iter_getitem_len(self):
        c = ZephyrCartesianCoord(0, 1, 2)
        self.assertEqual(tuple(c), (0, 1, 2))
        self.assertEqual(c[1], 1)
        self.assertEqual(len(c), 3)

    def test_cross_type_eq_is_notimplemented(self):
        self.assertNotEqual(ZephyrCartesianCoord(0, 1, 2), (0, 1, 2))

    @parameterized.expand([("x",), ("y",), ("k",)])
    def test_coord_values_are_read_only(self, attr):
        coord = ZephyrCartesianCoord(0, 1, 2)
        with self.assertRaises(AttributeError):
            setattr(coord, attr, 7)

    def test_to_quotient(self):
        self.assertEqual(
            ZephyrCartesianCoord(5, 2, 1).to_quotient(),
            ZephyrCartesianCoord(5, 2, QUOTIENT),
        )

    @parameterized.expand([((6, QUOTIENT),), ((INFINITE, 2),)])
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
            ((1, 0, QUOTIENT, 0, 0),),
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
            ((0, 0, 0, 0, 0), (1, QUOTIENT), False),
            ((0, 15, 2, 0, 0), (6, 4), False),
            ((0, 3, QUOTIENT, 0, 2), (6, 4), False),
        ]
    )
    def test_is_shape_consistent(self, uwkjz, shape, expected):
        self.assertEqual(ZephyrCoord(*uwkjz).is_shape_consistent(ZephyrShape(*shape)), expected)

    @parameterized.expand(
        [
            (
                (0, 0, 0, 0, 0),
                (6, QUOTIENT),
            ),
            (
                (0, 15, 2, 0, 0),
                (6, 4),
            ),
            ((0, 15, QUOTIENT, 0, 0), (6, 4)),
        ]
    )
    def test_to_non_quotient_raises_error(self, uwkjz, shape):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrCoord(*uwkjz).to_non_quotient(ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((0, 3, 1, 0, 5), (6, 10), 1),
            ((1, 12, QUOTIENT, 1, 5), (6, 2), 2),
            ((0, 2, QUOTIENT, 1, 0), (1, 10), 10),
        ]
    )
    def test_to_non_quotient(self, uwkjz, shape, expected_len):
        self.assertEqual(
            len(ZephyrCoord(*uwkjz).to_non_quotient(ZephyrShape(*shape))), expected_len
        )

    @parameterized.expand(
        [((0, 2, 4, 1, 5),), ((1, 3, 3, 0, 0),), ((1, 2, QUOTIENT, 1, 5),)]
    )
    def test_zephyr_to_cartesian_runs(self, uwkjz):
        zcoord = ZephyrCoord(*uwkjz)
        self.assertIs(zcoord.convert(CoordKind.CARTESIAN).kind, CoordKind.CARTESIAN)
        self.assertIs(zcoord.convert(CoordKind.TOPOLOGY).kind, CoordKind.TOPOLOGY)

    @parameterized.expand(
        [((0, 2, 4, 1, 5),), ((1, 3, 3, 0, 0),), ((1, 2, QUOTIENT, 1, 5),)]
    )
    def test_ccoord_to_zcoord(self, uwkjz):
        zcoord = ZephyrCoord(*uwkjz)
        ccoord = zcoord.convert(CoordKind.CARTESIAN)
        self.assertEqual(zcoord, ccoord.convert(CoordKind.TOPOLOGY))

    @parameterized.expand(
        [
            ((0, 1, QUOTIENT),),
            ((1, 0, QUOTIENT),),
            ((12, 3, QUOTIENT),),
        ]
    )
    def test_zcoord_to_ccoord(self, xyk):
        ccoord = ZephyrCartesianCoord(*xyk)
        zcoord = ccoord.convert(CoordKind.TOPOLOGY)
        self.assertEqual(ccoord, zcoord.convert(CoordKind.CARTESIAN))

    def test_to_quotient(self):
        self.assertEqual(
            ZephyrCoord(0, 3, 1, 0, 2).to_quotient(),
            ZephyrCoord(0, 3, QUOTIENT, 0, 2),
        )

    def test_convert_invalid_kind_raises_error(self):
        with self.assertRaises(ValueError):
            ZephyrCoord(0, 3, 1, 0, 2).convert("invalid_coord_kind")

    @parameterized.expand(
        [
            (ZephyrCartesianCoord(0, 1, QUOTIENT),),  # different Coord subclass
            (5,),  # non-Coord
            ((0, 0, QUOTIENT, 0, 0),),  # plain tuple
        ]
    )
    def test_eq_lt_notimplemented(self, other):
        coord = ZephyrCoord(0, 0, QUOTIENT, 0, 0)
        self.assertIs(coord.__eq__(other), NotImplemented)
        self.assertIs(coord.__lt__(other), NotImplemented)

    @parameterized.expand([("u",), ("w",), ("k",), ("j",), ("z",)])
    def test_coord_values_are_read_only(self, attr):
        coord = ZephyrCoord(0, 1, 2, 0, 3)
        with self.assertRaises(AttributeError):
            setattr(coord, attr, 7)

    def test_cached_tuple_cannot_go_stale(self):
        coord = ZephyrCoord(0, 1, 2, 0, 3)
        hash(coord)
        with self.assertRaises(AttributeError):
            coord.w = 7
        self.assertEqual(coord.to_tuple(), tuple(coord))
        self.assertEqual(coord, ZephyrCoord(0, 1, 2, 0, 3))
        self.assertNotEqual(coord, ZephyrCoord(0, 7, 2, 0, 3))


class TestConvertToLinear(TestCase):

    def test_zephyr_to_linear_matches_converter(self):
        m, t = 2, 4
        coords = zephyr_coordinates(m, t)
        zc = ZephyrCoord(0, 1, 2, 1, 0)
        expected = coords.zephyr_to_linear(zc.to_tuple())
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
        for shape in (ZephyrShape(2, QUOTIENT), ZephyrShape(INFINITE, 4)):
            with self.assertRaises(ValueError):
                ZephyrCoord(0, 1, 2, 1, 0).convert(CoordKind.LINEAR, shape)

    @parameterized.expand(
        [
            ((0, 5, 0, 0, 0), (2, 4),),
            ((0, 0, 0, 0, 2), (2, 4),),
            ((0, 0, 4, 0, 0), (2, 4),),
        ]
    )
    def test_linear_rejects_out_of_shape_zephyr_coord(self, uwkjz, shape):
        coord = ZephyrCoord(*uwkjz)
        self.assertFalse(coord.is_shape_consistent(ZephyrShape(*shape)))
        with self.assertRaises(ValueError):
            coord.convert(CoordKind.LINEAR, ZephyrShape(*shape))

    @parameterized.expand(
        [
            ((17, 2, 1), (2, 4),),
            ((0, 17, 1),(2, 4),),
            ((0, 1, 4),(2, 4),),
        ]
    )
    def test_linear_rejects_out_of_shape_cartesian_coord(self, xyk, shape):
        coord = ZephyrCartesianCoord(*xyk)
        self.assertFalse(coord.is_shape_consistent(ZephyrShape(*shape)))
        with self.assertRaises(ValueError):
            coord.convert(CoordKind.LINEAR, ZephyrShape(*shape))

    def test_linear_rejects_quotient_coord(self):
        for coord in (
            ZephyrCoord(0, 1, QUOTIENT, 1, 0),
            ZephyrCartesianCoord(0, 1, QUOTIENT),
        ):
            with self.assertRaises(ValueError):
                coord.convert(CoordKind.LINEAR, ZephyrShape(2, 4))

    def test_linear_in_shape_coords_are_unique_and_contiguous(self):
        m, t = 2, 4
        shape = ZephyrShape(m, t)
        indices = [
            ZephyrCoord(u, w, k, j, z).convert(CoordKind.LINEAR, shape)
            for u in range(2)
            for w in range(2 * m + 1)
            for k in range(t)
            for j in range(2)
            for z in range(m)
        ]
        self.assertEqual(sorted(indices), list(range(4 * t * m * (2 * m + 1))))


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
