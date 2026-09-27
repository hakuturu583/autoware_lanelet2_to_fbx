# autoware_lanelet2_to_fbx

`autoware-lanelet2-to-fbx` converts Autoware Lanelet2 `.osm` maps into layered
FBX meshes for CARLA. Alongside the FBX it writes a JSON report and a log, so a
conversion can be checked without opening the FBX first.

The package was ported from the `feat/lanelet2-to-fbx` branch of
[tier4/autoware_lanelet2_to_opendrive](https://github.com/tier4/autoware_lanelet2_to_opendrive),
where it lived as `lanelet2_to_fbx/` (`ll2tofbx`), with two changes to how it is
installed:

- **Lanelet2 comes from [`simple-lanelet2`](https://github.com/hakuturu583/simple_lanelet2)**,
  a prebuilt abi3 wheel that reimplements the Lanelet2 Python API, instead of the
  per-interpreter Boost.Python `lanelet2` bindings.
- **Blender comes from the [`bpy`](https://pypi.org/project/bpy/) wheel**
  instead of a system `blender` package. `bpy` ships for exactly one CPython per
  Blender line, and with Lanelet2 no longer tying the interpreter down, each
  supported Python simply gets the line that ships for it.

| Python | `bpy` installed | FBX export via |
| --- | --- | --- |
| 3.11 | `>=4.2,<5.1` | `bpy` in a child process of the same interpreter |
| 3.12 | none (no wheel exists) | `blender` on `PATH`, or `BLENDER_BIN` |
| 3.13 | `>=5.1` | `bpy` in a child process of the same interpreter |

`BLENDER_BIN` always takes precedence when set.

## Install

```bash
uv sync            # or: pip install .
uv run ll2tofbx export --help
```

No compiler, system Blender or Docker is required on Linux `x86_64`, macOS or
Windows. The `bpy` wheel links against the X11/GL client libraries, which desktop
installs already have. On a minimal headless image (e.g. `python:*-slim`),
install them first (nothing opens a display):

```bash
apt-get install -y --no-install-recommends \
  libgl1 libsm6 libx11-6 libxext6 libxfixes3 libxi6 libxkbcommon0 libxrender1
```

## Quick Start

```bash
mkdir -p out
uv run ll2tofbx export \
  --input lanelet2_map.osm \
  --output out/lanelet2_map.fbx \
  --report out/lanelet2_map.report.json \
  --log out/lanelet2_map.log
```

Then check the report:

- `success` is `true`
- `validation.errors` is empty
- the `*.fbx` file exists

## Common Conversion Examples

### Basic Odaiba conversion

`--lanelet-side-overlap 0.3` keeps the original `lanelet_road` layer and also
adds a `road_extention` layer widened by 0.3 m on both sides. Use
`--keep-intermediate` when the intermediate OBJ/MTL files should be preserved.

```bash
uv run ll2tofbx export \
  --input "odaiba_ll2_raw.osm" \
  --output "out/odaiba_ll2_raw_ver4.fbx" \
  --report "out/odaiba_ll2_raw_ver4.report.json" \
  --log "out/odaiba_ll2_raw_ver4.log" \
  --lanelet-side-overlap 0.3 \
  --keep-intermediate
```

### Export ground layers as flat surfaces

`--surface-style flat` exports ground layers as double-sided surfaces instead
of solid meshes with thickness. This applies to `lanelet_road`,
`road_extention`, `intersection_area`, `hatched_area`, `parking_lot`, and
`shoulder`.

In this mode, `--road-thickness` is ignored.

```bash
uv run ll2tofbx export \
  --input "odaiba_ll2_raw.osm" \
  --output "out/odaiba_ll2_raw_flat_ground.fbx" \
  --report "out/odaiba_ll2_raw_flat_ground.report.json" \
  --log "out/odaiba_ll2_raw_flat_ground.log" \
  --lanelet-side-overlap 0.3 \
  --surface-style flat
```

### Export road markings as flat surfaces

`--marking-style flat` exports `road_marking` as nearly flat surfaces instead
of raised prisms. The default `--marking-offset 0.002` lifts markings 2 mm
above the road surface to reduce z-fighting.

In this mode, `--marking-thickness` is ignored.

```bash
uv run ll2tofbx export \
  --input "odaiba_ll2_raw.osm" \
  --output "out/odaiba_ll2_raw_flat_marking.fbx" \
  --report "out/odaiba_ll2_raw_flat_marking.report.json" \
  --log "out/odaiba_ll2_raw_flat_marking.log" \
  --lanelet-side-overlap 0.3 \
  --marking-style flat
```

### Align the FBX with an existing OpenDRIVE offset

If another tool has already produced an OpenDRIVE map with a known offset, use
`--origin explicit` and pass the same values to
`--shift-x`, `--shift-y`, and `--shift-z`.

The FBX vertices are exported as:

```text
vertex = local_coordinate - shift
```

Use this rule when matching coordinate origins:

```text
OpenDRIVE offset.x/y/z = FBX --shift-x/--shift-y/--shift-z
```

For the Odaiba map, use:

```bash
uv run ll2tofbx export \
  --input "odaiba_ll2_raw.osm" \
  --output "out/odaiba_ll2_raw_aligned.fbx" \
  --report "out/odaiba_ll2_raw_aligned.report.json" \
  --log "out/odaiba_ll2_raw_aligned.log" \
  --origin explicit \
  --shift-x 92008.5 \
  --shift-y 45335.1 \
  --shift-z 0.0
```

If the OpenDRIVE offset is `0, 0, 0`, still use explicit origin mode:

```bash
uv run ll2tofbx export \
  --input "lanelet2_map.osm" \
  --output "out/lanelet2_map_aligned.fbx" \
  --report "out/lanelet2_map_aligned.report.json" \
  --log "out/lanelet2_map_aligned.log" \
  --origin explicit \
  --shift-x 0 \
  --shift-y 0 \
  --shift-z 0
```

Do not use `--origin center` when the FBX needs to match another local
coordinate system. `center` recenters the map around the road surface bounds,
so it will not match an external OpenDRIVE offset.

## Common CLI Options

These are the options most commonly used with `ll2tofbx export`.

| Option | Description |
| --- | --- |
| `--input` | Input Lanelet2 OSM file |
| `--output` | Output FBX path |
| `--report` | Output JSON report path |
| `--log` | Log output path. If omitted, a `.log` file is written next to the report |
| `--origin center` | Default. Automatically shifts the map so the road surface is near the origin |
| `--origin explicit` | Uses the given shift values exactly |
| `--shift-x` `--shift-y` `--shift-z` | Shift values used with `--origin explicit` |
| `--surface-style` | `solid` or `flat`. `flat` exports ground layers as double-sided surfaces |
| `--lanelet-side-overlap` | Extra road support surface width added outside lanelet boundaries, in meters |
| `--marking-style` | `prism` or `flat`. `flat` exports markings as nearly flat surfaces |
| `--keep-intermediate` | Keeps the intermediate OBJ/MTL files |

## Lanelet Side Overlap

`--lanelet-side-overlap` adds a widened support surface without changing the
original `lanelet_road` mesh.

In the output FBX:

- `lanelet_road` is generated from the original lanelet width
- `road_extention` is generated by widening both sides by the given distance

For example, `--lanelet-side-overlap 0.3` creates a `road_extention` surface
that extends 0.3 m beyond each side of the original lanelet road. This is useful
when CARLA needs a more continuous drivable surface or when small visual gaps
appear between lanelets.

Recommended starting values:

- `0.0`: no widening
- `0.2` to `0.3`: practical first values to try

Large values can create unintended overlaps with nearby geometry.

## Coordinate Shift Modes

The default `--origin center` mode automatically shifts the road surface so the
map is near the FBX origin. This is convenient when the FBX only needs to be
placed near `(0, 0, 0)`.

Use `--origin explicit` when the FBX must align with another map or simulator
coordinate system:

```bash
--origin explicit \
--shift-x <offset_x> \
--shift-y <offset_y> \
--shift-z <offset_z>
```

`--shift-x`, `--shift-y`, and `--shift-z` are only valid with
`--origin explicit`.

## Outputs

The main outputs are:

- `*.fbx`
- `*.report.json`
- `*.log`

When `--keep-intermediate` is used, the intermediate OBJ/MTL files are also
preserved.

## Troubleshooting

If `success` is `false`, inspect the JSON report first.

Useful report fields include:

- `validation.errors`
- `validation.warnings`
- `filtered_source_counts`
- `blender_command`

The report is usually the fastest way to understand
what happened during conversion.

## Development

```bash
uv sync --dev
uv run pytest -n auto              # tests; the `blender` ones need bpy or blender
uv run pre-commit run --all-files  # ruff, ruff-format, mypy
```

`tests/data/two_lane_road.osm` is a small hand-written map (two lanes, road
borders, a stop line, an intersection area and a hatched area) that the
end-to-end tests load through simple-lanelet2 and export through Blender.
