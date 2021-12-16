from enum import Enum


class CarState(Enum):
    """
    State of a car
    """
    BROKEN = 0
    FUNCTIONING = 1


class Material(Enum):
    """
    Kinds of plastics.
    """
    REUSE = 0
    VIRGIN = 1
    RECYCLATE_LOW = 2
    RECYCLATE_HIGH = 3
    CAR = 4
