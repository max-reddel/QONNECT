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

        # Track how much was sold last tick and the the tick before that
        self.sold_volume = {'last': 0, 'second_last': 0}

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
                supplier.provide(
                    recipient=self, component=component, amount=rest_demand)
                self.reduce_current_demand(
                    supplies=rest_demand, component=component)
                supplier.register_sales(rest_demand)
            else:
                rest_stock = self.get_rest_stock(stock_of_supplier)
                supplier.provide(
                    recipient=self, component=component, amount=rest_stock)
                self.reduce_current_demand(
                    supplies=rest_stock, component=component)
                supplier.register_sales(rest_stock)

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

    def provide(self, recipient, component, amount):
        """
        This method provides a specific amount of a specific component to a specific buyer.
        :param recipient: Agent
        :param component: Component
        :param amount: float or int
        """
        if isinstance(self.stock[component], float) or isinstance(self.stock[component], int):
            self.stock[component] -= amount
            recipient.receive(component=component, amount=amount)
        elif isinstance(self.stock[component], list):
            # Get the supplies
            supplies = self.stock[component][:amount]
            # Remove supplies from the stock
            self.stock[component] = self.stock[component][amount:]
            # Give supplis to the recipient
            recipient.receive(component=component,
                              amount=amount, supplies=supplies)

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
        Process goods (manufacturing, shredding, using, or repairing).
        """
        pass

    def update(self):
        """
        Update prices and demand for the next instant depending on the sales developed within the last two instants.
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

    def register_sales(self, sales):
        """
        Register the sales of an agent during the current instant. This can then be used later to adjust prices and e.g.
        production of components.
        """
        if isinstance(sales, float) or isinstance(sales, int):
            amount = sales
        elif isinstance(sales, list):
            amount = len(sales)
        else:
            amount = 0

        self.sold_volume['second_last'] = self.sold_volume['last']
        self.sold_volume['last'] = amount

    def adjust_future_prices(self, component):
        """
        Adjust the price of an agent's component for the next instant.
        :param component: Component
        """
        prev_year = self.sold_volume['last']
        prev_prev_year = self.sold_volume['second_last']
        noise = self.random.normalvariate(mu=1.0, sigma=0.2)

        if prev_year != 0 and prev_prev_year != 0:
            self.prices[component] = self.prices[component] * \
                prev_year / prev_prev_year * noise
        else:
            self.prices[component] = component.get_random_price()

    def adjust_future_demand(self, component):
        """
        Adjust the demand of an agent's component for the next instant.
        :param component: Component
        TODO: Doesn't work for agents (only not PMs and CMs?) that get two different components
        """
        prev_year = self.sold_volume['last']
        prev_prev_year = self.sold_volume['second_last']
        noise = self.random.normalvariate(mu=1.0, sigma=0.2)

        if prev_year != 0 and prev_prev_year != 0:
            self.demand[component] = self.demand[component] * \
                prev_year / prev_prev_year * noise
            if component == Component.PARTS or component == Component.CARS:
                self.demand[component] = round(self.demand[component])
        else:
            self.demand[component] = self.default_demand[component]


