from __future__ import print_function

import sys
import time
from optparse import OptionParser

import ezdxf

__version__ = "0.1"


class Stitcher(object):
    def __init__(self, input_name, output_name):
        self.old = ezdxf.readfile(input_name)
        self.new = ezdxf.new()
        self.output_name = output_name

        self.partial_loops = []
        self.closed_loops = []
        # This can reconstruct polylines that are stored in the correct order.
        # It does not destroy the direction, and works even if the segments are
        # randomly ordered.

        stats = {
            "last_match": 0,
            "insert": 0,
            "random_order": 0,
            "stitch_reversed": 0,
            "approx_match": 0,
        }

        self.load_partial_loops()

    def load_partial_loops(self):
        t0 = time.time()
        for line in self.old.modelspace().query("LINE"):
            for i, p in enumerate(self.partial_loops):
                if p[-1] == line.dxf.start:
                    p.append(line.dxf.end)
                    # if i == 0:
                    #    stats['last_match'] += 1
                    break
            else:
                self.partial_loops.insert(0, [line.dxf.start, line.dxf.end])
                # stats['insert'] += 1
        t1 = time.time()
        print("Grouped segments in", t1 - t0)

    def promote_closed_loops(self):
        t0 = time.time()
        for i in range(len(self.partial_loops) - 1, -1, -1):
            if (
                self.partial_loops[i][0] == self.partial_loops[i][-1]
                and len(self.partial_loops[i]) > 2
            ):
                self.closed_loops.append(self.partial_loops.pop(i))
        t1 = time.time()
        print("promote", t1 - t0)

    def promote_circles(self):
        """Promotes closed loops that are made of almost identical length
        segments to be circles based on the *point* distance (matching openscad
        behavior for polygonal approximations."""

        for i in range(len(self.closed_loops) - 1, -1, -1):
            c = find_circle_center(self.closed_loops[i])
            print("closed loops", len(self.closed_loops[i]), "center", c)
            if c is not None:
                r = dist(c, self.closed_loops[i][0])
                self.new.modelspace().add_circle(c, r)
                del self.closed_loops[i]

    def reconstruct_loops(self):
        t0 = time.time()
        for i in range(len(self.partial_loops) - 1):
            for j in range(len(self.partial_loops) - 1, i, -1):
                if self.partial_loops[i][-1] == self.partial_loops[j][0]:
                    self.partial_loops[i].extend(self.partial_loops.pop(j))
        t1 = time.time()
        print("reconstruct", t1 - t0)

    """

    t1 = time.time()
    print "De-randomized in", t1-t0

    t0 = time.time()
    for i in range(len(partial_loops)-1, -1, -1):
        if (partial_loops[i][0] == partial_loops[i][-1] and
            len(partial_loops[i]) > 2):
            closed_loops.append(partial_loops.pop(i))

    for i in range(len(partial_loops)-1):
        for j in range(len(partial_loops)-1, i, -1):
            if partial_loops[i][-1] == partial_loops[j][-1]:
                partial_loops[i].extend(partial_loops.pop(j)[::-1])
                stats['stitch_reversed'] += 1

    t1 = time.time()
    print "Corrected order in", t1-t0

    for i in range(len(partial_loops)-1, -1, -1):
        if (partial_loops[i][0] == partial_loops[i][-1] and
            len(partial_loops[i]) > 2):
            closed_loops.append(partial_loops.pop(i))

    stats['closed'] = len(closed_loops)
    stats['partial'] = len(partial_loops)
    print stats

    if partial_loops:
        print partial_loops[0]

    """

    def save(self):
        for c in self.closed_loops:
            self.new.modelspace().add_polyline2d(c)

        for p in self.partial_loops:
            self.new.modelspace().add_polyline2d(p)

        self.new.filename = self.output_name
        self.new.save()


def bounds_elementwise(lst):
    """Given a non-empty list, returns (mins, maxes) each of which is the same
    length as the list items.

    >>> bounds_elementwise([[0,6,0], [5,0,7]])
    ([0,0,0], [5,6,7])
    """
    indices = list(range(len(lst[0])))
    mins = [min(el[i] for el in lst) for i in indices]
    maxes = [max(el[i] for el in lst) for i in indices]
    return (mins, maxes)


def boundingbox(polyline):
    """Returns the bounding box, inclusive."""
    mins, maxes = bounds_elementwise(polyline)
    return [mins[0], mins[1], maxes[0], maxes[1]]


def bounding_box_intersect(b1, b2):
    # A A B B = no intersect (except perhaps if they touch at edge)
    # A B B A = yes
    # A B A B = yes
    x_pts = sorted([(b1[0], 1), (b1[2], 1), (b2[0], 2), (b2[2], 2)])
    y_pts = sorted([(b1[1], 1), (b1[3], 1), (b2[1], 2), (b2[3], 2)])
    return x_pts[0][1] != x_pts[1][1] and y_pts[0][1] != y_pts[1][1]


def dist(pt1, pt2):
    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]
    return ((dx * dx) + (dy * dy)) ** 0.5


def close(a, b, e=0.01):
    return abs(a - b) < e


def find_arc_center(pts, start):
    """Finds the center of an arc starting with pts[start:].

    Returns ((x,y), radius, count), or None.

    The count will never be fewer than 3.

    All the middle segments will have the same length, and their perpendicular
    bisectors will all point at the same `center`, which is `radius` units away
    from the points (not the bisected line).

    The first and last may be shorter, but if they were the same length, their
    perpendicular bisectors would satisfy the same requirement.

    TODO: Does this work with a circle?  (It should not accidentally pick
    segments a half-circle away from each other.)
    """

    if start < len(pts) - 2:
        return None

    ideal_dist = dist(pts[start + 1], pts[start + 2])
    i = start + 2
    while i < len(pts) and close(ideal_dist, dist(pts[i], pts[i + 1])):
        end = i + 1
        i += 1

    # pts[start+1:end] inclusive are segments the same length


def find_circle_center(polyline):
    # Closed polylines will have first point duplicated, so odd are actually an
    # even number of unique points.

    if len(polyline) % 2 == 1:
        box = boundingbox(polyline)
        center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

        dists = [dist(center, pt) for pt in polyline[:-1]]
        m, n = min(dists), max(dists)
        if abs(m - n) > 0.01:
            return None
    else:
        center = find_arc_center(polyline, 0)
        # TODO crosscheck using some other points
    return center


def main(args=None):
    parser = OptionParser()
    parser.add_option("-o", "--output-file", action="store", help="Name of output file")
    (options, args) = parser.parse_args()

    if not args:
        print("Input filename is required")
        sys.exit(1)

    s = Stitcher(args[0], options.output_file or (args[0] + ".new.dxf"))
    s.reconstruct_loops()
    s.promote_closed_loops()
    s.promote_circles()
    s.save()


if __name__ == "__main__":
    main()
