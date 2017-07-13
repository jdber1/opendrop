from collections import namedtuple
import json

import threading

from opendrop import VERSION
from opendrop.conf import PREFERENCES_FILENAME
from opendrop.resources import resources

from opendrop.constants import OperationMode

from opendrop.utility import coroutines

from opendrop.utility.vectors import Vector2, BBox2
# DEBUG
from opendrop.opendrop_ui.view_manager.devtools.view_hook import view_hook

from opendrop.opendrop_ui.view_manager import ViewManager

from opendrop.opendrop_ui import views

OPENDROP_OP_REQUIREMENTS = {
    OperationMode.PENDANT: {
        "regions": 1,
    },
    OperationMode.SESSILE: {
        "regions": 1,
    },
    OperationMode.CONAN: {
        "regions": 2,
    },
    OperationMode.CONAN_NEEDLE: {
        "regions": 2,
    },
}

def make_preferences(form_data):

    # TODO: Convert form_data to pref

    pref = form_data

    return pref

def save_preferences(pref):
    with open(PREFERENCES_FILENAME, "w") as pref_file:
        json.dump(pref, pref_file, indent = 4)

def load_preferences():
    try:
        with open(PREFERENCES_FILENAME, "r") as pref_file:
            pref = json.load(pref_file)

            return pref
    except IOError:
        return None

def parse_preferences(pref):
    # TODO: Convert pref to form_data

    form_data = pref

    return form_data

@coroutines.co
def select_regions(context, num_regions, image_source_desc, image_source_type):
    view_manager = context["view_manager"]

    regions = []

    for i in range(num_regions):
        view = yield view_manager.set_view(views.SelectRegion,
            image_source_desc=image_source_desc,
            image_source_type=image_source_type
        )

        response = yield view.events.submit

        if response:
            regions.append(response)
        else:
            regions = None
            yield None
            yield coroutines.EXIT

    yield regions

@coroutines.co
def select_threshold(context, image_source_desc, image_source_type):
    view_manager = context["view_manager"]

    # view = yield view_manager.set_view(views.SelectThreshold,
    #     image_source_desc=image_source_desc,
    #     image_source_type=image_source_type
    # )
    #
    # threshold_val = yield view.events.submit
    #
    # yield threshold_val

    yield 40


# Main UI flow

@coroutines.co
def entry(context):
    #yield test(context)
    yield main_menu(context)

@coroutines.co
def test(context):
    view = yield context["view_manager"].set_view(views.SelectRegion, image_source_desc = 0, image_source_type = "USB camera")
    yield view.events.blah

@coroutines.co
def main_menu(context):
    view = yield context["view_manager"].set_view(views.MainMenu)

    operation_mode = yield view.events.submit

    context["operation_mode"] = operation_mode

    yield user_input(context)

@coroutines.co
def user_input(context):
    view = yield context["view_manager"].set_view(views.OpendropUserInput)

    # TODO: handle if preferences are corrupted

    pref = load_preferences()
    pref_form = parse_preferences(pref)

    view.restore_form(pref_form)

    response_form = yield view.events.submit

    if response_form is None:
        yield main_menu(context)
        yield coroutines.EXIT

    pref = make_preferences(response_form)
    save_preferences(pref)

    num_regions = OPENDROP_OP_REQUIREMENTS[context["operation_mode"]]["regions"]

    image_source_desc = response_form["image_acquisition"]["image_source"]
    image_source_type = response_form["image_acquisition"]["image_source_type"]

    threshold_val = yield select_threshold(context, image_source_desc=image_source_desc,
                                           image_source_type=image_source_type)

    if threshold_val is None:
        yield user_input(context)
        yield coroutines.EXIT

    regions = yield select_regions(context,
        num_regions,
        image_source_desc=image_source_desc,
        image_source_type=image_source_type
    )

    if regions is None:
        yield user_input(context)
        yield coroutines.EXIT

# End of UI

def main():
    view_manager = view_hook(ViewManager(default_title="Opendrop {}".format(VERSION)))

    context = {"view_manager": view_manager}

    def exit(code):
        print("Exit with {}".format(code))
        view_manager.exit()

    entry(context).bind(exit)

    view_manager.mainloop()

if __name__ == '__main__':
    main()
