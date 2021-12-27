"""
This module contains all agent classes.
"""

from mesa import Agent
from model.preferences import *
from model.bigger_components import *
import math


class GenericAgent(Agent):
    """
    This agent is a generic agent. Its descendants are:
        - Refiner
        - Recycler
        - PartsManufacturer/OEM
        - CarManufacturer
        - Garage
        - Dismantler
        - User
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model)
        self.all_agents = all_agents

        # Stock of specific components
        self.stock = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: [],
            Component.CARS: []
        }

        # Demand of specific components
        self.demand = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: 0,
            Component.CARS: 0
        }

        # Default Demand of specific components
        self.default_demand = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: 0,
            Component.CARS: 0
        }

        # Prices for specific components
        self.prices = {
            Component.VIRGIN: math.inf,
            Component.RECYCLATE_LOW: math.inf,
            Component.RECYCLATE_HIGH: math.inf,
            Component.PARTS: math.inf,
            Component.CARS: math.inf
        }

        # Stock goals of specific components (how much does an agent want to have in their own stock at each instant)
        self.stock_goals = {
            Component.VIRGIN: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: 0,
            Component.CARS: 0
        }

        # Minimum requirements given by law or car designers
        self.minimum_requirements = {
            PartState.REUSED: 0.0,
            Component.RECYCLATE_LOW: 0.0,
            Component.RECYCLATE_HIGH: 0.0
        }

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        pass

    def get_sorted_suppliers(self, suppliers, component):
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

    def get_component_from_suppliers(self, suppliers, component):
        """
        Go through the suppliers and try to buy a specific component.
        :param suppliers: list of Agents
        :param component: Component that this agent demands
        """
        rest_demand = self.demand[component]

        while suppliers and rest_demand > 0.0:
            supplier = suppliers[0]
            stock_of_supplier = supplier.get_stock()[component]

            if self.sufficient_stock(rest_demand, stock_of_supplier):
                supplier.provide(recepient=self, component=component, amount=rest_demand)
                self.reduce_current_demand(supplies=rest_demand, component=component)
            else:
                rest_stock = self.get_rest_stock(stock_of_supplier)
                supplier.provide(recepient=self, component=component, amount=rest_stock)
                self.reduce_current_demand(supplies=rest_stock, component=component)

            # Adjust remaining demand and supplier list
            rest_demand = self.demand[component]
            suppliers = suppliers[1:]

    def reduce_current_demand(self, supplies, component):
        """
        After receiving components, the current demand should be reduced accordingly.
        :return:
        """
        self.demand[component] -= supplies

    @staticmethod
    def get_rest_stock(stock_of_supplier):
        """
        Compute the rest stock
        :param stock_of_supplier: float or list
        :return:
            float or int
        """
        if isinstance(stock_of_supplier, float) or isinstance(stock_of_supplier, int):
            return stock_of_supplier
        elif isinstance(stock_of_supplier, list):
            return len(stock_of_supplier)

    def provide(self, recepient, component, amount):
        """
        This method provides a specific amount of a specific component to a specific buyer.
        :param recepient: Agent
        :param component: Component
        :param amount: float or int
        """
        if isinstance(self.stock[component], float) or isinstance(self.stock[component], int):
            self.stock[component] -= amount
            recepient.receive(component=component, amount=amount)
        elif isinstance(self.stock[component], list):
            # Get the supplies
            supplies = self.stock[component][:amount]
            # Remove supplies from the stock
            self.stock[component] = self.stock[component][amount:]
            # Give supplis to the recepient
            recepient.receive(component=component, amount=amount, supplies=supplies)

    def receive(self, component, amount, supplies=None):
        """
        Agent receives a specific amount of a specific component
        :param component: Component
        :param amount: float or int
        :param supplies: Car or Part
        """
        if isinstance(self.stock[component], float) or isinstance(self.stock[component], int):
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

    def process_components(self):
        """
        Process goods (manufactuging, shredding, using, or repairing).
        """
        # TODO: Implement this while using some kind of combination of plastics under specific constraints.
        pass

    def update_demand(self):
        """
        Update own demand for next round. E.g., see how much this agent had to supply versus how much stock there was.
        # TODO: Currently, the demand for the next round equals the default demand. Improve!
        """
        self.demand = self.default_demand.copy()

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
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.demand = {
            Component.VIRGIN: self.random.normalvariate(mu=2.0, sigma=0.2),
            Component.RECYCLATE_LOW: self.random.normalvariate(mu=2.0, sigma=0.2),
            Component.RECYCLATE_HIGH: self.random.normalvariate(mu=3.0, sigma=0.1)}

        self.default_demand = self.demand.copy()

        self.stock = {
            Component.VIRGIN: self.random.normalvariate(mu=2.0, sigma=0.2),
            Component.RECYCLATE_LOW: self.random.normalvariate(mu=2.0, sigma=0.2),
            Component.RECYCLATE_HIGH: self.random.normalvariate(mu=3.0, sigma=0.1),
            Component.PARTS: [Part() for _ in range(100)]}

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """

        refiners = self.all_agents[Refiner]
        post_shredders = self.all_agents[Recycler]

        refiners = self.get_sorted_suppliers(suppliers=refiners, component=Component.VIRGIN)
        self.get_component_from_suppliers(suppliers=refiners, component=Component.VIRGIN)

        post_shredders_low = self.get_sorted_suppliers(suppliers=post_shredders, component=Component.RECYCLATE_LOW)
        self.get_component_from_suppliers(suppliers=post_shredders_low, component=Component.RECYCLATE_LOW)

        post_shredders_high = self.get_sorted_suppliers(suppliers=post_shredders, component=Component.RECYCLATE_HIGH)
        self.get_component_from_suppliers(suppliers=post_shredders_high, component=Component.RECYCLATE_HIGH)


