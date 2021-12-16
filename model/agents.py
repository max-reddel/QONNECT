"""
This module contains all agent classes.
"""

from mesa import Agent
from model.preferences import *
from model.components import *
import math


class GenericAgent(Agent):
    """
    This agent is a generic agent. A lot of other agents are probably inherting attributes and methods from it:
        - Dismantler
        - Refiner
        - PostShredder
        - PartsManufacturer
        - OEM
        - LogisticCompany
        - Garages
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

        # Stock of specific materials
        self.stock = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: [],
            Component.CARS: []
        }

        # Demand of specific materials
        self.demand = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: 0,
            Component.CARS: 0
        }

        # Prices for specific materials
        self.prices = {
            Component.VIRGIN: math.inf,
            Component.RECYCLATE_LOW: math.inf,
            Component.RECYCLATE_HIGH: math.inf,
            Component.PARTS: math.inf,
            Component.CARS: math.inf
        }

        # Minimum constraints given by law or car designers
        self.constraints = {
            PartState.REUSED: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0
        }

        # Stock goals of specific materials
        self.stock_goals = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: 0,
            Component.CARS: 0
        }

    def step(self):
        """
        Step method: buy components, manufacture other components, adjust demand for next round.
        """
        self.buy_all_components()
        self.manufacture_goods()
        self.update_demand()

    def buy_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        pass

    def get_sorted_supplier_list(self, suppliers, component):
        """
        Determine a list that is sorted by the priority of the suppliers for a specific component.
        :param suppliers: list of Agents
        :param component: Component
        :return:
            suppliers_sorted: list of sorted Agents
        """
        preferences = Preferences(agent=self, suppliers=suppliers).data
        row = preferences.loc[component, :]
        series = row.sort_values(ascending=True)
        suppliers_sorted = list(series.index)

        return suppliers_sorted

    def buy_one_component_from_suppliers(self, suppliers, component):
        """
        Go through the suppliers and try to buy a specific component.
        :param suppliers: list of Agents
        :param component: Component that this agent demands
        """
        rest_demand = self.demand[component]

        while suppliers and rest_demand > 0:
            supplier = suppliers[0]
            stock_of_supplier = supplier.get_stock()[component]

            # print(f'rest_demand: {rest_demand}')
            if self.sufficient_stock(rest_demand, stock_of_supplier):
                supplier.provide(recepient=self, component=component, amount=rest_demand)
            else:
                # demand is either float or int
                # stock is either float or lists
                rest_stock = self.get_rest_stock(stock_of_supplier)
                # print(f'rest_stock: {rest_stock}')
                supplier.provide(recepient=self, component=component, amount=rest_stock)
            suppliers = suppliers[1:]

    def get_rest_stock(self, stock_of_supplier):
        """
        Compute the rest stock
        :param stock_of_supplier: float or list
        :return:
            float or int
        """
        if isinstance(stock_of_supplier, float):
            return stock_of_supplier
        elif isinstance(stock_of_supplier, list):
            return len(stock_of_supplier)

    def provide(self, recepient, component, amount):
        """
        This method provides a specific amount of a specific component to a specific buyer.
        :param recepient: Agent
        :param component: Component
        :param amount: float/int
        """
        # print(f'agent: {self}')
        if isinstance(self.stock[component], float):
            self.stock[component] -= amount
            recepient.receive(component=component, amount=amount)
        elif isinstance(amount, list):
            # TODO: Never goes in here
            print('elif')

            # Get the supplies
            amount = len(amount)
            supplies = self.stock[component][:amount]
            # Remove supplies from the stock
            self.stock[component] = self.stock[component][amount:]
            # Give supplis to the recepient
            recepient.receive(component=component, amount=amount, supplies=supplies)
        else:
            print('else')

    def receive(self, component, amount, supplies=None):
        """
        Agent receives a specific amount of a specific component
        :param component: Component
        :param amount: float/int
        """
        # TODO: Continue here, use supplies with an if statement. Test this + provide()
        if isinstance(self.stock[component], float):
            self.stock[component] += amount
        elif isinstance(self.stock[component], list):
            self.stock[component].append(supplies)

    def get_stock(self):
        """
        Getter for stock
        :return:
            self.stock: dictionary with {Component: float}
        """
        return self.stock

    def get_prices(self):
        """
        Getter for prices.
        :return:
            self.prices: dictionary with {Component: float}
        """
        return self.prices

    def manufacture_goods(self):
        """
        Manufacture specific amount of goods (either parts or cars).
        """
        # TODO: Implement this while using some kind of combination of plastics under specific constraints.
        pass

    def update_demand(self):
        """
        Update own demand for next round. E.g., see how much this agent had to supply versus how much stock there was.
        """
        pass

    @staticmethod
    def sufficient_stock(rest_demand, stock_of_supplier):
        """
        Check whether there is enough stock to cover the demand.
        Take into account different data types of input parameters.
        :param rest_demand: float/int
        :param stock_of_supplier: float/set
        :return:
            truth: Boolean: True when there is enough stock to cover demand.
        """
        truth = False
        if isinstance(stock_of_supplier, float):
            truth = rest_demand <= stock_of_supplier
        elif isinstance(stock_of_supplier, list):
            truth = rest_demand <= len(stock_of_supplier)
        return truth


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
            Component.VIRGIN: self.random.normalvariate(2.0, 0.2),
            Component.RECYCLATE_LOW: self.random.normalvariate(2.0, 0.2),
            Component.RECYCLATE_HIGH: self.random.normalvariate(3.0, 0.1)}

        # self.stock_goals[Component.PARTS] = 100
        self.stock[Component.PARTS] = [Part() for _ in range(100)]

    def buy_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers
        self.refiners = self.all_agents[Refiner]
        self.post_shredders = self.all_agents[PostShredder]

        refiners = self.get_sorted_supplier_list(suppliers=self.refiners, component=Component.VIRGIN)
        self.buy_one_component_from_suppliers(suppliers=refiners, component=Component.VIRGIN)

        post_shredders_low = self.get_sorted_supplier_list(suppliers=self.post_shredders, component=Component.RECYCLATE_LOW)
        self.buy_one_component_from_suppliers(suppliers=post_shredders_low, component=Component.RECYCLATE_LOW)

        post_shredders_high = self.get_sorted_supplier_list(suppliers=self.post_shredders, component=Component.RECYCLATE_HIGH)
        self.buy_one_component_from_suppliers(suppliers=post_shredders_high, component=Component.RECYCLATE_HIGH)


class Refiner(GenericAgent):

    def __init__(self, unique_id, model, all_agents):
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.VIRGIN] = self.random.normalvariate(10.0, 2)
        self.prices[Component.VIRGIN] = self.random.normalvariate(2.5, 0.2)  # cost per unit

    def step(self):
        """
        Step method.
        """
        pass


class PostShredder(GenericAgent):
    """
    PostShredder and Postshredder agent.
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: PlasticModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.RECYCLATE_LOW] = self.random.normalvariate(10.0, 2)
        self.stock[Component.RECYCLATE_HIGH] = self.random.normalvariate(10.0, 2)

        self.prices[Component.RECYCLATE_LOW] = self.random.normalvariate(2.5, 0.2)  # cost per unit
        self.prices[Component.RECYCLATE_HIGH] = self.random.normalvariate(2.5, 0.2)  # cost per unit

    def step(self):
        """
        Step method.
        """


