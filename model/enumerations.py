from enum import Enum


class Component(Enum):
    """
    Kinds of plastics.
    """
    VIRGIN = 1
    RECYCLATE_LOW = 2
    RECYCLATE_HIGH = 3
    PARTS = 4
    DISCARDED_PARTS = 5
    CARS = 6
    CARS_FOR_SHREDDER = 7
    CARS_FOR_DISMANTLER = 8


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
    END_OF_LIFE = 2


class Brand(Enum):
    """
    Kinds of car brands. We can rename them and/or change how many we want.
    """
    VW = 0
    GM = 1
    TOYOTA = 2
    MERCEDES = 3
