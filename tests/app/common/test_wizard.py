from unittest.mock import Mock, call

import pytest

from opendrop.component.wizard.wizard import WizardPositionView, WizardPositionPresenter, WizardPageID
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.speaker import Moderator


class MockWizardPageID(WizardPageID):
    MOCK0 = ('Mock 0',)
    MOCK1 = ('Mock 1',)
    MOCK2 = ('Mock 2',)


class MockWizardPositionView(WizardPositionView):
    LOG_BN_ACTIVE_KEY_SET = 'LOG_BN_ACTIVE_KEY_SET'
    LOG_CLEAR = 'LOG_CLEAR'
    LOG_ADD_KEY = 'LOG_ADD_KEY'

    def __init__(self):
        self.bn_active_key = AtomicBindableAdapter(setter=self._bn_active_key_setter)
        # Used for testing.
        self.log = Mock()

    def _bn_active_key_setter(self, value):
        self.log.bn_active_key_setter(value)

    def add_key(self, key):
        self.log.add_key(key)

    def clear(self):
        self.log.clear()


def test_wizard_position_presenter_clears_and_adds_keys():
    wizard_pos_view = MockWizardPositionView()

    presenter = WizardPositionPresenter(Mock(), [
        MockWizardPageID.MOCK0,
        MockWizardPageID.MOCK2,
        MockWizardPageID.MOCK1
    ], wizard_pos_view)

    wizard_pos_view.log.assert_has_calls([
        call.clear(),
        call.add_key(MockWizardPageID.MOCK0),
        call.add_key(MockWizardPageID.MOCK2),
        call.add_key(MockWizardPageID.MOCK1)
    ])


@pytest.mark.asyncio
async def test_wizard_position_presenter_propagates_active_key():
    wizard_mod = Moderator()
    wizard_mod.add_speaker(MockWizardPageID.MOCK0, Mock())
    wizard_mod.add_speaker(MockWizardPageID.MOCK1, Mock())
    wizard_mod.add_speaker(MockWizardPageID.MOCK2, Mock())

    wizard_pos_view = MockWizardPositionView()

    presenter = WizardPositionPresenter(wizard_mod, [
        MockWizardPageID.MOCK0,
        MockWizardPageID.MOCK2,
        MockWizardPageID.MOCK1
    ], wizard_pos_view)

    # Clear the logs.
    wizard_pos_view.log.reset_mock()

    await wizard_mod.activate_speaker_by_key(MockWizardPageID.MOCK1)

    assert wizard_pos_view.log.method_calls == [call.bn_active_key_setter(MockWizardPageID.MOCK1)]


@pytest.mark.asyncio
async def test_wizard_position_presenter_syncs_active_key():
    wizard_mod = Moderator()
    wizard_mod.add_speaker(MockWizardPageID.MOCK0, Mock())
    wizard_mod.add_speaker(MockWizardPageID.MOCK1, Mock())
    wizard_mod.add_speaker(MockWizardPageID.MOCK2, Mock())

    wizard_pos_view = MockWizardPositionView()

    await wizard_mod.activate_speaker_by_key(MockWizardPageID.MOCK2)

    presenter = WizardPositionPresenter(wizard_mod, [
        MockWizardPageID.MOCK0,
        MockWizardPageID.MOCK2,
        MockWizardPageID.MOCK1
    ], wizard_pos_view)

    wizard_pos_view.log.assert_has_calls([call.bn_active_key_setter(MockWizardPageID.MOCK2)])


@pytest.mark.asyncio
async def test_wizard_position_destroy():
    wizard_mod = Moderator()
    wizard_mod.add_speaker(MockWizardPageID.MOCK0, Mock())
    wizard_mod.add_speaker(MockWizardPageID.MOCK1, Mock())
    wizard_mod.add_speaker(MockWizardPageID.MOCK2, Mock())

    wizard_pos_view = MockWizardPositionView()

    presenter = WizardPositionPresenter(wizard_mod, [
        MockWizardPageID.MOCK0,
        MockWizardPageID.MOCK2,
        MockWizardPageID.MOCK1
    ], wizard_pos_view)

    # Clear the logs.
    wizard_pos_view.log.reset_mock()

    presenter.destroy()

    # Activate another speaker after the presenter is destroyed.
    await wizard_mod.activate_speaker_by_key(MockWizardPageID.MOCK0)

    wizard_pos_view.log.assert_not_called()
