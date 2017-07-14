from copy import copy

class ArgFilter(object):
    def __init__(self, default, permissions, exclusives):
        self.default = default

        self.permissions = permissions

        self.exclusives = exclusives

        # Just to make that all exclusives have permissions equal to True
        assert(all(permissions[k] == True for k in exclusives))


    def filter(self, kwargs):
        new_kwargs = {}

        for k, v in kwargs.items():
            if (k in self.permissions and self.permissions[k]) or \
               (k not in self.permissions and self.default):
                new_kwargs[k] = v

        return new_kwargs

class Exclusive(object):
    def __init__(self, name):
        self.name = name

def customlist(default, permissions):
    exclusives = set()

    for k, v in list(permissions.items()):
        if isinstance(k, Exclusive):
            exclusives.add(k.name)

            # Remove the Exclusive() wrapper
            del permissions[k]
            permissions[k.name] = v

    return ArgFilter(default, permissions, exclusives)

def blacklist(*keywords):
    default = True
    permissions = {arg_name: True for arg_name in keywords}

    return customlist(default, permissions)

def whitelist(*keywords):
    default = False
    permissions = {k: True for k in keywords}

    return customlist(default, permissions)

def multikwarg(**arg_filters):
    all_exclusives = set()

    for arg_filter in arg_filters.values():
        all_exclusives = all_exclusives.union(arg_filter.exclusives)

    for arg_filter in arg_filters.values():
        permissions_underlay = {k: False for k in all_exclusives}
        permissions_underlay.update(arg_filter.permissions)

        arg_filter.permissions = permissions_underlay

    def decorator(function):
        def wrapper(*args, **kwargs):
            multikwargs = copy(kwargs)

            for group_name, arg_filter in arg_filters.items():
                multikwargs[group_name] = arg_filter.filter(kwargs)

            return function(args[0], **multikwargs)

        return wrapper

    return decorator
