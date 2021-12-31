"""
This module contains the Car and Part class.
A car consists of parts.
Parts consist of different kinds of plastic.
"""

from model.enumerations import *
import random


class Part:
    """
    A part conists of three different kinds of plastic.
    """

    def __init__(self, plastic_ratio=None, state=PartState.STANDARD):

        self.minimum_requirements = {
            Component.RECYCLATE_LOW: 0.2,
            Component.RECYCLATE_HIGH: 0.2}

        if plastic_ratio is None:
            self.plastic_ratio = {
                Component.VIRGIN: 0,
                Component.RECYCLATE_LOW: random.uniform(
                    self.minimum_requirements[Component.RECYCLATE_LOW],
                    self.minimum_requirements[Component.RECYCLATE_LOW] * 1.25),
                Component.RECYCLATE_HIGH: random.uniform(
                    self.minimum_requirements[Component.RECYCLATE_HIGH],
                    self.minimum_requirements[Component.RECYCLATE_HIGH] * 1.25)
            }
            # Adjust virgin plastic weight such that the sum of all plastic will be 1.0
            self.plastic_ratio[Component.VIRGIN] = 1.0 - sum(self.plastic_ratio.values())
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


class Car:
    """
    The Car class.
    """

    def __init__(self, brand, lifetime_current=0, state=CarState.FUNCTIONING,
                 parts=None, nr_of_parts=4, break_down_probability=0.1):
        # Apply parameters, if none specified then it will be a new car. Otherwise, randomly old car.
        if parts is None:
            parts = [Part() for _ in range(nr_of_parts)]

        self.lifetime_current = lifetime_current
        self.ELV = 10
        self.state = state
        self.brand = brand
        self.parts = parts
        self.break_down_probability = break_down_probability

    def repair_car(self, part):  # Garage calls this function.
        """
        A new part is always added at the end of the list, such that it takes the longest time to break down again. A
        part that has been reused is placed at a random place in the parts list.
        """

        if part.state == PartState.REUSED:
            part_index = random.randint(0, len(self.parts)-1)

            for i in range(part_index):
                self.parts[i] = self.parts[i+1]

            self.parts[part_index] = part

        else:
            self.parts = self.parts[1:]
            self.parts.append(part)

        self.state = CarState.FUNCTIONING

    def increment_lifetime(self):
        """
        A car is only being used when it is functioning.
        """
        if self.state == CarState.FUNCTIONING:
            self.lifetime_current += 1

    def to_break_down(self):
        """
        A car can break down when it is functioning. It may also have reached its end of life.
        """
        if self.lifetime_current >= self.ELV:
            self.state = CarState.END_OF_LIFE

        elif random.random() < self.break_down_probability and self.state == CarState.FUNCTIONING:
            self.state = CarState.BROKEN

    def use_car(self):  # User calls this function.
        self.to_break_down()
        self.increment_lifetime()
