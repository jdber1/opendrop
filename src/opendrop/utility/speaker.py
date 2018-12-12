from typing import Generic, TypeVar, Optional, MutableMapping, Callable, List


K = TypeVar('K')


class Speaker(Generic[K]):
    def __init__(self) -> None:
        self._moderator = None  # type: Optional[Moderator[K]]

    def do_activate(self) -> None:
        """Invoked when this Speaker is to be activated."""

    def do_deactivate(self) -> None:
        """Invoked when this Speaker is to be deactivated."""

    async def do_request_deactivate(self) -> bool:
        """This method is a coroutine. This method is invoked when the Moderator is asking for permission from this
        Speaker to deactivate, return True to prevent this Speaker from deactivating and False to approve the
        deactivation request. After approving the deactivation request, this Speaker will be deactivated, and the
        deactivate() method will be invoked. Default implementation returns True"""
        return False

    @property
    def moderator(self) -> 'Optional[Moderator[K]]':
        return self._moderator


class Moderator(Generic[K]):
    def __init__(self) -> None:
        self._active_speaker = None  # type: Optional[K]
        self._key_to_speakers = {}  # type: MutableMapping[K, Speaker]

    @property
    def active_speaker(self) -> Optional[K]:
        """Return the key that identifies the currently active Speaker, return None if no Speaker is currently active.
        """
        return self._active_speaker

    def add_speaker(self, key: K, spk: Speaker) -> None:
        if key is None:
            raise ValueError('Identifying key cannot be None')

        self._key_to_speakers[key] = spk
        spk._moderator = self

    def _handle_speaker_request_activate_speaker(self, src_key: K, activate_key: K) -> None:
        if self.active_speaker is not src_key:
            return

        self.activate_speaker(activate_key)

    async def _deactivate_active_speaker(self, force: bool) -> bool:
        """Deactivate the currently active Speaker (if it exists), returns True if successful and False otherwise. This
        method will not update the `_active_speaker` attribute."""
        if self._active_speaker is None:
            return True

        # The 'actual' active speaker, not the key used to identify it
        active_speaker = self._key_to_speakers[self._active_speaker]

        block = False if force else await active_speaker.do_request_deactivate()

        if block:
            return False

        active_speaker.do_deactivate()
        return True

    async def activate_speaker(self, key: Optional[K], force: bool = False) -> bool:
        """Activate the speaker identified by key, return True if desired speaker is successfully activated, and False
        otherwise. Pass force=True to force any currently active speaker to be deactivated, preventing it from blocking
        the deactivation. To deactivate the current active speaker only, without activating another speaker, use
        key=None."""
        if key is not None and key not in self._key_to_speakers:
            raise ValueError('No speaker identified by `{}`'.format(key))

        deactivation_success = await self._deactivate_active_speaker(force)

        if not deactivation_success:
            return False

        if key is not None:
            desired_speaker = self._key_to_speakers[key]
            desired_speaker.do_activate()

        self._active_speaker = key
        return True
