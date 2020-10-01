import enum
from typing import Callable, Any

import attr
from toolz import merge


class AutoNumberEnum(enum.Enum):
    def __new__(cls, *args):
        print(args)
        value = len(cls.__members__) + 1
        obj = cls.__new__(cls)
        obj._value_ = value
        return obj


class EnumMixin(enum.Enum):
    """Transforms the enum __init__ arg to kwargs for the class in the mro

    The enum input is given as a tuple, but we usually want to pass kwargs for complicated classes.

    Recommended usage::

        @enum.unique
        class RepoIndex(EnumMixin, AutoNumberEnum):
            ...

    - Place the EnumMixin first in the base classes so its __init__ gets
      called first.
    - Place the class that will get the kwargs in its __init__ next.

    """

    def __init__(self, kwargs):
        super().__init__(**kwargs)


class Name(str):
    """If used in a namespace like below,

    ::
        @make_namespace
        class NS:
            x = AutoName()


    """

    pass


def make_namespace(cls):
    for k, v in cls.__dict__.items():
        if v == Name() and isinstance(v, Name):
            setattr(cls, k, k)

    return cls


def auto_names(cls):
    """
    Fill in the names of attributes using the variable name.

    :return: class with renamed values
    """
    for k, v in cls.__dict__.items():
        if isinstance(getattr(v, "name", None), Name) and v.name == Name():
            setattr(cls, k, attr.evolve(v, name=k))

    return cls
