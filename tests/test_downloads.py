"""Check the committed files in download/ match what sayodevice_case.py builds now.

Fails if the script was changed but the download files weren't regenerated.
STEP and STL files can't be compared byte-for-byte (STEP has timestamps, and
STL triangulation can differ slightly between machines), so the geometry is
compared instead.
"""
import os
import sys

import cadquery as cq
import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)   # repo root, for the import below
import sayodevice_case as case

DOWNLOAD = os.path.join(ROOT, "download")
STALE = ("download/ is out of date with sayodevice_case.py - "
         "rebuild it with `python sayodevice_case.py --download` and commit the files")

MAX_DIFF_VOLUME = 0.01   # mm^3, volume that's in one shape but not the other
MAX_VERTEX_DIST = 0.01   # mm, STL corners must lie on the built part's surface
MAX_MESH_VOL_ERR = 1e-3  # relative, STL volume vs the exact solid (tessellation error)

PARTS = {"top": case.build_top, "bottom": case.build_bottom}


@pytest.fixture(scope="module")
def built():
    return {name: build().val() for name, build in PARTS.items()}


def read_stl(path):
    """Triangles from a binary STL as an (n, 3, 3) array."""
    with open(path, "rb") as f:
        data = f.read()
    n = int.from_bytes(data[80:84], "little")
    tri = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    return np.frombuffer(data, dtype=tri, count=n, offset=84)["v"].astype(float)


def mesh_volume(tris):
    """Volume enclosed by a closed triangle mesh (sum of signed tetrahedra)."""
    return abs(np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum() / 6)


@pytest.mark.parametrize("name", PARTS)
def test_step_matches_script(built, name):
    solid = built[name]
    filed = cq.importers.importStep(os.path.join(DOWNLOAD, f"o3c_case_{name}.step")).val()
    # symmetric difference: catches any change, even a moved hole that keeps the volume the same
    diff = solid.cut(filed).Volume() + filed.cut(solid).Volume()
    assert diff < MAX_DIFF_VOLUME, f"o3c_case_{name}.step differs by {diff:.3f} mm^3. {STALE}"


@pytest.mark.parametrize("name", PARTS)
def test_stl_matches_script(built, name):
    solid = built[name]
    tris = read_stl(os.path.join(DOWNLOAD, f"o3c_case_{name}.stl"))
    assert len(tris) > 0, f"o3c_case_{name}.stl has no triangles"

    vol_err = abs(mesh_volume(tris) - solid.Volume()) / solid.Volume()
    assert vol_err < MAX_MESH_VOL_ERR, f"o3c_case_{name}.stl volume is off by {vol_err:.2%}. {STALE}"

    verts = np.unique(tris.reshape(-1, 3), axis=0)
    worst = max(solid.distance(cq.Vertex.makeVertex(*p)) for p in verts)
    assert worst < MAX_VERTEX_DIST, f"o3c_case_{name}.stl is {worst:.3f} mm off the model. {STALE}"
