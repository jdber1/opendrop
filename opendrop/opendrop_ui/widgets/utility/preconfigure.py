import inspect

from collections import defaultdict

class PreconfiguredWidgetModule(object):
    def __init__(self, contents, preconfig):
        self._contents = {}

        for name, v in contents.items():
            subpreconfig = preconfig[name]

            if inspect.isclass(v):
                self._contents[name] = preconfigure_widget(v, subpreconfig)
            elif inspect.ismodule(v):
                self._contents[name] = v.preconfigure(subpreconfig)

    def __getattr__(self, name):
        try:
            return self._contents[name]
        except:
            raise AttributeError(
                "'PreconfiguredWidgetModule' object has no attribute '{}'".format(name)
            )

class Preconfig(object):
    def __init__(self, data, defaults = {}):
        data = data.copy()
        defaults = defaults.copy()

        self.children = {}

        self.defaults = defaults

        if all(isinstance(v, dict) for v in data.values()):
            # Data only contains values that are dicts, therefore treat it as a submodule preconfig
            # declaration
            if "*" in data:
                self.defaults.update(data["*"])
                del data["*"]

            self.children.update({
                k: Preconfig(v, defaults = self.defaults) for k, v in data.items()
            })
        else:
            # Preconfig declaration for a widget
            self.defaults.update(data)

    def __getitem__(self, name):
        if name in self.children:
            return self.children[name]
        else:
            return Preconfig({}, defaults = self.defaults)

    def __repr__(self):
        return "Preconfig(defaults={})".format(repr(self.defaults))

    def mix(self, kwargs):
        new_kwargs = self.defaults.copy()
        new_kwargs.update(kwargs)

        return new_kwargs

def preconfigure_widget(widget, preconfig):
    class PreconfiguredWidget(widget):
        def __init__(self, *args, **kwargs):
            widget.__init__(self, *args, **preconfig.mix(kwargs))

    return PreconfiguredWidget

def preconfigure(contents, preconfig):
    if not isinstance(preconfig, Preconfig):
        try:
            preconfig = Preconfig(preconfig)
        except:
            raise

    return PreconfiguredWidgetModule(contents, preconfig)
