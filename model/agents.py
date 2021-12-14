"""
This module contains all agent classes.
"""

from mesa import Agent
from model.preferences import *
import math


class GenericAgent(Agent):
    """
    This agent is a generic agent. A lot of other agents are probably inherting attributes and methods from it:
        - Dismantler
        - MinerRefiner
        - Shredder
        - PartsManufacturer
        - OEM
        - LogisticCompany
        - Garages
    TODO: Should CarManufacturers follow this style as well or would they need to be modeled differently?
    TODO: Other agents such as User, ARN, and CarDesigner should follow a different structure.
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: PlasticModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model)
        self.all_agents = all_agents
        self.unique_name = f'{self.__class__.__name__}_{unique_id}'  # This is optional

        # Percentual constraints given by law or car designers
        self.constraints = {
            PlasticType.VIRGIN: 0.7,
            PlasticType.REUSE: 0.0,
            PlasticType.RECYCLATE_LOW: 0.1,
            PlasticType.RECYCLATE_HIGH: 0.2}

        # Prices for specific plastic types
        self.prices = {
            PlasticType.REUSE: math.inf,
            PlasticType.VIRGIN: math.inf,
            PlasticType.RECYCLATE_LOW: math.inf,
            PlasticType.RECYCLATE_HIGH: math.inf}

        # Stock of specific plastic types
        self.stock = {
            PlasticType.REUSE: 0.0,
            PlasticType.VIRGIN: 0.0,
            PlasticType.RECYCLATE_LOW: 0.0,
            PlasticType.RECYCLATE_HIGH: 0.0}

    def get_prices(self):
        """
        Getter for prices.
        :return:
            self.prices: dictionary with {PlasticType: float}
        """
        return self.prices

    def offer_preferences(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        pass

    def satisfy_preferences(self):
        """
        Second stage of the agent step: satisfy agent's preferences as far as possible.
        """
        pass


class PartsManufacturer(GenericAgent):
    """
    PartsManfucturer agent.
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: PlasticModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)
        self.demand = {
            PlasticType.VIRGIN: self.random.normalvariate(10.0, 2),
            PlasticType.RECYCLATE_LOW: self.random.normalvariate(2.0, 0.2),
            PlasticType.RECYCLATE_HIGH: self.random.normalvariate(8.0, 2)}

    def offer_preferences(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        suppliers = self.all_agents[MinerRefiner] + self.all_agents[Shredder]
        self.preferences = Preferences(agent=self, suppliers=suppliers)

    def satisfy_preferences(self):
        """
        Second stage of the agent step: satisfy agent's preferences as far as possible.
        """
        pass


class MinerRefiner(GenericAgent):

    def __init__(self, unique_id, model, all_agents):
        super().__init__(unique_id, model, all_agents)

        self.stock[PlasticType.VIRGIN] = self.random.normalvariate(10.0, 2)
        self.prices[PlasticType.VIRGIN] = self.random.normalvariate(2.5, 0.2)  # cost per unit

    def offer_preferences(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        pass

    def satisfy_preferences(self):
        """
        Second stage of the agent step: satisfy agent's preferences as far as possible.
        """
        pass


class Shredder(GenericAgent):
    """
    Shredder and Postshredder agent.
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: PlasticModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.stock[PlasticType.RECYCLATE_LOW] = self.random.normalvariate(10.0, 2)
        self.stock[PlasticType.RECYCLATE_HIGH] = self.random.normalvariate(10.0, 2)

        self.prices[PlasticType.RECYCLATE_LOW] = self.random.normalvariate(2.5, 0.2)  # cost per unit
        self.prices[PlasticType.RECYCLATE_HIGH] = self.random.normalvariate(2.5, 0.2)  # cost per unit

    def offer_preferences(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        pass

    def satisfy_preferences(self):
        """
        Second stage of the agent step: satisfy agent's preferences as far as possible.
        """
        pass
