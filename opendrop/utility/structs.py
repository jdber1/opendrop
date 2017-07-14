from six.moves import zip_longest

class Struct(object):
    """
    Basic struct implementation for python, example:

        class MyStruct(Struct):
            attributes = (
                'Attr1',
                'Attr2',
                'Attr3'
            )

            default = 0

        my_struct = MyStruct(1, 2, 3)
        my_struct2 = MyStruct(1, 2)
        my_other_struct = MyStruct(Attr1 = 1, Attr2 = 2, Attr3 = 3)
        my_other_struct2 = MyStruct(Attr1 = 1, Attr3 = 3)

    Structs can be instantiated either by positional arguments or by keyword, but not both.
    If 'default' is defined in the class definition, arguments to __init__ can be ommited and will
    take on the value of 'default'. Default values on a per attribute basis is not implemented.
    """
    def __init__(self, *args, **kwargs):
        default_all = (bool(args) or bool(kwargs)) == False
        if not default_all and bool(args) and bool(kwargs):
            raise ValueError(
                "Can't mix positional and keyword arguments to instantiate struct"
            )

        if args or default_all:
            if not hasattr(self, 'default') and len(args) != len(self.attributes):
                raise ValueError(
                    "Length of arguments passed do not match number of attributes in struct"
                )

            for attr, val in zip_longest(self.attributes, args,
                                         fillvalue = getattr(self, "default", None)):
                super(Struct, self).__setattr__(attr, val)
        elif kwargs:
            if not hasattr(self, 'default') and len(kwargs) != len(self.attributes):
                raise ValueError(
                    "Number of arguments passed do not match number of attributes in struct"
                )
            elif not all(key in self.attributes for key in kwargs.keys()):
                for key in kwargs.keys():
                    if key not in self.attributes:
                        raise ValueError(
                            "Keyword arguments contain extraneuous attribute '{}'".format(key)
                        )

            for attr in self.attributes:
                try:
                    super(Struct, self).__setattr__(attr, kwargs[attr])
                except KeyError:
                    super(Struct, self).__setattr__(attr, self.default)

    def __repr__(self):
        repr_dict = {}

        for name in self.attributes:
            repr_dict[name] = getattr(self, name)

        return self.__class__.__name__ + "({})".format(repr(repr_dict))
