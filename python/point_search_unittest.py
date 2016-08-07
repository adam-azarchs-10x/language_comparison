#!/usr/bin/env python
"""Unit tests for point_search"""

import unittest
import math

import point_search as ps

class PointSearchTest(unittest.TestCase):
    def test_read_points(self):
        pts = list(ps.read_points(["X,Y\n", "1,1\n", "2,2\n", "3,3\n"]))
        self.assertListEqual(pts, [(1, 1), (2, 2), (3, 3)])

    def test_quadratic_interpolate(self):
        self.assertEquals(ps._quadratic_interpolate(1.0, 1, 3.0, 9, 4), 2.0)
        self.assertEquals(ps._quadratic_interpolate(0.0, 0, 3.0, 9, 4), 2.0)
        self.assertEquals(ps._quadratic_interpolate(1.0, 2, 3.0, 12, 6), 2.0)

    def test_quad_tree_small(self):
        tree = ps.QuadTree(ps.Point(0,0), 1)
        tree.add_point(ps.Point(-1, -1))
        tree.add_point(ps.Point(1, 1))
        tree.add_point(ps.Point(0, 0))
        tree.add_point(ps.Point(0.5, 0.5))
        pts = ps.near_points(tree, [ps.Point(0, 0)], tree.max_radius())
        self.assertEquals(set(tree.all_points()), pts)
        self.assertEquals(len(pts), 4)
        self.assertEquals(len(ps.near_points(tree, [ps.Point(0, 0)], 0.9)), 2)


    def test_quad_tree_large(self):
        tree = ps.QuadTree(ps.Point(0, 0), 8)
        tree.add_point(ps.Point(-8, -8))
        tree.add_point(ps.Point(8, 8))
        tree.add_point(ps.Point(0, 8))
        tree.add_point(ps.Point(8, 0))
        tree.add_point(ps.Point(0, 0))
        tree.add_point(ps.Point(4, 4))
        pts = ps.near_points(tree, [ps.Point(0, 0)], tree.max_radius())
        self.assertEquals(len(pts), 6)
        self.assertEquals(set(tree.all_points()), pts)
        pts = ps.near_points(tree, [ps.Point(0, 0)], tree.max_radius() + 1)
        self.assertEquals(len(pts), 6)
        self.assertEquals(set(tree.all_points()), pts)
        pts = ps.near_points(tree, [ps.Point(10, 1)], 1)
        self.assertEquals(len(pts), 0)
        pts = ps.near_points(tree, [ps.Point(1, 10)], 1)
        self.assertEquals(len(pts), 0)
        self.assertEquals(len(ps.near_points(tree, [ps.Point(0, 0)], 7)), 2)
        self.assertEquals(len(ps.near_points(tree, [ps.Point(0, 0)], 8)), 4)
        self.assertEquals(len(ps.near_points(tree, [ps.Point(4, 4)], 7)), 5)
        self.assertEquals(len(ps.near_points(tree,
                                            [ps.Point(6, 6), ps.Point(-6, -6)],
                                            3)),
                          3)


    def test_newton_search(self):
        tree = ps.make_tree([
                ps.Point(0, 0),
                ps.Point(-8, -8),
                ps.Point(8, 8),
                ps.Point(0, 8),
                ps.Point(8, 0),
                ps.Point(0, 0),
                ps.Point(4, 4),
            ])
        radius, count = ps.newton_search(tree, [ps.Point(4, 5)], 5.5, 3)
        self.assertEquals(radius, 5.5)
        self.assertEquals(count, 3)
        radius, count = ps.newton_search(tree, [ps.Point(4, 5)], 7, 3)
        self.assertTrue(radius >= math.sqrt(3**2 + 4**2))
        self.assertTrue(radius < math.sqrt(5**2 + 4**2))
        self.assertEquals(count, 3)
        radius, count = ps.newton_search(tree, [ps.Point(4, 4)], 7, 3)
        self.assertEquals(count, 5)


if __name__ == '__main__':
    unittest.main()
