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
            Component.DISCARDED_PARTS: [],
            Component.PARTS: [],
            Component.CARS: [],
            Component.CARS_FOR_SHREDDER: [],
            Component.CARS_FOR_DISMANTLER: []
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
        self.default_demand = self.demand.copy()

        # Prices for specific components
        self.prices = {
            Component.VIRGIN: math.inf,
            Component.RECYCLATE_LOW: math.inf,
            Component.RECYCLATE_HIGH: math.inf,
            Component.PARTS: math.inf,
            Component.CARS: math.inf
        }

        # Minimum requirements given by law or car designer
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
            self.stock[component] += supplies

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
        pass

    def update_demand(self):
        """
        Update own demand for next round. E.g., see how much this agent had to supply versus how much stock there was.
        # TODO: Currently, the demand for the next round equals the default demand. Improve!
        # TODO: This function could maybe also used to adjust prices, etc. for the next round.
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
            Component.RECYCLATE_HIGH: self.random.normalvariate(mu=3.0, sigma=0.1),
            Component.PARTS: round(self.random.normalvariate(mu=50.0, sigma=10.0))}  # How many parts to manufacture

        self.default_demand = self.demand.copy()

        self.stock = {
            Component.VIRGIN: self.random.normalvariate(mu=2.0, sigma=0.2),
            Component.RECYCLATE_LOW: self.random.normalvariate(mu=2.0, sigma=0.2),
            Component.RECYCLATE_HIGH: self.random.normalvariate(mu=3.0, sigma=0.1),
            Component.PARTS: [Part() for _ in range(100)]}

        self.minimum_requirements = {
            Component.RECYCLATE_LOW: 0.2,
            Component.RECYCLATE_HIGH: 0.2}

    def process_components(self):
        """
        Manufacture parts out of plastic.

        Remark: Currrently, this is very simply implemented as it doesn't specify what plastic_ratio the parts have.
        """

        for _ in range(self.demand[Component.PARTS]):
            plastic_ratio = self.compute_plastic_ratio()
            new_part = Part(plastic_ratio)
            self.stock[Component.PARTS].append(new_part)

    def compute_plastic_ratio(self):
        """
        Compute the ratio of plastic that is needed to create parts
        :return:
        """

        plastic_ratio = {
            Component.VIRGIN: 0,
            Component.RECYCLATE_LOW: self.random.uniform(self.minimum_requirements[Component.RECYCLATE_LOW],
                                                    self.minimum_requirements[Component.RECYCLATE_LOW] * 1.25),
            Component.RECYCLATE_HIGH: self.random.uniform(self.minimum_requirements[Component.RECYCLATE_HIGH],
                                                     self.minimum_requirements[Component.RECYCLATE_HIGH] * 1.25)
        }

        # Adjust virgin plastic weight such that the sum of all plastic will be 1.0
        plastic_ratio[Component.VIRGIN] = max(0, 1.0 - sum(plastic_ratio.values()))

        return plastic_ratio

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
    """
    Refiner agent that produces virgin plastic.
    """

    def __init__(self, unique_id, model, all_agents):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)
        self.stock[Component.VIRGIN] = math.inf
        self.prices[Component.VIRGIN] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit


class Recycler(GenericAgent):
    """
    Recycler agent that processes old parts and cars into recyclate plastic.
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


