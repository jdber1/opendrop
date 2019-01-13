import asyncio
import math
from unittest.mock import Mock

import numpy as np
import pytest
from scipy import interpolate
from scipy.spatial import distance

from opendrop.app.ift.analysis_model.analyser import IFTDropAnalysis, IFTImageAnnotations, IFTPhysicalParameters
from opendrop.iftcalc.younglaplace.yl_fit import YoungLaplaceFit
from opendrop.mytypes import Rect2
from opendrop.utility.events import Event
from tests.iftcalc.dataset.water_in_air001 import data as water_in_air001_data


# Helper functions/classes

class NumpyEqualsAll:
    def __init__(self, target):
        self._target = target

    def __eq__(self, other):
        if not isinstance(other, np.ndarray):
            return False

        return (self._target == other).all()


# Fixtures

class MockYoungLaplaceFit:
    def __init__(self, data, loop):
        self.params = data.params
        self.profile = interpolate.CubicSpline(x=data.profile_data[:, 0], y=data.profile_data[:, 1:])
        self.profile_domain = data.profile_data[:, 0].max()

        self.stop_flags = 0
        self.on_params_changed = Event()

        # Mock methods:
        self.optimise = Mock(return_value=loop.create_future())
        self.cancel = Mock()

        # Mock attributes
        self.objective = Mock()
        self.residuals = Mock()

    @property
    def apex_x(self):
        return self.params[0]

    @property
    def apex_y(self):
        return self.params[1]

    @property
    def apex_radius(self):
        return self.params[2]

    @property
    def bond_number(self):
        return self.params[3]

    @property
    def apex_rot(self):
        return self.params[4]

    @property
    def _apex_rot_matrix(self):
        angle = self.apex_rot
        return np.array([[math.cos(angle), -math.sin(angle)],
                         [math.sin(angle),  math.cos(angle)]])

    def rz_from_xy(self, x, y):
        return self._apex_rot_matrix @ [x, y]

    def xy_from_rz(self, r, z):
        return self._apex_rot_matrix.T @ [r, z]


@pytest.fixture(params=[
    water_in_air001_data])
def mock_yl_fit_and_drop_data(request, event_loop):
    return MockYoungLaplaceFit(request.param, event_loop), request.param


@pytest.fixture
def phys_params():
    return IFTPhysicalParameters(1000, 0, 0.7176, 9.8)


@pytest.fixture
def image_and_annotations():
    image = Mock()
    image_timestamp = 321
    annotations = IFTImageAnnotations(
        m_per_px=1.234,
        drop_region_px=Rect2(x=150, y=250, w=350, h=450),
        needle_region_px=Rect2(x=100, y=200, w=300, h=400),
        drop_contour_px=np.random.rand(10, 2),
        needle_contours_px=(np.random.rand(10, 2), np.random.rand(10, 2)))
    return image, image_timestamp, annotations


class DropAnalysisJustInitialisedContext:
    def __init__(self, *, drop_analysis, phys_params, mock_yl_fit_factory, calculate_ift, calculate_volume,
                 calculate_surface_area, calculate_worthington):
        self.drop_analysis = drop_analysis
        self.phys_params = phys_params
        self.mock_yl_fit_factory = mock_yl_fit_factory
        self.calculate_ift = calculate_ift
        self.calculate_volume = calculate_volume
        self.calculate_surface_area = calculate_surface_area
        self.calculate_worthington = calculate_worthington


@pytest.fixture
def drop_analysis_just_initialised(phys_params: IFTPhysicalParameters) -> DropAnalysisJustInitialisedContext:
    mock_yl_fit_factory = Mock()

    calculate_ift = Mock()
    calculate_volume = Mock()
    calculate_surface_area = Mock()
    calculate_worthington = Mock()

    drop_analysis = IFTDropAnalysis(
        phys_params=phys_params,
        create_yl_fit=mock_yl_fit_factory,
        calculate_ift=calculate_ift,
        calculate_volume=calculate_volume,
        calculate_surface_area=calculate_surface_area,
        calculate_worthington=calculate_worthington)

    return DropAnalysisJustInitialisedContext(
        drop_analysis=drop_analysis,
        phys_params=phys_params,
        mock_yl_fit_factory=mock_yl_fit_factory,
        calculate_ift=calculate_ift,
        calculate_volume=calculate_volume,
        calculate_surface_area=calculate_surface_area,
        calculate_worthington=calculate_worthington)


