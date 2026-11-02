"""Sanity checks on the case geometry: valid solids with the expected outer dimensions."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # repo root, for the import below
import sayodevice_case as case

TOL = 0.01   # mm


@pytest.fixture(scope="module")
def top():
    return case.build_top()


@pytest.fixture(scope="module")
def bottom():
    return case.build_bottom()


def test_top_is_valid_solid(top):
    assert top.val().isValid()


def test_bottom_is_valid_solid(bottom):
    assert bottom.val().isValid()


def test_top_footprint(top):
    bb = top.val().BoundingBox()
    assert bb.xlen == pytest.approx(case.CASE_W, abs=TOL)
    assert bb.ylen == pytest.approx(case.CASE_D, abs=TOL)


def test_top_sits_on_base(top):
    bb = top.val().BoundingBox()
    assert bb.zmin == pytest.approx(case.BOTTOM_H, abs=TOL)
    assert bb.zlen == pytest.approx(case.TOP_H, abs=TOL)


def test_bottom_height(bottom):
    bb = bottom.val().BoundingBox()
    assert bb.zlen == pytest.approx(case.BOTTOM_H + case.POST_H, abs=TOL)