class Refiner(GenericAgent):

    def __init__(self, unique_id, model, all_agents):
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.VIRGIN] = math.inf
        self.prices[Component.VIRGIN] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit

    def step(self):
        """
        Step method.
        """
        pass


class Recycler(GenericAgent):
    """
    Recycler and Postshredder agent.
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.RECYCLATE_LOW] = self.random.normalvariate(mu=10.0, sigma=2)
        self.stock[Component.RECYCLATE_HIGH] = self.random.normalvariate(mu=10.0, sigma=2)

        self.prices[Component.RECYCLATE_LOW] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit
        self.prices[Component.RECYCLATE_HIGH] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit

        # TODO: Need to define demand and default_demand (but for this, we need to define this agent's suppliers first)

        # Recyclers get both CARS and PARTS from Garages and Dismantlers. Therefore, they have demand for both CARS and PARTS.
        # Is PARTS demand > CARS demand or vice-versa?

        self.demand[Component.PARTS] = round(self.random.normalvariate(mu=100.0, sigma=2))
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]
        self.demand[Component.CARS] = round(self.random.normalvariate(mu=100.0, sigma=2))
        self.default_demand[Component.CARS] = self.demand[Component.CARS]

    def step(self):
        """
        Step method.
        """

    def process_components(self):
        # return super().process_components()

        # Shred parts to extract plastic
        # VIRGIN plastic present in the parts is recycled as RECYCLATE_HIGH. 
        # RECYCLATE_HIGH present in part is extracted and is converted into RECYCLATE_LOW.
        # The RECYCLATE_LOW in components is discareded. 
        for part in self.stock[Component.PARTS]:
            plastic_ratio = part.extract_plastic()
            self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_HIGH]
            self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.VIRGIN]
        self.stock[Component.PARTS] = []

        # Shred cars to extract plastic
        for car in self.stock[Component.CARS]:
            # Extracting parts to get the plastic 
            for part in car.parts:
                plastic_ratio = part.extract_plastic()
                self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_HIGH]
                self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.VIRGIN]
        self.stock[Component.CARS] = []

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers for CARS
        self.garages = self.all_agents[Garage]
        garages = self.get_sorted_suppliers(suppliers=self.garages, component=Component.CARS)
        self.get_component_from_suppliers(suppliers=garages, component=Component.CARS)

        # Suppliers for PARTS
        self.dismantlers = self.all_agents[Dismantler]
        dismantlers = self.get_sorted_suppliers(suppliers=self.dismantlers, component=Component.PARTS)
        self.get_component_from_suppliers(suppliers=dismantlers, component=Component.PARTS)


class CarManufacturer(GenericAgent):
    """
    CarManufcaturer agent.
    """

    def __init__(self, unique_id, model, all_agents, brand):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.brand = brand

        self.stock[Component.PARTS] = [Part() for _ in range(100)]
        self.stock[Component.CARS] = [Car(Brand.MERCEDES) for _ in range(10)]

        self.prices[Component.PARTS] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit
        self.prices[Component.CARS] = self.random.normalvariate(mu=1000.0, sigma=0.2)  # cost per unit

        self.demand[Component.PARTS] = round(self.random.normalvariate(mu=100.0, sigma=2))
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers
        self.parts_manufacturers = self.all_agents[PartsManufacturer]
        parts_manufacturers = self.get_sorted_suppliers(suppliers=self.parts_manufacturers, component=Component.PARTS)
        self.get_component_from_suppliers(suppliers=parts_manufacturers, component=Component.PARTS)

    def process_components(self):
        """
        Manufacture specific amount of cars.
        """
        # TODO: Implement this while using some kind of combination of parts and considering minimum requirements.
        pass


class User(GenericAgent):
    """
    This agent was used to validate the car buying behavior. Currently, a user buys a car at each instant.
    # TODO: Changes are needed.
    """

    def __init__(self, unique_id, model, all_agents):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.CARS] = []
        self.demand[Component.CARS] = 1
        self.default_demand[Component.CARS] = self.demand[Component.CARS]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        self.car_manufacturers = self.all_agents[CarManufacturer]
        car_manufacturers = self.get_sorted_suppliers(suppliers=self.car_manufacturers, component=Component.CARS)
        self.get_component_from_suppliers(suppliers=car_manufacturers, component=Component.CARS)


class Garage(GenericAgent):
    """
    This agent was used to validate the car buying behavior.
    # TODO: Further implementation is needed
    """

    def __init__(self, unique_id, model, all_agents):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)


class Dismantler(GenericAgent):
    """
    This agent was used to validate the car buying behavior.
    # TODO: Further implementation is needed
    """

    def __init__(self, unique_id, model, all_agents):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.PARTS] = [Part() for _ in range(100)]

        # Randomly select a brand for each car in the stock
        brands = []
        for brand in Brand:
            brands.append(str(brand).rpartition('.')[2])
        self.stock[Component.CARS] = [Car(brand=self.random.choice(brands)) for _ in range(10)]

        self.prices[Component.PARTS] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit

        self.demand[Component.CARS] = round(self.random.normalvariate(mu=100.0, sigma=2))
        self.default_demand[Component.CARS] = self.demand[Component.CARS]

    def process_components(self):
        """
        Dismantle the car and adds the extracted parts to stock
        """

        # Sanity check
        if len(self.stock[Component.CARS]) < 1:
            raise 'ValueError'
        # Dismantles the car, reuses the STANDARD parts and adds them to the stock
        for car in self.stock[Component.CARS]:
            for part in car.parts:
                if part.state.__eq__(PartState.STANDARD):
                    print('going into the enumeration')
                    part = Part.reuse(part)
                    self.stock[Component.PARTS].append(part)
                else:
                    # TODO: What to do with the reused parts?
                    pass
        self.stock[Component.CARS] = []

    def get_all_components(self):
        """
        Determine the order of suppliers (Garages) by personal preference and then buy components.
        """
        self.garages = self.all_agents[Garage]
        garages = self.get_sorted_suppliers(suppliers=self.garages, component=Component.CARS)
        self.get_component_from_suppliers(suppliers=garages, component=Component.CARS)

    # TODO: Send dismantelled cars to Recyclers
