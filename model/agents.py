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

        # Minimum constraints given by law or car designers
        self.constraints = {
            Material.REUSE: 0.0,
            Material.VIRGIN: 0.0,
            Material.RECYCLATE_LOW: 0.0,
            Material.RECYCLATE_HIGH: 0.0}

        # Prices for specific materials
        self.prices = {
            Material.REUSE: math.inf,
            Material.VIRGIN: math.inf,
            Material.RECYCLATE_LOW: math.inf,
            Material.RECYCLATE_HIGH: math.inf}

        # Stock of specific materials
        self.stock = {
            Material.REUSE: 0.0,
            Material.VIRGIN: 0.0,
            Material.RECYCLATE_LOW: 0.0,
            Material.RECYCLATE_HIGH: 0.0}

        # Demand of specific materials
        self.demand = {
            Material.REUSE: 0.0,
            Material.VIRGIN: 0.0,
            Material.RECYCLATE_LOW: 0.0,
            Material.RECYCLATE_HIGH: 0.0}

    def get_prices(self):
        """
        Getter for prices.
        :return:
            self.prices: dictionary with {Material: float}
        """
        return self.prices

    def update_suppliers(self):
        pass

    def initialize_transaction(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        pass

    def finalize_transaction(self):
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
            Material.REUSE: 0,
            Material.VIRGIN: self.random.normalvariate(10.0, 2),
            Material.RECYCLATE_LOW: self.random.normalvariate(2.0, 0.2),
            Material.RECYCLATE_HIGH: self.random.normalvariate(8.0, 2)}

    def initialize_transaction(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        suppliers = self.all_agents[MinerRefiner] + self.all_agents[Shredder]
        self.preferences = Preferences(agent=self, suppliers=suppliers)
        self.update_suppliers(suppliers)

    def finalize_transaction(self):
        """
        Second stage of the agent step: satisfy agent's preferences as far as possible.
        """
        pass

    def update_suppliers(self, suppliers):

        # for s in suppliers:
        #     s.
        pass


class MinerRefiner(GenericAgent):

    def __init__(self, unique_id, model, all_agents):
        super().__init__(unique_id, model, all_agents)

        self.stock[Material.VIRGIN] = self.random.normalvariate(10.0, 2)
        self.prices[Material.VIRGIN] = self.random.normalvariate(2.5, 0.2)  # cost per unit

    def initialize_transaction(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        pass

    def finalize_transaction(self):
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

        self.stock[Material.RECYCLATE_LOW] = self.random.normalvariate(10.0, 2)
        self.stock[Material.RECYCLATE_HIGH] = self.random.normalvariate(10.0, 2)

        self.prices[Material.RECYCLATE_LOW] = self.random.normalvariate(2.5, 0.2)  # cost per unit
        self.prices[Material.RECYCLATE_HIGH] = self.random.normalvariate(2.5, 0.2)  # cost per unit

    def initialize_transaction(self):
        """
        First stage of the agent step: compute agent's preferences.
        """
        pass

    def finalize_transaction(self):
        """
        Second stage of the agent step: satisfy agent's preferences as far as possible.
        """
        pass
