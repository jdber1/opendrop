from gi.repository import Gdk

from opendrop.mvp.event_container import MouseMoveEvent, ModifierType

MODIFIER_TYPE_FROM_GDK_MODIFIER_TYPE = {
    Gdk.ModifierType.SHIFT_MASK: ModifierType.SHIFT,
    Gdk.ModifierType.LOCK_MASK: ModifierType.CAPSLOCK,
    Gdk.ModifierType.CONTROL_MASK: ModifierType.CONTROL,
    Gdk.ModifierType.MOD1_MASK: ModifierType.ALT,
    Gdk.ModifierType.BUTTON1_MASK: ModifierType.BUTTON1,
    Gdk.ModifierType.BUTTON2_MASK: ModifierType.BUTTON2,
    Gdk.ModifierType.BUTTON3_MASK: ModifierType.BUTTON3
}


def mouse_move_event_from_event_motion(gdk_event: Gdk.EventMotion) -> MouseMoveEvent:
    state = 0

    for k, v in MODIFIER_TYPE_FROM_GDK_MODIFIER_TYPE.items():
        if gdk_event.state & k == k:
            state |= v

    return MouseMoveEvent(
        timestamp=gdk_event.time,
        pos=(gdk_event.x, gdk_event.y),
        state=state
    )
