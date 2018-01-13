from gi.repository import Gdk

from opendrop.gtk_specific.shims import mouse_move_event_from_event_motion
from opendrop.mvp.event_container import ModifierType


def test_mouse_move_event_from_event_motion():
    gdk_event = Gdk.EventMotion()

    gdk_event.time = 123
    gdk_event.x = 9
    gdk_event.y = 34

    gdk_event.state = Gdk.ModifierType.SHIFT_MASK \
                      | Gdk.ModifierType.BUTTON2_MASK \
                      | Gdk.ModifierType.CONTROL_MASK \
                      | 0b10000000000000000  # random unknown flag

    event = mouse_move_event_from_event_motion(gdk_event)

    print(event.state, (ModifierType.SHIFT | ModifierType.BUTTON2 | ModifierType.CONTROL))

    assert event.timestamp == gdk_event.time and \
           event.pos == (gdk_event.x, gdk_event.y) and \
           event.state == (ModifierType.SHIFT | ModifierType.BUTTON2 | ModifierType.CONTROL)
