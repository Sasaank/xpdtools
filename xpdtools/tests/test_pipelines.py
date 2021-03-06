import numpy as np
import pyFAI
import pytest
import tifffile

from xpdsim import pyfai_poni, image_file
from xpdtools.pipelines.raw_pipeline import (
    pipeline_order,
    namespace as g_namespace,
)
from streamz_ext.link import link
from xpdtools.pipelines.extra import z_score_gen
from streamz_ext import destroy_pipeline

img = tifffile.imread(image_file)
geo = pyFAI.load(pyfai_poni)


@pytest.mark.parametrize("mask_s", ["first", "none", "auto"])
def test_raw_pipeline(mask_s):
    # link the pipeline up
    namespace = link(*pipeline_order, **g_namespace)

    is_calibration_img = namespace["is_calibration_img"]
    geo_input = namespace["geo_input"]
    img_counter = namespace["img_counter"]
    namespace["mask_setting"]["setting"] = mask_s

    pdf = namespace["pdf"]
    raw_background_dark = namespace["raw_background_dark"]
    raw_background = namespace["raw_background"]
    raw_foreground_dark = namespace["raw_foreground_dark"]
    composition = namespace["composition"]
    raw_foreground = namespace["raw_foreground"]
    sl = pdf.sink_to_list()
    L = namespace["geometry"].sink_to_list()
    ml = namespace["mask"].sink_to_list()

    is_calibration_img.emit(False)
    a = geo.getPyFAI()
    geo_input.emit(a)
    for s in [raw_background_dark, raw_background, raw_foreground_dark]:
        s.emit(np.zeros(img.shape))
    composition.emit("Au")
    img_counter.emit(1)
    raw_foreground.emit(img)
    destroy_pipeline(raw_foreground)
    del namespace
    assert len(L) == 1
    assert ml
    assert len(sl) == 1
    sl.clear()
    L.clear()
    ml.clear()


def test_extra_pipeline():
    # link the pipeline up
    namespace = link(*(pipeline_order + [z_score_gen]), **g_namespace)

    geometry = namespace["geometry"]

    z_score = namespace["z_score"]
    raw_background_dark = namespace["raw_background_dark"]
    raw_background = namespace["raw_background"]
    raw_foreground_dark = namespace["raw_foreground_dark"]
    raw_foreground = namespace["raw_foreground"]

    sl = z_score.sink_to_list()
    geometry.emit(geo)
    for s in [raw_background_dark, raw_background, raw_foreground_dark]:
        s.emit(np.zeros(img.shape))
    raw_foreground.emit(img)
    del namespace
    destroy_pipeline(raw_foreground)
    assert len(sl) == 1
    sl.clear()