class CarManufacturer(GenericAgent):
    """
    CarManufcaturer agent which transforms parts into cars.
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
        self.stock[Component.CARS] = [Car(self.brand) for _ in range(10)]

        self.prices[Component.PARTS] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit
        self.prices[Component.CARS] = self.random.normalvariate(mu=1000.0, sigma=0.2)  # cost per unit

        self.demand[Component.PARTS] = round(self.random.normalvariate(mu=100.0, sigma=2))
        self.demand[Component.CARS] = round(self.random.normalvariate(mu=10.0, sigma=2))  # aim to produce
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers
        parts_manufacturers = self.all_agents[PartsManufacturer]
        parts_manufacturers = self.get_sorted_suppliers(suppliers=parts_manufacturers, component=Component.PARTS)
        self.get_component_from_suppliers(suppliers=parts_manufacturers, component=Component.PARTS)

    def process_components(self):
        """
        Manufacture specific amount of cars.
        """
        for _ in range(self.demand[Component.CARS]):
            parts = self.get_next_parts(nr_of_parts=4)
            if not parts:
                break
            else:
                new_car = Car(brand=self.brand, parts=parts)
                self.stock[Component.CARS].append(new_car)

    def get_next_parts(self, nr_of_parts=4):
        """
        Get the next four parts from stock and return them to create a car with them.
        :param nr_of_parts: int: indicates how many parts a car needs to be fully assembled
        :return:
            next_parts: list with Parts
        """
        all_parts = self.stock[Component.PARTS]

        if len(all_parts) >= nr_of_parts:
            next_parts = all_parts[:4]
        else:
            next_parts = []

        return next_parts


class User(GenericAgent):
    """
    Car user agent. Can buy a car, use it, and can bring it to a garage for repairs or for discarding it.
    # TODO: Changes are needed.
    """

    def __init__(self, unique_id, model, all_agents, car=None, use_intensity=1):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)
        self.use_intensity = use_intensity
        self.car_repair = False

        self.garages = []
        if car is None:
            self.stock[Component.CARS] = []
        else:
            self.stock[Component.CARS] = [car]
        self.demand[Component.CARS] = 1
        self.default_demand[Component.CARS] = self.demand[Component.CARS]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        For a user this function buys a car of a car manufacturer when it has no car in possession and its car is not
        being repaired at a garage.
        When the user has bought the car, the ELV of the car is corrected by the intensity of use of the car.
        """

        if not self.stock[Component.CARS] and not self.car_repair:
            car_manufacturers = self.all_agents[CarManufacturer]
            car_manufacturers = self.get_sorted_suppliers(suppliers=car_manufacturers, component=Component.CARS)
            self.get_component_from_suppliers(suppliers=car_manufacturers, component=Component.CARS)
            car = self.stock[Component.CARS][0]
            car.ELV = car.ELV * self.use_intensity

    def bring_car_to_garage(self, car):
        """
        Bring car to garage of choice in case it is broken or total loss. Currently, garage is randomly chosen.
        # TODO: choose garage based on price of parts
        """
        if car.state.__eq__(CarState.BROKEN):
            garages = self.all_agents[Garage]
            garage_of_choice = self.random.choice(garages)
            garage_of_choice.receive_car_from_user(user=self, car=car)
            self.car_repair = True
        elif car.state.__eq__(CarState.END_OF_LIFE):
            garages = self.all_agents[Garage]
            garage_of_choice = self.random.choice(garages)
            garage_of_choice.receive_car_from_user(user=self, car=car)

    def possess_car(self):
        """
        A user possesses a car. In case its car is not at the garage, the user will bring the car to the garage in case
        it is broken and continues using the car. If it is not broken, it will simply use the car.
        At the moment the equivalent of process_components.
        """
        if self.stock[Component.CARS]:
            car = self.stock[Component.CARS][0]
            self.bring_car_to_garage(car)
            car.use_car()

    def process_components(self):
        self.possess_car()


class Garage(GenericAgent):
    """
    This agent was used to validate the car buying behavior.
    """

    def __init__(self, unique_id, model, all_agents, circularity_friendliness=0.2):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.customer_base = {}
        self.circularity_friendliness = circularity_friendliness

        self.prices[Component.PARTS] = self.random.normalvariate(mu=4, sigma=0.2)  # cost per unit

        self.stock[Component.CARS] = []
        self.stock[Component.PARTS] = []
        self.stock[Component.DISCARDED_PARTS] = []
        self.stock[Component.CARS_FOR_SHREDDER] = []
        self.stock[Component.CARS_FOR_DISMANTLER] = []

        self.demand[Component.PARTS] = round(self.random.normalvariate(mu=100.0, sigma=2))
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        parts_suppliers = self.all_agents[PartsManufacturer] + self.all_agents[Dismantler]
        parts_suppliers = self.get_sorted_suppliers(suppliers=parts_suppliers, component=Component.PARTS)
        self.get_component_from_suppliers(suppliers=parts_suppliers, component=Component.PARTS)

    def receive_car_from_user(self, user, car):
        """
        Receive a car from User. Should be initiated by User in case car is broken, it can choose which garage to go to.
        We keep track of which user a car belongs to in the customer base.
        If the car is at the end of its life, the garage decides whether the car goes to the shredder or dismantler.
        # TODO: merge with get_all_components?
        """
        component = Component.CARS
        self.demand[component] = 1  # To make functions work for receiving cars.

        self.get_component_from_suppliers(suppliers=user, component=component)

        if car.state.__eq__(CarState.BROKEN):
            self.customer_base[car] = user

        elif car.state.__eq__(CarState.END_OF_LIFE):
            if self.random.random() < self.circularity_friendliness:
                self.stock[Component.CARS_FOR_DISMANTLER].append(car)
            else:
                self.stock[Component.CARS_FOR_SHREDDER].append(car)

    def repair_and_return_cars(self):
        """
        In the Car class is defined which component is broken and needs to be replaced, currently limited to one part.
        This function simply replaces that part.
        At the moment the equivalent of process_components.
        """
        cars_to_be_repaired = self.stock[Component.CARS]
        while self.stock[Component.PARTS]:

            car = cars_to_be_repaired[0]
            cars_to_be_repaired = cars_to_be_repaired[1:]

            if car.state.__eq__(CarState.BROKEN):
                part = self.stock[Component.PARTS][0]
                self.stock[Component.PARTS] = self.stock[Component.PARTS][1:]

                removed_part = car.parts[0]
                self.stock[Component.DISCARDED_PARTS].append(removed_part)
                car.repair_car(part)

                self.provide(recepient=self.customer_base[car], component=Component.CARS, amount=1)
                self.customer_base[car].car_repair = False

    def process_components(self):
        self.repair_and_return_cars()


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