class PartsManufacturer(GenericAgent):
    """
    PartsManufacturer agent.
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

        self.plastic_ratio = self.compute_plastic_ratio()

    def process_components(self):
        """
        Manufacture parts out of plastic.
        Remark: Currently, this is very simply implemented as it doesn't specify what plastic_ratio the parts have.
        """

        for _ in range(self.demand[Component.PARTS]):
            #plastic_ratio = self.compute_plastic_ratio()
            new_part = Part(self.plastic_ratio)
            self.stock[Component.PARTS].append(new_part)

    def compute_plastic_ratio(self):
        """
        Compute the ratio of plastic that is needed to create parts
        :return:
        # TODO: We dealt with max function with virgin plastics, but what about the recycled materials?
        Let's say recyclate low has a minimum requirement of 20% and high of 80%, by then randomising it we end up
        with more than one again. Maybe create an if statement to check whether the sum of recycled materials is bigger
        than one and if so, scale them to one again.
        """

        plastic_ratio = {
            Component.VIRGIN: 0,
            Component.RECYCLATE_LOW: self.random.uniform(self.minimum_requirements[Component.RECYCLATE_LOW],
                                                         self.minimum_requirements[Component.RECYCLATE_LOW] * 1.25),
            Component.RECYCLATE_HIGH: self.random.uniform(self.minimum_requirements[Component.RECYCLATE_HIGH],
                                                          self.minimum_requirements[Component.RECYCLATE_HIGH] * 1.25)
        }

        ratio_recyclables = plastic_ratio[Component.RECYCLATE_LOW] + plastic_ratio[Component.RECYCLATE_HIGH]
        if ratio_recyclables > 1:
            plastic_ratio = {
                Component.VIRGIN: 0,
                Component.RECYCLATE_LOW: plastic_ratio[Component.RECYCLATE_LOW]/ratio_recyclables,
                Component.RECYCLATE_HIGH: plastic_ratio[Component.RECYCLATE_HIGH]/ratio_recyclables
            }

        # Adjust virgin plastic weight such that the sum of all plastic will be 1.0
        plastic_ratio[Component.VIRGIN] = max(
            0.0, 1.0 - sum(plastic_ratio.values()))

        return plastic_ratio

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """

        refiners = self.all_agents[Refiner]
        post_shredders = self.all_agents[Recycler]

        refiners = self.get_sorted_suppliers(
            suppliers=refiners, component=Component.VIRGIN)
        self.get_component_from_suppliers(
            suppliers=refiners, component=Component.VIRGIN)

        post_shredders_low = self.get_sorted_suppliers(
            suppliers=post_shredders, component=Component.RECYCLATE_LOW)
        self.get_component_from_suppliers(
            suppliers=post_shredders_low, component=Component.RECYCLATE_LOW)

        post_shredders_high = self.get_sorted_suppliers(
            suppliers=post_shredders, component=Component.RECYCLATE_HIGH)
        self.get_component_from_suppliers(
            suppliers=post_shredders_high, component=Component.RECYCLATE_HIGH)

    def update(self):
        """
        Update prices and demand for the next instant depending on the sales developed within the last two instants.
        """
        self.adjust_future_prices(component=Component.PARTS)
        self.adjust_future_demand(component=Component.PARTS)

    def adjust_future_demand(self, component):
        """
        Parts manufacturers adjust demand differently than other agents, because they supply different components than
        they receive. They update their demand for parts and accordingly to their plastic ratios, update their demand
        for raw materials.
        """
        prev_year = self.sold_volume['last']
        prev_prev_year = self.sold_volume['second_last']
        noise = self.random.normalvariate(mu=1.0, sigma=0.2)

        if prev_year != 0 and prev_prev_year != 0:
            self.demand[component] = self.demand[component] * prev_year / prev_prev_year * noise
            self.demand[component] = round(self.demand[component])
        else:
            self.demand[component] = self.default_demand[component]

        self.plastic_ratio = self.compute_plastic_ratio()

        for plastic_type, ratio in self.plastic_ratio.items():
            self.demand[plastic_type] = ratio * self.demand[Component.PARTS]


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
        self.prices[Component.VIRGIN] = self.random.normalvariate(
            mu=2.5, sigma=0.2)  # cost per unit

    def update(self):
        """
        Update prices for the next instant depending on the sales developed within the last two instants.
        """
        self.adjust_future_prices(component=Component.VIRGIN)


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

        self.stock[Component.DISCARDED_PARTS] = [
            Part(state=PartState.REUSED) for _ in range(10)]
        self.stock[Component.RECYCLATE_LOW] = self.random.normalvariate(
            mu=10.0, sigma=2)
        self.stock[Component.RECYCLATE_HIGH] = self.random.normalvariate(
            mu=10.0, sigma=2)
        brands = []
        for brand in Brand:
            brands.append(str(brand).rpartition('.')[2])
        self.stock[Component.CARS_FOR_SHREDDER] = [
            Car(brand=self.random.choice(brands)) for _ in range(10)]

        self.prices[Component.RECYCLATE_LOW] = self.random.normalvariate(
            mu=2.5, sigma=0.2)  # cost per unit of recyclate
        self.prices[Component.RECYCLATE_HIGH] = self.random.normalvariate(
            mu=3, sigma=0.2)  # cost per unit recyclate

        # `efficiency` for recyclers control how many times `RECYCLATE_HIGH` can be recycled as 'RECYCLATE_HIGH'
        self.efficiency = 0.50

    def step(self):
        """
        Step method.
        """

    def process_components(self):
        # return super().process_components()

        # Shred discarded parts to extract plastic
        # VIRGIN plastic present in the discarded parts is recycled as RECYCLATE_HIGH.
        # RECYCLATE_HIGH present in part is extracted and can be either used as RECYCLATE_HIGH or RECYCLATE_LOW depending upon efficiency of the Recycler.
        # Similarly, The RECYCLATE_LOW can be either recycled as RECYCLATE_LOW or discarded depending upon efficiency of the Recycler.

        while len(self.stock[Component.DISCARDED_PARTS]) > 0:
            part = self.stock[Component.DISCARDED_PARTS][0]
            plastic_ratio = Part.extract_plastic(part)
            self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.VIRGIN]
            if random.uniform(0, 1) < self.efficiency:
                self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.RECYCLATE_HIGH]
                self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_LOW]

            else:
                self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_HIGH]
            del self.stock[Component.DISCARDED_PARTS][0]

        # Shred cars to extract plastic
        while len(self.stock[Component.CARS_FOR_SHREDDER]) > 0:
            # Extracting parts to get the plastic
            car = self.stock[Component.CARS_FOR_SHREDDER][0]
            while len(car.parts) > 1:
                part = car.parts[0]
                plastic_ratio = Part.extract_plastic(part)
                self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.VIRGIN]
                if random.uniform(0, 1) < self.efficiency:
                    self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.RECYCLATE_HIGH]
                    self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_LOW]
                else:
                    self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_HIGH]
                del car.parts[0]
            del self.stock[Component.CARS_FOR_SHREDDER][0]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers for CARS_FOR_SHREDDER
        garages = self.all_agents[Garage]
        garages = self.get_sorted_suppliers(
            suppliers=garages, component=Component.CARS_FOR_SHREDDER)
        self.get_component_from_suppliers(
            suppliers=garages, component=Component.CARS_FOR_SHREDDER)

        # Suppliers for DISCARDED_PARTS
        dismantler = self.all_agents[Dismantler]
        dismantler = self.get_sorted_suppliers(
            suppliers=dismantler, component=Component.DISCARDED_PARTS)
        self.get_component_from_suppliers(
            suppliers=dismantler, component=Component.DISCARDED_PARTS)

    def get_component_from_suppliers(self, suppliers, component):
        """
        Go through the suppliers and try to buy a specific component. Recycler buys all the available 'CARS_FOR_SHREDDER' and `DISCARDED_PARTS. 
        :param suppliers: list of Agents
        :param component: Component that this agent demands
        """
        while len(suppliers) > 0.0:
            supplier = suppliers[0]
            stock_of_supplier = supplier.get_stock()[component]
            # Convert stock of supplier to int/float
            if isinstance(stock_of_supplier, float) or isinstance(stock_of_supplier, int):
                pass
                # stock_of_supplier = stock_of_supplier
            elif isinstance(stock_of_supplier, list):
                stock_of_supplier = len(stock_of_supplier)
            # Get the material from supplier
            supplier.provide(recipient=self, component=component,
                             amount=stock_of_supplier)
            # Adjust remaining demand and supplier list
            suppliers = suppliers[1:]

    def update(self):
        """
        Update prices for the next instant depending on the sales developed within the last two instants.
        """
        self.adjust_future_prices(component=Component.RECYCLATE_LOW)
        self.adjust_future_prices(component=Component.RECYCLATE_HIGH)


