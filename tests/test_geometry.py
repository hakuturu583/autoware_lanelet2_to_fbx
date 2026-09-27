import unittest


from autoware_lanelet2_to_fbx.geometry import cumulative_distances, polyline_length
from autoware_lanelet2_to_fbx.mesh_types import Vec3


class GeometryTests(unittest.TestCase):
    def test_cumulative_distances_follow_polyline_segments(self):
        points = [
            Vec3(0.0, 0.0, 0.0),
            Vec3(3.0, 4.0, 0.0),
            Vec3(3.0, 4.0, 12.0),
        ]

        self.assertEqual(cumulative_distances(points), [0.0, 5.0, 17.0])

    def test_cumulative_distances_empty_polyline_matches_existing_helpers(self):
        self.assertEqual(cumulative_distances([]), [0.0])

    def test_polyline_length_returns_total_distance(self):
        points = [
            Vec3(0.0, 0.0, 0.0),
            Vec3(0.0, 5.0, 0.0),
            Vec3(12.0, 5.0, 0.0),
        ]

        self.assertEqual(polyline_length(points), 17.0)


if __name__ == "__main__":
    unittest.main()
