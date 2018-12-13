from unittest.mock import Mock

import pytest

from opendrop.utility.speaker import Speaker, Moderator


class MySpeaker(Speaker):
    LOG_ACTIVATE = object()
    LOG_DEACTIVATE = object()
    LOG_REQUEST_DEACTIVATE = object()

    def __init__(self):
        Speaker.__init__(self)

        # Used for testing.
        self.log = []

    def do_activate(self):
        self.log.append(self.LOG_ACTIVATE)

    def do_deactivate(self):
        self.log.append(self.LOG_DEACTIVATE)

    async def do_request_deactivate(self):
        self.log.append(self.LOG_REQUEST_DEACTIVATE)


class MyBlockingSpeaker(MySpeaker):
    LOG_BLOCK_DEACTIVATION_REQUEST = object()

    async def do_request_deactivate(self):
        self.log.append(self.LOG_BLOCK_DEACTIVATION_REQUEST)
        return True


# Tests start here

def test_speaker_moderator_value_after_instantiate():
    my_spk = MySpeaker()

    assert my_spk.moderator is None


def test_speaker_moderator_readonly():
    my_spk = MySpeaker()

    with pytest.raises(AttributeError):
        my_spk.moderator = 1


def test_moderator_active_speaker_value_after_instantiate():
    mod = Moderator()

    assert mod.active_speaker is None
    assert mod.bn_active_speaker.get() is None


def test_moderator_active_speaker_readonly():
    mod = Moderator()

    with pytest.raises(ValueError):
        mod.active_speaker = 1
    with pytest.raises(ValueError):
        mod.bn_active_speaker.set(1)


def test_moderator_add_speaker():
    mod = Moderator()
    my_spk = MySpeaker()

    # Add the speaker
    mod.add_speaker(0, my_spk)
    assert my_spk.log == []
    assert my_spk.moderator == mod


def test_moderator_add_speaker_with_key_none():
    mod = Moderator()
    my_spk = MySpeaker()

    with pytest.raises(ValueError):
        mod.add_speaker(None, my_spk)


@pytest.mark.asyncio
async def test_moderator_activate_speaker():
    mod = Moderator()
    my_spk = MySpeaker()
    mod.add_speaker(0, my_spk)
    cb = Mock()
    mod.bn_active_speaker.on_changed.connect(cb, immediate=True)

    # Activate the speaker
    success = await mod.activate_speaker(0)

    assert success
    assert my_spk.log == [MySpeaker.LOG_ACTIVATE]
    cb.assert_called_once_with()
    assert mod.active_speaker == 0
    assert mod.bn_active_speaker.get() == 0


@pytest.mark.asyncio
async def test_moderator_activate_nonexistent_speaker():
    mod = Moderator()

    with pytest.raises(ValueError):
        await mod.activate_speaker(0)


@pytest.mark.asyncio
async def test_moderator_deactivate_active_speaker():
    mod = Moderator()
    my_spk = MySpeaker()
    mod.add_speaker(0, my_spk)
    await mod.activate_speaker(0)
    cb = Mock()
    mod.bn_active_speaker.on_changed.connect(cb, immediate=True)

    # Deactivate the current active speaker
    await mod.activate_speaker(None)

    assert my_spk.log == [MySpeaker.LOG_ACTIVATE, MySpeaker.LOG_REQUEST_DEACTIVATE, MySpeaker.LOG_DEACTIVATE]
    cb.assert_called_once_with()
    assert mod.active_speaker is None
    assert mod.bn_active_speaker.get() is None


@pytest.mark.asyncio
async def test_moderator_activate_speaker_but_current_active_speaker_blocks():
    mod = Moderator()
    my_blocking_spk = MyBlockingSpeaker()
    my_spk = MySpeaker()
    mod.add_speaker(0, my_blocking_spk)
    mod.add_speaker(1, my_spk)

    # Activate the blocking speaker
    await mod.activate_speaker(0)

    cb = Mock()
    mod.bn_active_speaker.on_changed.connect(cb, immediate=True)

    # Try to activate another speaker
    success = await mod.activate_speaker(0)

    assert success is False
    assert my_blocking_spk.log == [MyBlockingSpeaker.LOG_ACTIVATE, MyBlockingSpeaker.LOG_BLOCK_DEACTIVATION_REQUEST]
    assert my_spk.log == []
    cb.assert_not_called()
    assert mod.active_speaker == 0
    assert mod.bn_active_speaker.get() == 0


@pytest.mark.asyncio
async def test_moderator_activate_speaker_with_force():
    mod = Moderator()
    my_blocking_spk = MyBlockingSpeaker()
    my_spk = MySpeaker()
    mod.add_speaker(0, my_blocking_spk)
    mod.add_speaker(1, my_spk)

    # Activate the blocking speaker
    await mod.activate_speaker(0)

    cb = Mock()
    mod.bn_active_speaker.on_changed.connect(cb, immediate=True)

    # Try to activate another speaker
    success = await mod.activate_speaker(1, force=True)

    assert success
    assert my_blocking_spk.log == [MyBlockingSpeaker.LOG_ACTIVATE, MyBlockingSpeaker.LOG_DEACTIVATE]
    assert my_spk.log == [MySpeaker.LOG_ACTIVATE]
    cb.assert_called_once_with()
    assert mod.active_speaker == 1
    assert mod.bn_active_speaker.get() == 1
