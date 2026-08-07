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

from dwave.graphs.topologies.common import EdgeKind, NodeKind, _Infinite, _Quotient
from dwave.graphs.topologies.zephyr import (ZephyrCartesianCoord, ZephyrCoord, ZephyrEdge,
                                            ZephyrNode, ZephyrPlaneShift, ZephyrShape)


class TestZephyrEdge(unittest.TestCase):

    @parameterized.expand(
        [
            (ZephyrCoord(0, 10, 3, 1, 3), ZephyrCoord(0, 10, 3, 1, 2), ZephyrShape(6, 4)),
            (ZephyrCartesianCoord(4, 3, 2), ZephyrCartesianCoord(4, 1, 2), (6, 3)),
            ((1, 6, _Quotient.QUOTIENT), (5, 6, _Quotient.QUOTIENT), None),
        ]
    )
    def test_valid_input_runs(self, x, y, shape) -> None:
        zn_x = ZephyrNode(coord=x, shape=shape)
        zn_y = ZephyrNode(coord=y, shape=shape)

        ZephyrEdge(zn_x, zn_y)

    @parameterized.expand(
        [
            ((2, 4), AttributeError),
            (
                (
                    ZephyrNode(coord=ZephyrCartesianCoord(4, 3, 2), shape=(6, 3)),
                    ZephyrNode(coord=ZephyrCartesianCoord(4, 3, 2), shape=(6, 3)),
                ),
                ValueError,
            ),
        ]
    )
    def test_invalid_input_raises_error(self, invalid_edge, expected_err):
        with self.assertRaises(expected_err):
            ZephyrEdge(*invalid_edge)


U_VALS = [0, 1]
J_VALS = [0, 1]
M_VALS = [1, 6, 12]
T_VALS = [1, 2, 4, 6]


