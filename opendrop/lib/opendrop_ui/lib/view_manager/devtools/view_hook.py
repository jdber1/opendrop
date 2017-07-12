import sys, os, inspect
import functools
import pprint

def log(*args):
    if len(args) == 1:
        args = args[0]

    msg = args

    if not isinstance(args, str):
        msg = pprint.pformat(args)

    # TODO: Turn this logging into a class with colour chooser for [header]
    print("\033[95m[view_hook]\033[0m {}".format(msg))

def pretty_args(*args, **kwargs):
    out = ""

    out += ",".join(pprint.pformat(arg) for arg in args)

    if kwargs:
        out += ","
        out += ",".join("{0}={1}".format(k, repr(v)) for k, v in kwargs)

    return out

def import_by_filename(filename):
    if sys.version_info >= (3,5):
        util = __import__("importlib.util")

        spec = util.spec_from_file_location("", filename)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module
    elif sys.version_info >= (3,3):
        SourceFileLoader = __import__("importlib.machinery").SourceFileLoader

        module = SourceFileLoader("", file_name).load_module()

        return module
    elif sys.version_info >= (2,):
        imp = __import__("imp")

        module = imp.load_source("", filename)

        return module
    else:
        sys.exit("Python 2.0 or newer is required for 'import_by_filename'.")

class ViewEventsHook(object):
    def __init__(self, view_manager):
        self.current_view = None

        view_manager.events.view_change.bind(self.view_change)

    def view_change(self, new_view):
        if new_view:
            self.current_view = new_view

            new_view.events._any.bind(functools.partial(self.events_hook, "events"))
            new_view.core_events._any.bind(functools.partial(self.events_hook, "core_events"))

    def events_hook(self, prefix, event_name, *args, **kwargs):
        view_name = self.current_view.__class__.__name__

        # TODO: Fix up this pretty print formatting
        pargs = pretty_args(*args, **kwargs)
        if "\n" in pargs:
            pargs = "\n" + pargs
            pargs = "\n".join("    " + line for line in pargs.split("\n"))
            pargs+= "\n"

        log("{view_name}.{prefix}.{event_name}({args})".format(
            prefix=prefix,
            view_name=view_name,
            event_name=event_name,
            args=pargs
        ))

def view_hook(view_manager):
    ViewEventsHook(view_manager)

    log("Hooked initialised")

    return view_manager

#
# class ShowViewController(Controller):
#     @bind
#     def show_view(self, reply, view):
#         vm = self.view_manager
#
#         view = vm.set_view(view)
#
# def main(*args):
#     filename = args[0]
#     view_class_name = None
#
#     if len(args) == 1:
#         view_class_name = os.path.basename(os.path.splitext(filename)[0])
#     else:
#         view_class_name = args[1]
#
#     view = getattr(import_by_filename(filename), view_class_name)
#
#
#     model = Model()
#     view_manager = ViewManager()
#     controller = hook(ShowViewController(model = model, view_manager = view_manager))
#
#     model.do_async("show_view", view)
#
#     view_manager.mainloop()
#
# if __name__ == '__main__':
#     # Dont include the script name as the first argument
#     main(*sys.argv[1:])
