import unittest


from autoware_lanelet2_to_fbx.layer_names import LAYER_NAMES, OPTIONAL_LAYER_NAMES, ROAD_SURFACE_LAYER_NAMES


class LayerNamesTests(unittest.TestCase):
    def test_optional_layers_are_known_layers(self):
        self.assertLessEqual(OPTIONAL_LAYER_NAMES, set(LAYER_NAMES))

    def test_road_surface_layers_are_known_layers(self):
        self.assertLessEqual(ROAD_SURFACE_LAYER_NAMES, set(LAYER_NAMES))


if __name__ == "__main__":
    unittest.main()