class DropAnalysisReadyToFitContext(DropAnalysisJustInitialisedContext):
    pass


@pytest.fixture
def drop_analysis_ready_to_fit(drop_analysis_just_initialised: DropAnalysisJustInitialisedContext,
                               image_and_annotations) -> DropAnalysisReadyToFitContext:
    drop_analysis = drop_analysis_just_initialised.drop_analysis
    drop_analysis._give_image(*image_and_annotations)

    return DropAnalysisReadyToFitContext(**drop_analysis_just_initialised.__dict__)


class DropAnalysisFittingContext(DropAnalysisReadyToFitContext):
    def __init__(self, *, mock_yl_fit, drop_data, **kwargs):
        super().__init__(**kwargs)
        self.mock_yl_fit = mock_yl_fit
        self.drop_data = drop_data


@pytest.fixture
async def drop_analysis_fitting(drop_analysis_ready_to_fit: DropAnalysisReadyToFitContext, mock_yl_fit_and_drop_data,
                                event_loop) -> DropAnalysisFittingContext:
    mock_yl_fit, drop_data = mock_yl_fit_and_drop_data
    mock_yl_fit_factory = drop_analysis_ready_to_fit.mock_yl_fit_factory
    mock_yl_fit_factory.return_value = mock_yl_fit

    drop_analysis = drop_analysis_ready_to_fit.drop_analysis

    # Start the fit
    event_loop.create_task(drop_analysis._start_fit())

    # Wait for status to change to FITTING
    await asyncio.wait_for(drop_analysis.bn_status.on_changed.wait(), 0.1)

    return DropAnalysisFittingContext(mock_yl_fit=mock_yl_fit, drop_data=drop_data,
                                      **drop_analysis_ready_to_fit.__dict__)


# Tests

class TestDropAnalysisJustInitialised:
    @pytest.fixture(autouse=True)
    def fixture(self, drop_analysis_just_initialised: DropAnalysisJustInitialisedContext):
        self.drop_analysis = drop_analysis_just_initialised.drop_analysis

    def test_initial_status(self):
        drop_analysis = self.drop_analysis
        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.WAITING_FOR_IMAGE

    @pytest.mark.asyncio
    async def test_give_image(self, image_and_annotations):
        drop_analysis = self.drop_analysis
        image, image_timestamp, image_annotations = image_and_annotations

        wait_for_these = asyncio.gather(
            drop_analysis.bn_status.on_changed.wait(),
            drop_analysis.bn_image.on_changed.wait(),
            drop_analysis.bn_image_timestamp.on_changed.wait(),
            drop_analysis.bn_image_annotations.on_changed.wait())

        drop_analysis._give_image(image, image_timestamp, image_annotations)

        await asyncio.wait_for(wait_for_these, 0.1)

        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.READY_TO_FIT
        assert drop_analysis.bn_image.get() == image
        assert drop_analysis.bn_image_timestamp.get() == image_timestamp
        assert drop_analysis.bn_image_annotations.get() == image_annotations

    def test_cancel(self):
        drop_analysis = self.drop_analysis
        drop_analysis.cancel()
        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.CANCELLED

    def test_cancel_and_then_give_image(self, image_and_annotations):
        drop_analysis = self.drop_analysis
        drop_analysis.cancel()

        # Can't give image after cancelled.
        with pytest.raises(ValueError):
            drop_analysis._give_image(*image_and_annotations)

    @pytest.mark.asyncio
    async def test_start_fit_before_giving_image(self):
        drop_analysis = self.drop_analysis

        # Can't start fit before image and image annotations are given.
        with pytest.raises(ValueError):
            await drop_analysis._start_fit()


