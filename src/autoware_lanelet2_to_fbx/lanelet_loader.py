from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .mesh_types import Vec3
from .osm_index import OsmIndex

# `lanelet2` is provided by simple-lanelet2, a prebuilt abi3 wheel that
# reimplements the Lanelet2 Python API. Unlike the C++/Boost bindings it has no
# interpreter ceiling, so it no longer constrains which `bpy` can be installed.
from lanelet2.io import Origin, loadRobust
from lanelet2.projection import UtmProjector


@dataclass
class LoadedLaneletMap:
    lanelet_map: object
    load_errors: list[str]
    coordinate_resolver: Callable[[object], Vec3]


def load_lanelet_map(path: str | Path, osm_index: OsmIndex) -> LoadedLaneletMap:
    osm_path = Path(path).resolve()
    origin = osm_index.first_geo_reference or (0.0, 0.0)
    projector = UtmProjector(Origin(origin[0], origin[1]))
    lanelet_map, errors = loadRobust(str(osm_path), projector)
    load_errors = [str(error) for error in errors]
    return LoadedLaneletMap(
        lanelet_map=lanelet_map,
        load_errors=load_errors,
        coordinate_resolver=_make_coordinate_resolver(osm_index),
    )


def _make_coordinate_resolver(osm_index: OsmIndex) -> Callable[[object], Vec3]:
    def resolve(point: object) -> Vec3:
        point_id = getattr(point, "id", None)
        if point_id is not None:
            osm_node = osm_index.nodes.get(int(point_id))
            if osm_node and osm_node.local_x is not None and osm_node.local_y is not None:
                z_value = osm_node.ele
                if z_value is None:
                    z_value = float(getattr(point, "z", 0.0))
                return Vec3(float(osm_node.local_x), float(osm_node.local_y), float(z_value))
        return Vec3(
            float(getattr(point, "x", 0.0)),
            float(getattr(point, "y", 0.0)),
            float(getattr(point, "z", 0.0)),
        )

    return resolve
