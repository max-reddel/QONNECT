"""
This module contains the CAR class.
"""

from model.enumerations import *


class Car:
    """
    The CAR class.
    TODO: This is just a start. This needs to be elaborated on.
    """

    def __init__(self):

        self.life_time_current = 0
        self.state = CarState.FUNCTIONING
