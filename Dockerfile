FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/ll2tofbx/.venv \
    HOME=/tmp \
    XDG_CONFIG_HOME=/tmp/.config \
    XDG_CACHE_HOME=/tmp/.cache

# Blender itself comes from the `bpy` wheel; these are the X11/GL client
# libraries that wheel links against (nothing here opens a display).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgl1 \
        libsm6 \
        libx11-6 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxkbcommon0 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir uv

WORKDIR /opt/ll2tofbx

COPY pyproject.toml uv.lock README.md /opt/ll2tofbx/
RUN uv sync --frozen --no-dev --no-install-project

COPY src /opt/ll2tofbx/src
RUN uv sync --frozen --no-dev --no-editable

ENV PATH="/opt/ll2tofbx/.venv/bin:${PATH}"

ENTRYPOINT ["ll2tofbx"]
CMD ["--help"]
