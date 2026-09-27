#!/usr/bin/env bash
set -euo pipefail

# Runs `ll2tofbx export` inside the image. The current directory is mounted at
# the same absolute path inside the container, so pass --input/--output/
# --report/--log paths that live under it.
IMAGE_TAG="${LL2TOFBX_IMAGE:-ll2tofbx:local}"
WORK_DIR="$(pwd)"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e XDG_CONFIG_HOME=/tmp/.config \
  -e XDG_CACHE_HOME=/tmp/.cache \
  -v "${WORK_DIR}:${WORK_DIR}" \
  -w "${WORK_DIR}" \
  "${IMAGE_TAG}" \
  export "$@"
