"""
This module contains the Preferences class.
"""

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
        self.indices = [x for x in Component]

        self.data = pd.DataFrame(columns=self.suppliers, index=self.indices)
        for supplier in self.suppliers:
            self.data[supplier] = self.compute_priorities_for_one_supplier(supplier)

    def compute_priorities_for_one_supplier(self, supplier):
        """
        Compute all priority values for a supplier.
        Remarks:
            - current implementation is limited to price only
            - actual priority values need to be elaborated on to include other decision variables
        :param supplier: Agent: an agent that supplies the current agent with material.
        :return:
            supplier_priorities: Pandas Series: represents a column in a dataframe
        """

        supplier_priorities = pd.Series(index=self.indices)
        prices = supplier.get_prices()
        components = list(prices.keys())
        for component in components:
            supplier_priorities[component] = prices[component]

        return supplier_priorities
