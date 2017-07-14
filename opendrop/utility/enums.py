from collections import namedtuple

class EnumValue(object):
    def __init__(self, typename, name):
        self._typename = typename
        self._name = name

    def __repr__(self):
        return ".".join((self._typename, self._name))

def enum(*values, **opts):
    if "typename" in opts:
        typename = opts["typename"]
    else:
        typename = "Enum"

    return namedtuple(typename, values)(*(EnumValue(typename, value) for value in values))
