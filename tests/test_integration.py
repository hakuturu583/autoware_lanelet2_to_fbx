"""End-to-end tests against a real Lanelet2 map.

These load ``tests/data/two_lane_road.osm`` through simple-lanelet2 and, for the
``blender`` ones, export an FBX through ``bpy`` (or a Blender executable) and read
it back.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from autoware_lanelet2_to_fbx.cli import main
from autoware_lanelet2_to_fbx.godot_extract import extract_feature_set
from autoware_lanelet2_to_fbx.lanelet_loader import load_lanelet_map
from autoware_lanelet2_to_fbx.layer_names import LAYER_NAMES
from autoware_lanelet2_to_fbx.osm_index import load_osm_index

MAP_PATH = Path(__file__).resolve().parent / "data" / "two_lane_road.osm"

HAS_BLENDER = importlib.util.find_spec("bpy") is not None or shutil.which("blender") is not None
requires_blender = pytest.mark.skipif(not HAS_BLENDER, reason="neither bpy nor a blender executable is available")


def test_osm_index_reads_local_coordinates_and_geo_reference():
    osm_index = load_osm_index(MAP_PATH)
    assert len(osm_index.nodes) == 22
    assert osm_index.first_geo_reference is not None
    first = osm_index.nodes[1]
    assert (first.local_x, first.local_y, first.ele) == (0.0, 3.5, 10.0)


def test_simple_lanelet2_loads_the_map_and_features_are_extracted():
    osm_index = load_osm_index(MAP_PATH)
    loaded = load_lanelet_map(MAP_PATH, osm_index)
    assert loaded.load_errors == []
    assert len(loaded.lanelet_map.laneletLayer) == 2

    feature_set = extract_feature_set(loaded.lanelet_map, loaded.coordinate_resolver)
    assert len(feature_set.lanelet_roads) == 2
    assert len(feature_set.intersection_areas) == 1
    assert len(feature_set.hatched_areas) == 1
    assert len(feature_set.road_borders) == 2
    assert sorted(marking.feature_type for marking in feature_set.road_markings) == ["line_thin", "stop_line"]
    # The resolver prefers the OSM local_x/local_y/ele tags over the projection.
    lanelet = feature_set.lanelet_roads[0]
    assert {(point.y, point.z) for point in lanelet.left + lanelet.right} <= {
        (3.5, 10.0),
        (0.0, 10.0),
        (-3.5, 10.0),
    }


@requires_blender
@pytest.mark.blender
def test_export_writes_an_fbx_with_every_layer(tmp_path: Path):
    output = tmp_path / "two_lane_road.fbx"
    report_path = tmp_path / "two_lane_road.report.json"
    exit_code = main(
        [
            "export",
            "--input",
            str(MAP_PATH),
            "--output",
            str(output),
            "--report",
            str(report_path),
            "--lanelet-side-overlap",
            "0.3",
        ]
    )
    report = json.loads(report_path.read_text())
    assert exit_code == 0, report["validation"]["errors"]
    assert report["success"] is True
    assert report["validation"]["errors"] == []
    assert output.stat().st_size > 0
    assert report["layer_stats"]["lanelet_road"]["triangle_count"] > 0
    assert report["layer_stats"]["road_extention"]["triangle_count"] > 0

    assert _fbx_object_names(output) >= {"two_lane_road", *LAYER_NAMES}


def _fbx_object_names(path: Path) -> set[str]:
    """Import ``path`` in a fresh Blender process and return its object names."""
    script = (
        "import sys, bpy\n"
        "bpy.ops.wm.read_factory_settings(use_empty=True)\n"
        "bpy.ops.import_scene.fbx(filepath=sys.argv[-1])\n"
        "print('OBJECTS=' + '|'.join(sorted(o.name for o in bpy.data.objects)))\n"
    )
    if importlib.util.find_spec("bpy") is not None:
        command = [sys.executable, "-c", script, str(path)]
    else:
        command = ["blender", "--background", "--factory-startup", "--python-expr", script, "--", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    line = next(line for line in result.stdout.splitlines() if line.startswith("OBJECTS="))
    return set(line.removeprefix("OBJECTS=").split("|"))