class TestZephyrNode(unittest.TestCase):
    def setUp(self):
        self.u_vals = [0, 1]
        self.invalid_u_vals = [2, -1, None, 3.5]
        self.invalid_w_vals = [-1]
        self.j_vals = [0, 1]
        self.invalid_j_vals = [2, -1, None, 3.5]
        self.m_vals = [6, 1, 20]
        self.invalid_m_vals = [0, 2.5, -3]
        self.t_vals = [6, 1, 20]
        self.invalid_t_vals = [0, 2.5, -2]
        self.invalid_z_vals = [-1, None]
        xym_vals = [
            ((0, 3), 1),
            ((5, 2), 6),
            ((16, 1), 4),
            ((1, 12), 3),
            ((3, 0), 4),
            ((5, 4), 6),
            ((0, 3), 6),
            ((6, 3), 5),
        ]
        self.xyms = xym_vals + [(xy, _Infinite.INFINITE) for xy, _ in xym_vals]
        self.left_up_xyms = [
            ((0, 3), 6),
            ((0, 3), _Infinite.INFINITE),
            ((11, 0), _Infinite.INFINITE),
            ((0, 5), 8),
        ]
        self.right_down_xyms = [((1, 12), 3), ((16, 1), 4)]
        self.midgrid_xyms = [((5, 2), 6), ((5, 4), 6), ((6, 7), 5)]

    @parameterized.expand(
        [
            ((u, w, k, j, z), (m, t))
            for u in U_VALS
            for j in J_VALS
            for m in M_VALS
            for t in T_VALS
            for w in range(2 * m + 1)
            for k in range(t)
            for z in range(m)
        ][::100]
    )
    def test_znode_topology_coord_runs(self, uwkjz, mt):
        ZephyrNode(coord=uwkjz, shape=mt)

    @parameterized.expand(
        [
            ((-1, 2), 6),
            ((6, -1), 4),
            ((1, 3), -5),
            ((1, 3), 6),
            ((2, 4), 6),
            ((17, 0), 4),
            ((0, 17), 4),
            ((0, 0, 0), 1),
            ((-1, 2), None),
        ]
    )
    def test_bad_args_raises_error_ccoord(self, xy, m):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrNode(coord=xy, shape=ZephyrShape(m=m))

    @parameterized.expand(
        [
            ((2, 0, 0, 0, 0), (6, 4)),  # All good except u_val
            ((None, 3, 0, 0, 4), (6, 1)),  # All good except u_val
            ((3.5, 8, 2, 0, 0), (8, 4)),  # All good except u_val
            ((0, -1, 1, 1, 3), (6, 4)),  # All good except w_val
            ((0, 10, 2.5, 0, 5), (6, 4)),  # All good except k_val
            ((1, 23, -1, 1, 5), (12, 2)),  # All good except k_val
            ((1, 24, 1, 3.5, 9), (12, 4)),  # All good except j_val
            ((1, 24, 0, 1, None), (12, 2)),  # All good except z_val
            ((1, 20, 3, 1, 12), (12, 6)),  # All good except z_val
            ((0, 0, 0, 0, 0), (0, 0)),  # All good except m_val
            ((0, 0, 0, 0, 0), (1, -1)),  # All good except t_val
        ]
    )
    def test_bad_args_raises_error_zcoord(self, uwkjz, mt):
        with self.assertRaises((ValueError, TypeError)):
            ZephyrNode(coord=uwkjz, shape=mt)

    @parameterized.expand(
        [
            ((0, 3), 6, ZephyrPlaneShift(-1, -1)),
            ((0, 3), _Infinite.INFINITE, ZephyrPlaneShift(-1, -1)),
            ((11, 0), _Infinite.INFINITE, ZephyrPlaneShift(-1, -1)),
            ((0, 5), 8, ZephyrPlaneShift(-1, -1)),
            ((1, 12), 3, ZephyrPlaneShift(1, 1)),
            ((16, 1), 4, ZephyrPlaneShift(1, 1)),
        ]
    )
    def test_add_sub_raises_error_invalid(self, xy, m, zps) -> None:
        zn = ZephyrNode(xy, ZephyrShape(m=m))
        with self.assertRaises(ValueError):
            zn + zps

    @parameterized.expand(
        [
            (
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrPlaneShift(-2, -2),
                ZephyrNode((3, 0), ZephyrShape(6)),
            ),
            (
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrPlaneShift(2, -2),
                ZephyrNode((7, 0), ZephyrShape(6)),
            ),
            (
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrPlaneShift(2, 2),
                ZephyrNode((7, 4), ZephyrShape(6)),
            ),
            (
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrPlaneShift(-2, 2),
                ZephyrNode((3, 4), ZephyrShape(6)),
            ),
            (
                ZephyrNode((5, 4), ZephyrShape(4)),
                ZephyrPlaneShift(-4, -4),
                ZephyrNode((1, 0), ZephyrShape(4)),
            ),
            (
                ZephyrNode((6, 7), ZephyrShape(5)),
                ZephyrPlaneShift(1, 11),
                ZephyrNode((7, 18), ZephyrShape(5)),
            ),
            (
                ZephyrNode((0, 3), ZephyrShape(6)),
                ZephyrPlaneShift(0, 0),
                ZephyrNode((0, 3), ZephyrShape(6)),
            ),
            (
                ZephyrNode((1, 12), ZephyrShape(3)),
                ZephyrPlaneShift(1, -1),
                ZephyrNode((2, 11), ZephyrShape(3)),
            ),
        ]
    )
    def test_add_sub(self, zn, zps, expected) -> None:
        self.assertEqual(zn + zps, expected)

    def test_neighbors_boundary(self) -> None:
        x, y, k, t = 1, 12, 4, 6
        expected_nbrs = {
            ZephyrNode((x + i, y + j, kp), ZephyrShape(t=t))
            for i in (-1, 1)
            for j in (-1, 1)
            for kp in range(t)
        }
        expected_nbrs |= {
            ZephyrNode((x + 2, y, k), ZephyrShape(t=t)),
            ZephyrNode((x + 4, y, k), ZephyrShape(t=t)),
        }
        self.assertEqual(set(ZephyrNode((x, y, k), ZephyrShape(t=t)).neighbors()), expected_nbrs)

    def test_neighbors_mid(self):
        x, y, k, t = 10, 5, 3, 6
        expected_nbrs = {
            ZephyrNode((x + i, y + j, kp), ZephyrShape(t=t))
            for i in (-1, 1)
            for j in (-1, 1)
            for kp in range(t)
        }
        expected_nbrs |= {
            ZephyrNode((x, y + 4, k), ZephyrShape(t=t)),
            ZephyrNode((x, y - 4, k), ZephyrShape(t=t)),
        }
        expected_nbrs |= {
            ZephyrNode((x, y + 2, k), ZephyrShape(t=t)),
            ZephyrNode((x, y - 2, k), ZephyrShape(t=t)),
        }
        self.assertEqual(set(ZephyrNode((x, y, k), ZephyrShape(t=t)).neighbors()), expected_nbrs)

    def test_zcoord(self) -> None:
        ZephyrNode((11, 12, 4), ZephyrShape(t=6)).zcoord == ZephyrCoord(1, 0, 4, 0, 2)
        ZephyrNode((1, 0)).zcoord == ZephyrCoord(1, 0, _Quotient.QUOTIENT, 0, 0)
        ZephyrNode((0, 1)).zcoord == ZephyrCoord(0, 0, _Quotient.QUOTIENT, 0, 0)

    @parameterized.expand(
        [
            ((u, w, k, j, z), (m, t))
            for u in U_VALS
            for j in J_VALS
            for m in M_VALS
            for t in T_VALS
            for w in range(2 * m + 1)
            for k in range(t)
            for z in range(m)
        ][::300]
    )
    def test_direction(self, uwkjz, mt) -> None:
        zn = ZephyrNode(coord=uwkjz, shape=mt)
        self.assertEqual(zn.direction, uwkjz[0])

    @parameterized.expand(
        [
            ((u, w, k, j, z), (m, t))
            for u in U_VALS
            for j in J_VALS
            for m in M_VALS
            for t in T_VALS
            for w in range(2 * m + 1)
            for k in range(t)
            for z in range(m)
        ][::200]
    )
    def test_node_kind(self, uwkjz, mt) -> None:
        zn = ZephyrNode(coord=uwkjz, shape=mt)
        if uwkjz[0] == 0:
            self.assertTrue(zn.is_vertical())
            self.assertEqual(zn.node_kind, NodeKind.VERTICAL)
        else:
            self.assertTrue(zn.is_horizontal())
            self.assertEqual(zn.node_kind, NodeKind.HORIZONTAL)

    @parameterized.expand(
        [
            (ZephyrNode((1, 0)), EdgeKind.INTERNAL),
            (ZephyrNode((1, 2)), EdgeKind.INTERNAL),
            (ZephyrNode((0, 3)), EdgeKind.ODD),
            (ZephyrNode((0, 5)), EdgeKind.EXTERNAL),
            (ZephyrNode((0, 7)), EdgeKind.INVALID),
            (ZephyrNode((1, 6)), EdgeKind.INVALID),
        ]
    )
    def test_neighbor_kind(self, zn1, nbr_kind) -> None:
        zn0 = ZephyrNode((0, 1))
        self.assertIs(zn0.neighbor_edge_kind(zn1), nbr_kind)

    @parameterized.expand(
        [
            (ZephyrNode((0, 1)), {ZephyrNode((1, 0)), ZephyrNode((1, 2))}),
            (
                ZephyrNode((0, 1, 0), ZephyrShape(t=4)),
                {ZephyrNode((1, 0, k), ZephyrShape(t=4)) for k in range(4)}
                | {ZephyrNode((1, 2, k), ZephyrShape(t=4)) for k in range(4)},
            ),
        ]
    )
    def test_internal(self, zn, expected) -> None:
        set_internal = {x for x in zn.internal_neighbors()}
        self.assertEqual(set_internal, expected)

    @parameterized.expand(
        [
            (ZephyrNode((0, 1)), {ZephyrNode((0, 5))}),
            (ZephyrNode((0, 1, 2), ZephyrShape(t=4)), {ZephyrNode((0, 5, 2), ZephyrShape(t=4))}),
            (
                ZephyrNode((11, 6, 3), ZephyrShape(t=4)),
                {ZephyrNode((7, 6, 3), ZephyrShape(t=4)), ZephyrNode((15, 6, 3), ZephyrShape(t=4))},
            ),
        ]
    )
    def test_external(self, zn, expected) -> None:
        set_external = {x for x in zn.external_neighbors()}
        self.assertEqual(set_external, expected)

    @parameterized.expand(
        [
            (ZephyrNode((0, 1)), {ZephyrNode((0, 3))}),
            (ZephyrNode((0, 1, 2), ZephyrShape(t=4)), {ZephyrNode((0, 3, 2), ZephyrShape(t=4))}),
            (ZephyrNode((15, 8)), {ZephyrNode((13, 8)), ZephyrNode((17, 8))}),
        ]
    )
    def test_odd(self, zn, expected) -> None:
        set_odd = {x for x in zn.odd_neighbors()}
        self.assertEqual(set_odd, expected)

    @parameterized.expand(
        [
            ((5, 2), 6, None, 4, 4),
            ((5, 2), 6, EdgeKind.INTERNAL, 4, 0),
            ((5, 2), 10, EdgeKind.EXTERNAL, 0, 2),
            ((5, 2), 4, [EdgeKind.INTERNAL, EdgeKind.EXTERNAL], 4, 2),
            ((5, 2), 3, [EdgeKind.ODD], 0, 2),
            ((6, 7), 12, None, 4, 4),
            ((6, 7), 8, EdgeKind.INTERNAL, 4, 0),
            ((6, 7), 12, EdgeKind.EXTERNAL, 0, 2),
            ((6, 7), 12, EdgeKind.ODD, 0, 2),
            ((0, 1), 4, EdgeKind.INTERNAL, 2, 0),
            ((0, 1), 2, EdgeKind.ODD, 0, 1),
            ((0, 1), 4, EdgeKind.EXTERNAL, 0, 1),
            ((0, 1), 4, None, 2, 2),
            ((24, 5), _Infinite.INFINITE, EdgeKind.INTERNAL, 4, 0),
            ((24, 5), _Infinite.INFINITE, EdgeKind.ODD, 0, 2),
            ((24, 5), _Infinite.INFINITE, EdgeKind.EXTERNAL, 0, 2),
            ((24, 5), _Infinite.INFINITE, None, 4, 4),
            ((24, 5), 6, EdgeKind.INTERNAL, 2, 0),
            ((24, 5), 8, EdgeKind.ODD, 0, 2),
            ((24, 5), 6, EdgeKind.EXTERNAL, 0, 2),
            ((24, 5), 8, None, 4, 4),
            ((24, 5), 8, EdgeKind.INVALID, 0, 0),
        ]
    )
    def test_degree(self, xy, m, nbr_kind, a, b) -> None:
        for t in [_Quotient.QUOTIENT, 1, 4, 6]:
            if t is _Quotient.QUOTIENT:
                coord, t_p = xy, 1
            else:
                coord, t_p = xy + (0,), t
            zn = ZephyrNode(coord=coord, shape=ZephyrShape(m=m, t=t))

            with self.subTest(case=t):
                self.assertEqual(zn.degree(nbr_kind=nbr_kind), a * t_p + b)

    @parameterized.expand(
        [
            (
                ZephyrNode((7, 4), ZephyrShape(6)),
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrPlaneShift(2, 2),
            ),
            (
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrNode((5, 2), ZephyrShape(6)),
                ZephyrPlaneShift(0, 0),
            ),
        ]
    )
    def test_sub(self, a, b, expected):
        self.assertEqual(a - b, expected)

    def test_add_sub_inverse(self):
        n = ZephyrNode((5, 2), ZephyrShape(6))
        shift = ZephyrPlaneShift(2, 2)
        self.assertEqual((n + shift) - n, shift)

    def test_ccoord_and_topology_coord_properties(self):
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        self.assertEqual(zn.ccoord, ZephyrCartesianCoord(5, 2, _Quotient.QUOTIENT))
        self.assertEqual(zn.topology_coord, zn.zcoord)

    def test_four_tuple_coord(self):
        self.assertEqual(
            ZephyrNode((0, 1, 0, 0)),
            ZephyrNode((0, 1, _Quotient.QUOTIENT, 0, 0)),
        )

    @parameterized.expand(
        [
            (EdgeKind.INTERNAL,),
            (EdgeKind.EXTERNAL,),
            (EdgeKind.ODD,),
        ]
    )
    def test_neighbors_where_filter_excludes_all(self, nbr_kind):
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        self.assertTrue(list(zn.neighbors(nbr_kind=nbr_kind)))
        self.assertEqual(list(zn.neighbors(nbr_kind=nbr_kind, where=lambda c: False)), [])

    @parameterized.expand(
        [
            ((1,), ValueError),
            ((1, 2), ValueError),
        ]
    )
    def test_add_invalid_shift_conversion(self, bad_shift, expected_err):
        zn = ZephyrNode((5, 2), ZephyrShape(6))
        with self.assertRaises(expected_err):
            zn + bad_shift

    def test_sub_invalid_delta(self):
        shape = ZephyrShape(6)
        a = ZephyrNode((5, 2), shape)
        b = ZephyrNode(
            ZephyrCartesianCoord(5, 3, _Quotient.QUOTIENT, check_coord=False),
            shape=shape,
            check_node_valid=False,
        )
        with self.assertRaises(ValueError):
            a - b