class CarManufacturer(GenericAgent):
    """
    CarManufacturer agent which transforms parts into cars.
    """

    def __init__(self, unique_id, model, all_agents, brand, nr_of_parts=4):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.brand = brand
        self.nr_of_parts = nr_of_parts

        self.stock[Component.PARTS] = [Part() for _ in range(100)]
        self.stock[Component.CARS] = [Car(self.brand) for _ in range(10)]

        self.prices[Component.PARTS] = self.random.normalvariate(
            mu=2.5, sigma=0.2)  # cost per unit
        self.prices[Component.CARS] = self.random.normalvariate(
            mu=1000.0, sigma=0.2)  # cost per unit

        self.demand[Component.PARTS] = round(
            self.random.normalvariate(mu=100.0, sigma=2))
        self.demand[Component.CARS] = round(
            self.random.normalvariate(mu=10.0, sigma=2))  # aim to produce
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]

        self.current_year_sales = 0

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers
        parts_manufacturers = self.all_agents[PartsManufacturer]
        parts_manufacturers = self.get_sorted_suppliers(
            suppliers=parts_manufacturers, component=Component.PARTS)
        self.get_component_from_suppliers(
            suppliers=parts_manufacturers, component=Component.PARTS)

    def process_components(self):
        """
        Manufacture specific amount of cars.
        """
        for _ in range(self.demand[Component.CARS]):
            parts = self.get_next_parts(nr_of_parts=self.nr_of_parts)
            if not parts:
                break
            else:
                new_car = Car(brand=self.brand, parts=parts)
                self.stock[Component.CARS].append(new_car)

    def get_next_parts(self, nr_of_parts):
        """
        Get the next four parts from stock and return them to create a car with them.
        :param nr_of_parts: int: indicates how many parts a car needs to be fully assembled
        :return:
            next_parts: list with Parts
        """
        all_parts = self.stock[Component.PARTS]

        if len(all_parts) >= nr_of_parts:
            next_parts = all_parts[:nr_of_parts]
        else:
            next_parts = []

        return next_parts

    def update(self):
        """
        Update sold volumes.
        Update prices and demand for the next instant depending on the sales developed within the last two instants.
        """
        self.sold_volume['second_last'] = self.sold_volume['last']
        self.sold_volume['last'] = self.current_year_sales

        self.adjust_future_prices(component=Component.CARS)
        self.adjust_future_demand(component=Component.PARTS)

        self.current_year_sales = 0

    def register_sales(self, sales):
        """
        In the current conceptualization, users buy cars themselves from car manufacturers which means this function is
        called everytime this happens. The general register_sales function can therefore not be used for this purpose.
        Instead, this function keeps track of their sales in another manner.
        """
        self.current_year_sales += sales

    def adjust_future_demand(self, component):
        """
        Car manufacturers adjust demand differently than other agents, because they supply different components than
        they receive.
        """
        prev_year = self.sold_volume['last'] * self.nr_of_parts
        prev_prev_year = self.sold_volume['second_last'] * self.nr_of_parts
        noise = self.random.normalvariate(mu=1.0, sigma=0.2)

        if prev_year != 0 and prev_prev_year != 0:
            self.demand[component] = self.demand[component] * prev_year / prev_prev_year * noise
            self.demand[component] = round(self.demand[component])
        else:
            self.demand[component] = self.default_demand[component]


