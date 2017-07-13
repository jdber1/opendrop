import importlib

def load(settings):
    globs = {}

    for name in settings.widgets:
        if name[-1] == ".":
            name = name[:-1]

            submodule = importlib.import_module(".." + name, settings.__name__)
            globs[name] = submodule
        else:
            widget = getattr(importlib.import_module(".." + name, settings.__name__), name)
            globs[name] = widget

    return globs
