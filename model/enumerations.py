from enum import Enum
from random import normalvariate, choice


class Component(Enum):
    """
    Kinds of plastics.
    """
    VIRGIN = 1
    RECYCLATE_LOW = 2
    RECYCLATE_HIGH = 3
    PARTS = 4
    PARTS_FOR_RECYCLER = 5
    CARS = 6
    CARS_FOR_RECYCLER = 7
    CARS_FOR_DISMANTLER = 8

    def get_random_price(self):
        """
        Sample the price for a component.
        :return:
            price: float
        """
        price = 1.0

        if self == Component.VIRGIN or self == Component.RECYCLATE_LOW or self == Component.RECYCLATE_HIGH:
            price = normalvariate(mu=2.5, sigma=0.2)
        elif self == Component.PARTS:
            price = normalvariate(mu=10.0, sigma=2.0)
        elif self == Component.CARS:
            price = normalvariate(mu=100.0, sigma=5.0)

        return price


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

    @staticmethod
    def get_random():
        """
        Returns a random brand.
        :return: brand: Brand
        """
        brands = [brand for brand in Brand]
        brand = choice(brands)
        return brand