class User(GenericAgent):
    """
    Car user agent. Can buy a car, use it, and can bring it to a garage for repairs or for discarding it.
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
            car_manufacturers = self.get_sorted_suppliers(
                suppliers=car_manufacturers, component=Component.CARS)
            self.get_component_from_suppliers(
                suppliers=car_manufacturers, component=Component.CARS)

            if self.stock[Component.CARS]:
                car = self.stock[Component.CARS][0]
                car.ELV = car.ELV * self.use_intensity

    def bring_car_to_garage(self, car):
        """
        Bring car to garage of choice in case it is broken or total loss. Currently, garage is randomly chosen.
        """

        if car.state == (CarState.BROKEN or CarState.END_OF_LIFE):

            garage_of_choice = self.select_garage()
            garage_of_choice.receive_car_from_user(user=self, car=car)

    def select_garage(self):
        """
        Users try to find a garage which has parts. They do so by checking garages on the top of their preference list
        whether they have parts to repair their car.
        """
        garages = self.all_agents[Garage]
        garage_preferences = self.get_sorted_suppliers(
            suppliers=garages, component=Component.PARTS)

        selected_garage = None
        cheapest_garage = garage_preferences[0]

        while garage_preferences:
            garage = garage_preferences[0]
            garage_preferences = garage_preferences[1:]
            stock_of_garage = garage.get_stock()[Component.PARTS]

            if stock_of_garage:
                selected_garage = garage
                return selected_garage

        if selected_garage is None:
            return cheapest_garage

    def possess_car(self):
        """
        A user possesses a car. In case its car is not at the garage, the user will bring the car to the garage in case
        it is broken and continues using the car. If it is not broken, it will simply use the car.
        NOTE: it is assumed a car is not for a whole year in the garage. Therefore, the car is still being used the year
        when it is brought to the garage.
        At the moment this function is the equivalent of process_components.
        """
        if self.stock[Component.CARS]:
            car = self.stock[Component.CARS][0]
            self.bring_car_to_garage(car)
            car.use_car()

    def process_components(self):
        """
        The possession of a car is considered to be the 'user stage' of the process_components stage 2. However,
        renaming this function, would not make intuitive sense and might confuse someone trying to read the code.
        """
        self.possess_car()

    def update(self):
        """
        Ensure a user always buys one car in case it does.
        """
        self.demand = self.default_demand


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

        self.prices[Component.PARTS] = self.random.normalvariate(
            mu=4, sigma=0.2)  # cost per unit

        self.stock[Component.CARS] = []
        self.stock[Component.PARTS] = [Part() for _ in range(5)]
        self.stock[Component.DISCARDED_PARTS] = []
        self.stock[Component.CARS_FOR_SHREDDER] = []
        self.stock[Component.CARS_FOR_DISMANTLER] = []

        self.demand[Component.PARTS] = round(
            self.random.normalvariate(mu=100.0, sigma=2))
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]

        self.current_year_demand = 0

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        parts_suppliers = self.all_agents[PartsManufacturer] + \
            self.all_agents[Dismantler]
        parts_suppliers = self.get_sorted_suppliers(
            suppliers=parts_suppliers, component=Component.PARTS)
        self.get_component_from_suppliers(
            suppliers=parts_suppliers, component=Component.PARTS)

    def receive_car_from_user(self, user, car):
        """
        Receive a car from User. Should be initiated by User in case car is broken, it can choose which garage to go to.
        We keep track of which user a car belongs to in the customer base.
        If the car is at the end of its life, the garage decides whether the car goes to the shredder or dismantler.
        """
        component = Component.CARS
        # To make functions work for receiving cars.
        self.demand[component] = 1

        self.get_component_from_suppliers(
            suppliers=[user], component=component)

        if car.state == CarState.BROKEN:
            self.customer_base[car] = user
            user.car_repair = True

            self.current_year_demand += 1

        elif car.state == CarState.END_OF_LIFE:
            self.stock[Component.CARS].remove(car)
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

            if not cars_to_be_repaired:
                break

            car = cars_to_be_repaired[0]
            cars_to_be_repaired = cars_to_be_repaired[1:]

            if car.state == CarState.BROKEN:

                part = self.stock[Component.PARTS][0]
                self.stock[Component.PARTS] = self.stock[Component.PARTS][1:]

                removed_part = car.parts[0]
                self.stock[Component.DISCARDED_PARTS].append(removed_part)
                car.repair_car(part)

                user = self.customer_base[car]
                self.provide(recipient=user,
                             component=Component.CARS, amount=1)
                user.car_repair = False
                self.customer_base.pop(car)

    def process_components(self):
        """
        Repairing and returning cars is considered to be the 'garage stage' of the process_components stage 2.
        Intuitively, the naming of repairing cars of users makes more sense and therefore changing function names, might
        confuse someone trying to read the code.
        """
        self.repair_and_return_cars()

    def update(self):
        """
        Update yearly demand for parts, because garages can see actual demand for their parts.
        Update prices and demand for the next instant depending on the sales developed within the last two instants.
        """
        self.sold_volume['second_last'] = self.sold_volume['last']
        self.sold_volume['last'] = self.current_year_demand

        self.adjust_future_prices(component=Component.PARTS)
        self.adjust_future_demand(component=Component.PARTS)

        self.current_year_demand = 0


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
        self.stock[Component.DISCARDED_PARTS] = [
            Part(state=PartState.REUSED) for _ in range(100)]

        # Randomly select a brand for cars in the stock
        brands = []
        for brand in Brand:
            brands.append(str(brand).rpartition('.')[2])
        self.stock[Component.CARS_FOR_DISMANTLER] = [
            Car(brand=self.random.choice(brands)) for _ in range(10)]

        self.prices[Component.PARTS] = self.random.normalvariate(
            mu=2.5, sigma=0.2)  # cost per unit

    def process_components(self):
        """
        Dismantle the car and adds the extracted parts to stock
        """

        # Sanity check
        # if len(self.stock[Component.CARS_FOR_DISMANTLER]) < 1:
        #     raise 'ValueError'

        # Dismantles the car, reuses the STANDARD parts and adds them to the stock
        while self.stock[Component.CARS_FOR_DISMANTLER]:
            car = self.stock[Component.CARS_FOR_DISMANTLER][0]
            while len(car.parts) > 1:
                part = car.parts[0]
                if part.state == PartState.STANDARD:
                    # print('going into the enumeration')
                    Part.reuse(part)
                    self.stock[Component.PARTS].append(part)
                else:
                    # Reused parts are discarded and sent to the recyclers
                    self.stock[Component.DISCARDED_PARTS].append(part)
                del car.parts[0]
            del self.stock[Component.CARS_FOR_DISMANTLER][0]

    def get_all_components(self):
        """
        Determine the order of suppliers (Garages) by personal preference and then buy components.
        """
        garages = self.all_agents[Garage]
        garages = self.get_sorted_suppliers(
            suppliers=garages, component=Component.CARS_FOR_DISMANTLER)
        self.get_component_from_suppliers(
            suppliers=garages, component=Component.CARS_FOR_DISMANTLER)

    def get_component_from_suppliers(self, suppliers, component):
        """
        Go through the suppliers and try to buy a specific component. Dismantler buys all the available 'CARS_FOR_DISMANTLER'. 
        :param suppliers: list of Agents
        :param component: Component that this agent demands
        """
        while len(suppliers) > 0.0:
            supplier = suppliers[0]
            stock_of_supplier = supplier.get_stock()[component]
            # Convert stock of supplier to int/float
            if isinstance(stock_of_supplier, float) or isinstance(stock_of_supplier, int):
                pass
                # stock_of_supplier = stock_of_supplier
            elif isinstance(stock_of_supplier, list):
                stock_of_supplier = len(stock_of_supplier)
            # Get the material from supplier
            supplier.provide(recipient=self, component=component,
                             amount=stock_of_supplier)
            # Adjust remaining demand and supplier list
            suppliers = suppliers[1:]

    def update(self):
        """
        Update prices for the next instant depending on the sales developed within the last two instants.
        """
        self.adjust_future_prices(component=Component.PARTS)
