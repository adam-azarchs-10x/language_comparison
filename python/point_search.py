#!/usr/bin/env python

"""
Methods to load points into a quad tree, and query for points in the tree
by proximity to a centroid.
"""

import collections
import math
import optparse
import sys

Point = collections.namedtuple('Point', ['x', 'y'])

def read_points(stream, skip_header=True):
    """Get an iterable of x,y points from an iterable of csv lines."""
    for line in stream:
        if skip_header:
            skip_header = False
        else:
            split = line.split(',')
            try:
                yield Point(float(split[0]), float(split[1]))
            except ValueError:
                sys.stderr.write('Invalid line %s\n' % line)


def read_points_from_file(filename):
    """Get a list of x,y points from a file."""
    with open(filename, 'r') as point_file:
        return list(read_points(point_file))


_MAX_TREE_RESOLUTION = 2.5


class QuadTree(object):
    """Stores x,y points in a quad tree.

    Includes methods to add points and retrieve them by proximity to a given
    centroid.
    """
    def __init__(self, center, halfwidth):
        """
        Args:
            center: The center of this quad
            size: The half width of the quad.
        """
        self._ur = None
        self._lr = None
        self._ul = None
        self._ll = None
        self._center = center
        self._width = halfwidth
        self._points = []

    def _is_in_box(self, point):
        """Checks that a point is in is node."""
        return (point.x >= self._center.x - self._width and
                point.x <= self._center.x + self._width and
                point.y >= self._center.y - self._width and
                point.y <= self._center.y + self._width)

    def max_radius(self):
        """Returns a radius which captures the entire tree."""
        return self._width * math.sqrt(2.0)

    def add_point(self, point):
        """Add a point to this tree."""
        assert self._is_in_box(point)
        if self._width <= _MAX_TREE_RESOLUTION:
            self._points.append(point)
        elif point.x < self._center.x:
            if point.y < self._center.y:
                if not self._ll:
                    self._ll = QuadTree(
                        Point(self._center.x - self._width / 2,
                              self._center.y - self._width / 2),
                        self._width / 2)
                self._ll.add_point(point)
            else:
                if not self._ul:
                    self._ul = QuadTree(
                        Point(self._center.x - self._width / 2,
                              self._center.y + self._width / 2),
                        self._width / 2)
                self._ul.add_point(point)
        else:
            if point.y < self._center.y:
                if not self._lr:
                    self._lr = QuadTree(
                        Point(self._center.x + self._width / 2,
                              self._center.y - self._width / 2),
                        self._width / 2)
                self._lr.add_point(point)
            else:
                if not self._ur:
                    self._ur = QuadTree(
                        Point(self._center.x + self._width / 2,
                              self._center.y + self._width / 2),
                        self._width / 2)
                self._ur.add_point(point)

    def all_points(self):
        """Iterates over all points in the tree."""
        for point in self._points:
            yield point
        if self._ll:
            for point in self._ll.all_points():
                yield point
        if self._ul:
            for point in self._ul.all_points():
                yield point
        if self._lr:
            for point in self._lr.all_points():
                yield point
        if self._ur:
            for point in self._ur.all_points():
                yield point

    def points_in_box(self, lower_left, upper_right):
        """Find all the points in this tree which fall within the given box.
        Args:
            lower_left: the minimum x,y of the box of interest
            upper_right: the maximum x, y of the box of interest
        """
        for point in self._points:
            if (point.x >= lower_left.x and point.y >= lower_left.y and
                    point.x <= upper_right.x and point.y <= upper_right.y):
                yield point
        if lower_left.x < self._center.x:
            if lower_left.y < self._center.y and self._ll:
                for point in self._ll.points_in_box(lower_left, upper_right):
                    yield point
            if upper_right.y > self._center.y and self._ul:
                for point in self._ul.points_in_box(lower_left, upper_right):
                    yield point
        if upper_right.x > self._center.x:
            if lower_left.y < self._center.y and self._lr:
                for point in self._lr.points_in_box(lower_left, upper_right):
                    yield point
            if upper_right.y > self._center.y and self._ur:
                for point in self._ur.points_in_box(lower_left, upper_right):
                    yield point

    def points_in_radius(self, centroid, radius):
        """Returns an iterable of the points in this tree which fall within the
        given radius of the given centroid."""
        if abs(centroid.x - self._center.x) > radius + self._width:
            return
        if abs(centroid.y - self._center.y) > radius + self._width:
            return
        r_sq = radius ** 2
        for point in self.points_in_box(Point(centroid.x - radius,
                                              centroid.y - radius),
                                        Point(centroid.x + radius,
                                              centroid.y + radius)):
            if ((point.x - centroid.x) ** 2 +
                    (point.y - centroid.y) ** 2) <= r_sq:
                yield point