class TestDropAnalysisReadyToFit:
    @pytest.fixture(autouse=True)
    def fixture(self, drop_analysis_ready_to_fit: DropAnalysisReadyToFitContext):
        ctx = drop_analysis_ready_to_fit

        self.drop_analysis = ctx.drop_analysis
        self.phys_params = ctx.phys_params
        self.mock_yl_fit_factory = ctx.mock_yl_fit_factory

    @pytest.mark.asyncio
    async def test_start_fit(self, event_loop):
        # Extract out the objects we need
        drop_analysis = self.drop_analysis
        mock_yl_fit_factory = self.mock_yl_fit_factory

        # Create a mock YoungLaplaceFit to be returned by mock_yl_fit_factory
        mock_yl_fit = Mock()
        mock_yl_fit.on_params_changed = Event()
        mock_yl_fit.optimise.return_value = event_loop.create_future()

        mock_yl_fit_factory.return_value = mock_yl_fit

        # Start the fit
        event_loop.create_task(drop_analysis._start_fit())

        # Wait until status is FITTING
        await asyncio.wait_for(drop_analysis.bn_status.on_changed.wait(), 0.1)
        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.FITTING

        # Validate mock_yl_fit_factory call arguments

        # Contour passed to YoungLaplaceFit should have y-coordinates that increase in the opposite direction to
        # gravity.
        image_annotations = drop_analysis.bn_image_annotations.get()
        expected_contour = image_annotations.drop_contour_px.copy()
        expected_contour[:, 1] *= -1
        expected_contour[:, 1] += image_annotations.drop_region_px.h

        mock_yl_fit_factory.assert_called_once_with(NumpyEqualsAll(expected_contour), drop_analysis.log)

        # Assert mock_yl_fit.optimise() was called.
        mock_yl_fit.optimise.assert_called_once_with()