class CarManufacturer(GenericAgent):
    """
    CarManufcaturer agent.
    """

    def __init__(self, unique_id, model, all_agents, brand):
        """
        :param unique_id: int
        :param model: PlasticModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.brand = brand

        self.stock[Component.PARTS] = [Part() for _ in range(100)]
        self.stock[Component.CARS] = [Car(Brand.MERCEDES) for _ in range(10)]

        self.prices[Component.PARTS] = self.random.normalvariate(2.5, 0.2)  # cost per unit
        self.prices[Component.CARS] = self.random.normalvariate(1000.0, 0.2)  # cost per unit

        self.demand[Component.PARTS] = round(self.random.normalvariate(100.0, 2))

    def buy_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers
        self.parts_manufacturers = self.all_agents[PartsManufacturer]
        parts_manufacturers = self.get_sorted_supplier_list(suppliers=self.parts_manufacturers, component=Component.PARTS)
        self.buy_one_component_from_suppliers(suppliers=parts_manufacturers, component=Component.PARTS)

    def manufacture_goods(self):
        """
        Manufacture specific amount of cars.
        """
        # TODO: Implement this while using some kind of combination of plastics under specific constraints.
        pass


class FakeUser(GenericAgent):
    """
    FakeUser agent.
    """

    def __init__(self, unique_id, model, all_agents):
        """
         :param unique_id: int
         :param model: PlasticModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.CARS] = 0
        self.demand[Component.CARS] = 1

    def buy_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        print(f'fake buyer')
        self.car_manufacturers = self.all_agents[CarManufacturer]
        car_manufacturers = self.get_sorted_supplier_list(suppliers=self.car_manufacturers, component=Component.CARS)
        self.buy_one_component_from_suppliers(suppliers=car_manufacturers, component=Component.CARS)
