"""
This module contains the Preferences class.
"""

# from queue import PriorityQueue  # Inteded to be used during agent.satisfy_preferences()
import pandas as pd
from model.enumerations import *


class Preferences:
    """
    This class describes the preferences of a single agent at an instant.
    """

    def __init__(self, agent, suppliers):
        """
        :param agent: Agent
        :param suppliers: list of Agents
        """
        self.agent = agent
        self.suppliers = suppliers
        self.indices = [x for x in PlasticType]

        self.data = pd.DataFrame(columns=self.suppliers, index=self.indices)
        for supplier in self.suppliers:
            self.data[supplier] = self.compute_priorities_for_one_supplier(supplier)

    def compute_priorities_for_one_supplier(self, supplier):
        """
        Compute all priority values for a supplier.
        :param supplier: GenericAgent: an agent that supplies the current agent with material.
        :return:
            supplier_priorities: Pandas Series: represents a column in a dataframe
        """
        # TODO: actual priority values need to be elaborated on to include other decision variables
        # TODO: current implementation is limited to price only

        supplier_priorities = pd.Series(index=self.indices)

        prices = supplier.get_prices()
        materials = list(prices.keys())

        for material in materials:
            supplier_priorities[material] = prices[material]

        return supplier_priorities