def make_tree(points):
    """Given a list of points, return them as a tree."""
    xmin = min([p.x for p in points])
    xmax = max([p.x for p in points])
    ymin = min([p.y for p in points])
    ymax = max([p.y for p in points])
    tree = QuadTree(Point((xmax + xmin)/2, (ymax + ymin)/2),
                    max((xmax - xmin), (ymax - ymin)) / 2.0 + 0.001)
    for point in points:
        tree.add_point(point)
    return tree


def near_points(tree, centroids, radius):
    """Returns all of the points in the tree within radius of any centroid."""
    pts = set()
    for centroid in centroids:
        for point in tree.points_in_radius(centroid, radius):
            pts.add(point)
    return pts


def _quadratic_interpolate(x1, y1, x2, y2, target_y):
    """
    Computes the x value for which a quadratic function hitting x1,y1 and
    x2,y2 would have a y value of target_y.

    We use this because we expect the count near the centroids to be
    proportional to the square of the radius, though there may be regions
    where the proportionality is closer to linear.
    """
    x1 = float(x1)
    x2 = float(x2)
    y1 = float(y1)
    y2 = float(y2)
    assert x2 > x1
    assert y2 >= y1
    assert x1 >= 0
    assert y1 >= 0
    target_y = float(target_y)
    if x1 == 0:
        return x2 * math.sqrt(target_y / y2)
    d = x1 * x2 * (x2 - x1)
    a = (x1 * y2 - x2 * y1) / d
    b = (x2**2 * y1 - x1**2 * y2) / d 
    return (math.sqrt(4.0 * a * target_y + b**2) - b ) / (2.0 * a)


def newton_search(tree, centroids, radius, target_count):
    """
    Performs a newton search on the radius to find the radius for which
    target_count points in the tree are within radius of one of the centroids.

    Returns the radius and the number near at that radius, which might not be
    the exact target under unfavorable arrangements of points and centroids.
    """
    if target_count <= 0:
        return 0, near_points(tree, centroids, 0)
    low_radius = radius
    low_count = len(near_points(tree, centroids, radius))
    if low_count == target_count:
        return radius, low_count
    high_radius = tree.max_radius()
    high_count = len(set(tree.all_points()))
    if high_count <= target_count:
        return high_radius, high_count

    if low_count > target_count:
        high_radius = low_radius
        high_count = low_count
        low_radius = 0
        low_count = 0
    while high_radius - low_radius > 0.000001:
        mid_radius = _quadratic_interpolate(low_radius, low_count, high_radius,
                                            high_count, target_count)
        sys.stderr.write("Trying radius %f\n" % mid_radius)
        assert mid_radius < high_radius
        assert mid_radius > low_radius
        mid_count = len(near_points(tree, centroids, mid_radius))
        if abs(mid_count - target_count) < 0.5:
            return mid_radius, mid_count
        elif mid_count < target_count:
            low_radius = mid_radius
            low_count = mid_count
        else:
            high_radius = mid_radius
            high_count = mid_count
    sys.stderr.write("Warning: couldn't get the exact number of points.\n")
    return high_radius, high_count


def main(argv):
    """Front end."""
    parser = optparse.OptionParser(usage=
        "usage: %prog [options] point_file centroid_file")
    parser.add_option('--radius', '-r', type='float', default=5.0,
        help="The radius in which to search for points")
    parser.add_option('--target-percent', type='float', default=None,
        dest='percent',
        help="The target number of points to find.  Radius will be "
             "adjusted until the target is reached.")
    parser.add_option('--list-points', action='store_true', dest='list_points',
        help="List the found points, rather than just their count.")
    options, argv = parser.parse_args(argv)
    if len(argv) != 3:
        parser.print_help()
        return 1
    pts = read_points_from_file(argv[1])
    sys.stderr.write("Read %d points.\n" % len(pts))
    tree = make_tree(pts)
    sys.stderr.write("Tree constructed.\n")
    centroids = read_points_from_file(argv[2])
    sys.stderr.write("Read %d centroids.\n" % len(centroids))
    if options.percent:
        target_count = int(round(float(len(pts)) * options.percent / 100.0))
        sys.stderr.write("Trying to find a radius that gets %d points.\n" %
                         target_count)
        rad, cnt = newton_search(tree, centroids, options.radius, target_count)
        print("%d points within radius %f." % (cnt, rad))
    else:
        pts = near_points(tree, centroids, options.radius)
        if options.list_points:
            print("X,Y")
            for point in pts:
                print("%f,%f" % (point.x, point.y))
        else:
            print("%d points within %f of the given centroids."
                  % (len(pts), options.radius))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
