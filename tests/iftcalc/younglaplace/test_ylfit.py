import asyncio
from unittest.mock import patch

import numpy as np
import pytest

from opendrop.iftcalc.younglaplace.yl_fit import YoungLaplaceFit
from tests.iftcalc.dataset.water_in_air001 import data as water_in_air001_data

EPSILON = 0.01

all_drop_data = [water_in_air001_data]


def _get_drop_data_by_drop_contour_annotation(contour):
    for drop_data in all_drop_data:
        if (contour == drop_data.drop_contour_annotation).all():
            return drop_data
    else:
        raise ValueError('could not find drop data for this contour')


def _is_profile_correct(for_this_drop_contour, actual_profile_eval):
    drop_data = _get_drop_data_by_drop_contour_annotation(for_this_drop_contour)

    expected_profile_domain = drop_data.profile_data[:, 0]
    expected_profile = drop_data.profile_data[:, 1:]
    actual_profile = actual_profile_eval(expected_profile_domain)

    # Assert that the calculated profile is close enough to expected.
    return abs(expected_profile - actual_profile).max() < EPSILON


def _is_params_correct(input_contour, actual_params):
    drop_data = _get_drop_data_by_drop_contour_annotation(input_contour)
    expected_params = drop_data.params
    return abs(np.array(expected_params) - actual_params).max() < EPSILON


@pytest.fixture(params=[water_in_air001_data.drop_contour_annotation])
def yl_fit_just_initialised(request):
    drop_contour = request.param
    yl_fit = YoungLaplaceFit(drop_contour)
    return yl_fit, drop_contour


@pytest.mark.asyncio
async def test_yl_fit_normal_usage(yl_fit_just_initialised):
    yl_fit, contour = yl_fit_just_initialised

    with patch.object(yl_fit, 'on_params_changed'):
        assert yl_fit.status is YoungLaplaceFit.Status.INITIALISED

        optimise_task = asyncio.get_event_loop().create_task(yl_fit.optimise())

        await asyncio.sleep(0)
        assert yl_fit.status is YoungLaplaceFit.Status.FITTING

        await optimise_task
        assert yl_fit.status is YoungLaplaceFit.Status.FINISHED

        # Assert that a stop flag exists.
        assert yl_fit.stop_flags != 0

        # Assert that the calculated parameters are close enough to expected.
        assert _is_params_correct(contour, yl_fit.params)
        # Assert that the calculated profile is correct.
        assert _is_profile_correct(contour, yl_fit.profile)

        # Just make sure on_params_changed was fired a few times.
        assert yl_fit.on_params_changed.fire.call_count > 1


@pytest.mark.asyncio
async def test_yl_fit_cancel(yl_fit_just_initialised):
    yl_fit, _ = yl_fit_just_initialised

    optimise_task = asyncio.get_event_loop().create_task(yl_fit.optimise())

    # Wait for the parameters to change twice
    for _ in range(2):
        await asyncio.wait_for(yl_fit.on_params_changed.wait(), 0.1)
    # and then cancel at this arbitrary point in time.
    yl_fit.cancel()

    await optimise_task

    # Assert that yl_fit was cancelled.
    assert yl_fit.stop_flags == YoungLaplaceFit.StopFlag.CANCELLED
