"""
This module contains the Car and Part class.
A car consists of parts.
Parts consist of different kinds of plastic.
"""

from model.enumerations import *


class Car:
    """
    The Car class.
    TODO: This is just a start. This needs to be elaborated on.
    """

    def __init__(self, brand):

        self.life_time_current = 0
        self.ELV = 10 # So basically we could multiply this with a use intensity of the user to update it.
        self.state = CarState.FUNCTIONING
        self.brand = brand
        self.parts = []

    def repair_car(self, part):
        self.state = CarState.FUNCTIONING
        self.parts = self.parts[1:]
        self.parts.append(part)

    def increment_lifetime(self):
        self.life_time_current += 1

class Part:
    """
    A part conists of three different kinds of plastic.
    """

    def __init__(self, plastic_ratio=None, state=PartState.STANDARD):

        if plastic_ratio is None:
            self.plastic_ratio = {
                Component.VIRGIN: 0.0,
                Component.RECYCLATE_LOW: 0.0,
                Component.RECYCLATE_HIGH: 0.0
            }
        else:
            self.plastic_ratio = plastic_ratio

        self.state = state

    def reuse(self):
        """
        Switch the state of the part form NEW to REUSED.
        """
        self.state = PartState.REUSED

    def extract_plastic(self):
        """
        Extract materials from part and return them.
        :return:
            plastic_ratio: dictionary with {Component: float}
        """
        plastic_ratio = self.plastic_ratio.copy()

        self.plastic_ratio = {x: 0.0 for x in self.plastic_ratio}

        return plastic_ratio