class TestDropAnalysisFitting:
    @pytest.fixture(autouse=True)
    def fixture(self, drop_analysis_fitting: DropAnalysisFittingContext):
        ctx = drop_analysis_fitting

        self.drop_analysis = ctx.drop_analysis

        self.phys_params = ctx.phys_params

        self.calculate_ift = ctx.calculate_ift
        self.calculate_volume = ctx.calculate_volume
        self.calculate_surface_area = ctx.calculate_surface_area
        self.calculate_worthington = ctx.calculate_worthington

        self.mock_yl_fit = ctx.mock_yl_fit
        self.drop_data = ctx.drop_data

    @pytest.mark.asyncio
    async def test_fit_normal_finish(self):
        # Extract out the objects we need
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        # Finish the fit
        mock_yl_fit.optimise.return_value.set_result(None)

        # Wait until status is FINISHED
        await asyncio.wait_for(drop_analysis.bn_status.on_changed.wait(), 0.1)
        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.FINISHED

    @pytest.mark.asyncio
    async def test_fit_exception(self):
        # Extract out the objects we need
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        # Set stop flags to UNEXPECTED_EXCEPTION
        mock_yl_fit.stop_flags = YoungLaplaceFit.StopFlag.UNEXPECTED_EXCEPTION

        # Finish the fit
        mock_yl_fit.optimise.return_value.set_result(None)

        # Wait until status is UNEXPECTED_EXCEPTION
        await asyncio.wait_for(drop_analysis.bn_status.on_changed.wait(), 0.1)
        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.UNEXPECTED_EXCEPTION

    @pytest.mark.asyncio
    async def test_fit_cancelled(self):
        # Extract out the objects we need
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        # Set stop flags to CANCELLED
        mock_yl_fit.stop_flags = YoungLaplaceFit.StopFlag.CANCELLED

        # Finish the fit
        mock_yl_fit.optimise.return_value.set_result(None)

        # Wait until status is CANCELLED
        await asyncio.wait_for(drop_analysis.bn_status.on_changed.wait(), 0.1)
        assert drop_analysis.bn_status.get() is IFTDropAnalysis.Status.CANCELLED

    def test_cancel_while_fitting(self):
        # Extract out the objects we need
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        drop_analysis.cancel()
        mock_yl_fit.cancel.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_fit_params_changed(self):
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        wait_for_these = asyncio.gather(
            drop_analysis.bn_objective.on_changed.wait(),
            drop_analysis.bn_bond_number.on_changed.wait(),
            drop_analysis.bn_interfacial_tension.on_changed.wait(),
            drop_analysis.bn_volume.on_changed.wait(),
            drop_analysis.bn_surface_area.on_changed.wait(),
            drop_analysis.bn_worthington.on_changed.wait(),
            drop_analysis.bn_apex_pos_px.on_changed.wait(),
            drop_analysis.bn_apex_rot.on_changed.wait(),
            drop_analysis.bn_apex_radius.on_changed.wait(),
            drop_analysis.bn_drop_contour_fit.on_changed.wait(),
            drop_analysis.bn_drop_contour_fit_residuals.on_changed.wait())

        mock_yl_fit.on_params_changed.fire()

        # Make sure that the relevant bindables have their on_changed events fire.
        await asyncio.wait_for(wait_for_these, 0.1)

    @pytest.mark.parametrize('samples', [
        100, 150
    ])
    def test_generate_drop_contour_fit(self, samples):
        drop_analysis = self.drop_analysis
        drop_data = self.drop_data

        drop_contour_fit = drop_analysis.generate_drop_contour_fit(samples).astype(int)
        expected_drop_contour_fit  = drop_data.drop_contour_fit

        # Assert that the actual contour fit is close enough to the expected contour fit.
        max_dist = 5  # 5 pixels
        assert distance.cdist(drop_contour_fit, expected_drop_contour_fit).min(axis=1).max() <= max_dist

        # Assert that the number of contour points returned equals the number of samples requested.
        assert len(drop_contour_fit) == samples

    def test_objective(self):
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        assert drop_analysis.bn_objective.get() == mock_yl_fit.objective

    def test_bond_number(self):
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        assert drop_analysis.bn_bond_number.get() == mock_yl_fit.bond_number

    def test_apex_pos_px(self):
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        mock_yl_fit_apex_pos_px = mock_yl_fit.apex_x, mock_yl_fit.apex_y

        # Calculate expected_apex_pos_px
        image_annotations = drop_analysis.bn_image_annotations.get()
        drop_region_px = image_annotations.drop_region_px
        expected_apex_pos_px = (int(mock_yl_fit_apex_pos_px[0]), int(drop_region_px.h - mock_yl_fit_apex_pos_px[1]))
        expected_apex_pos_px = expected_apex_pos_px[0] + drop_region_px.x, expected_apex_pos_px[1] + drop_region_px.y

        apex_pos_px = drop_analysis.bn_apex_pos_px.get()

        assert tuple(apex_pos_px) == expected_apex_pos_px

    def test_interfacial_tension(self):
        drop_analysis = self.drop_analysis
        phys_params = self.phys_params
        calculate_ift = self.calculate_ift

        calculate_ift.reset_mock()
        assert drop_analysis.bn_interfacial_tension.get() == calculate_ift.return_value
        calculate_ift.assert_called_once_with(
            phys_params.inner_density,
            phys_params.outer_density,
            drop_analysis.bn_bond_number.get(),
            drop_analysis.bn_apex_radius.get(),
            phys_params.gravity)

    def test_volume(self):
        drop_analysis = self.drop_analysis
        calculate_volume = self.calculate_volume
        mock_yl_fit = self.mock_yl_fit

        calculate_volume.reset_mock()
        assert drop_analysis.bn_volume.get() == calculate_volume.return_value
        calculate_volume.assert_called_once_with(
            mock_yl_fit.profile_domain,
            drop_analysis.bn_bond_number.get(),
            drop_analysis.bn_apex_radius.get())

    def test_surface_area(self):
        drop_analysis = self.drop_analysis
        calculate_surface_area = self.calculate_surface_area
        mock_yl_fit = self.mock_yl_fit

        calculate_surface_area.reset_mock()
        assert drop_analysis.bn_surface_area.get() == calculate_surface_area.return_value
        calculate_surface_area.assert_called_once_with(
            mock_yl_fit.profile_domain,
            drop_analysis.bn_bond_number.get(),
            drop_analysis.bn_apex_radius.get())

    def test_worthington(self):
        drop_analysis = self.drop_analysis
        phys_params = self.phys_params
        calculate_worthington = self.calculate_worthington

        calculate_worthington.reset_mock()
        assert drop_analysis.bn_worthington.get() == calculate_worthington.return_value
        calculate_worthington.assert_called_once_with(
            phys_params.inner_density,
            phys_params.outer_density,
            phys_params.gravity,
            drop_analysis.bn_interfacial_tension.get(),
            drop_analysis.bn_volume.get(),
            phys_params.needle_width)

    def test_drop_contour_fit(self):
        drop_analysis = self.drop_analysis
        assert (drop_analysis.bn_drop_contour_fit.get() == drop_analysis.generate_drop_contour_fit()).all()

    def test_drop_contour_fit_residuals(self):
        drop_analysis = self.drop_analysis
        mock_yl_fit = self.mock_yl_fit

        assert drop_analysis.bn_drop_contour_fit_residuals.get() == mock_yl_fit.residuals
