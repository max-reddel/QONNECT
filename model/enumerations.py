from enum import Enum


class Component(Enum):
    """
    Kinds of plastics.
    """
    VIRGIN = 1
    RECYCLATE_LOW = 2
    RECYCLATE_HIGH = 3
    PARTS = 4
    CARS = 5


class PartState(Enum):
    """
    Kinds of parts.
    """
    STANDARD = 1
    REUSED = 2


class CarState(Enum):
    """
    State of a car.
    """
    BROKEN = 0
    FUNCTIONING = 1


class Brand(Enum):
    """
    Kinds of car brands.
    """
    VW = 0
    GM = 1
    TOYOTA = 2
    MERCEDES = 3
