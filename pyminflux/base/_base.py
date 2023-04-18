#  Copyright (c) 2022 - 2023 D-BSSE, ETH Zurich. All rights reserved.


class Singleton(type):
    """Metaclass to implement the singleton pattern for classes."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
