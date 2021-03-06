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
            Component.PARTS_FOR_RECYCLER: [],
            Component.PARTS: [],
            Component.CARS: [],
            Component.CARS_FOR_RECYCLER: [],
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

        # Track how much was sold last tick and the tick before that
        self.sold_volume = {'last': 0, 'second_last': 0}

        # The following numbers have been adjusted
        self.demand_elasticity = 0.5  # earlier: 0.5
        self.max_demand_scaling = 2.0  # earlier: 2.0
        self.min_demand_scaling = 1.0 / self.max_demand_scaling

        self.price_elasticity = 0.1
        self.max_price_scaling = 1.1
        self.min_price_scaling = 1.0 / self.max_price_scaling

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

    def get_component_from_suppliers(self, suppliers, component, amount=None):
        """
        Go through the suppliers and try to buy a specific component.
        Either try to get components in order to cover own demand or to get a specific amount of components.
        :param amount: int
        :param suppliers: list of Agents
        :param component: Component that this agent demands
        """

        # Check whether agent already has enough in stock
        enough_in_stock = False

        if isinstance(self.stock[component], float or int):
            if self.demand[component] <= self.stock[component]:
                enough_in_stock = True

        elif isinstance(self.stock[component], list):
            if self.demand[component] <= len(self.stock[component]):
                enough_in_stock = True

        if not enough_in_stock:

            if amount is None:
                rest_demand = self.demand[component]
            else:
                rest_demand = amount

            while suppliers and rest_demand > 0.0:
                supplier = suppliers[0]
                stock_of_supplier = supplier.get_stock()[component]

                if self.sufficient_stock(rest_demand, stock_of_supplier):
                    supplier.provide(recipient=self, component=component, amount=rest_demand)
                    self.reduce_current_demand(supplies=rest_demand, component=component)
                    supplier.register_sales(rest_demand)
                else:
                    rest_stock = self.get_rest_stock(stock_of_supplier)
                    supplier.provide(recipient=self, component=component, amount=rest_stock)
                    self.reduce_current_demand(supplies=rest_stock, component=component)
                    # Always register the real demand for parts
                    supplier.register_sales(rest_demand)

                # Adjust remaining demand and supplier list
                rest_demand = self.demand[component]
                suppliers = suppliers[1:]

    def reduce_current_demand(self, supplies, component):
        """
        After receiving components, the current demand should be reduced accordingly.
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
            # Give supplies to the recipient
            recipient.receive(component=component,
                              amount=amount,
                              supplies=supplies)

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
        Take into account different data types of scenarios parameters.
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
            price_scaling_factor = noise * min(self.max_price_scaling,
                                               max(self.min_price_scaling,
                                                   (prev_year / prev_prev_year) ** self.price_elasticity))
            self.prices[component] *= price_scaling_factor
        else:
            self.prices[component] = component.get_random_price()

    def adjust_future_demand(self, component):
        """
        Adjust the demand of an agent's component for the next instant.
        :param component: Component
        """
        self.demand[component] = self.default_demand[component]

        prev_year = self.sold_volume['last']
        prev_prev_year = self.sold_volume['second_last']
        noise = self.random.normalvariate(mu=1.0, sigma=0.2)

        if prev_year != 0 and prev_prev_year != 0:
            demand_scaling_factor = noise * min(self.max_demand_scaling,
                                                max(self.min_demand_scaling,
                                                    (prev_year / prev_prev_year) ** self.demand_elasticity))
            self.demand[component] *= demand_scaling_factor
            if component == Component.PARTS or component == Component.CARS:
                self.demand[component] = round(self.demand[component])
            self.default_demand[component] = self.demand[component]

        elif prev_year != 0 or prev_prev_year != 0:
            self.demand[component] = sum(self.sold_volume.values())

        else:  # All other instants of simulation
            self.demand[component] = self.default_demand[component]


class PartsManufacturer(GenericAgent):
    """
    PartsManufacturer agent.
    """

    def __init__(self, unique_id, model, all_agents, minimal_requirements):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.demand = {
            Component.VIRGIN: 95.0,
            Component.RECYCLATE_LOW: 10.0,
            Component.RECYCLATE_HIGH: 0.0,
            Component.PARTS: 100
        }

        self.default_demand = self.demand.copy()

        self.stock = {
            Component.VIRGIN: 20.0,
            Component.RECYCLATE_LOW: 10.0,
            Component.RECYCLATE_HIGH: 10.0,
            Component.PARTS: [Part() for _ in range(150)]
        }

        self.minimum_requirements = minimal_requirements
        self.plastic_ratio = self.compute_plastic_ratio()

        self.current_year_sales = 0

    def process_components(self):
        """
        Manufacture parts out of plastic.
        """

        for _ in range(self.demand[Component.PARTS]):

            # Check whether there is enough virgin and high quality plastic in the stock
            virgin = self.plastic_ratio[Component.VIRGIN]
            recyclate_high = self.plastic_ratio[Component.RECYCLATE_HIGH]
            recyclate_low = self.plastic_ratio[Component.RECYCLATE_LOW]

            if virgin <= self.stock[Component.VIRGIN] and recyclate_high <= self.stock[Component.RECYCLATE_HIGH]:
                excess_high_quality = self.stock[Component.RECYCLATE_HIGH] - recyclate_high

                # Check whether there is enough low and high quality plastic in stock for low quality purposes
                if recyclate_low <= self.stock[Component.RECYCLATE_LOW] + excess_high_quality:

                    # And check whether there really exists a shortage in low quality plastics and update plastic ratios
                    if recyclate_low > self.stock[Component.RECYCLATE_LOW]:
                        low_quality_shortage = recyclate_low - self.stock[Component.RECYCLATE_LOW]
                        self.plastic_ratio[Component.RECYCLATE_HIGH] += low_quality_shortage
                        self.plastic_ratio[Component.RECYCLATE_LOW] -= low_quality_shortage

                    # Create new part
                    self.produce_part()

            elif virgin <= self.stock[Component.VIRGIN] and recyclate_low <= self.stock[Component.RECYCLATE_LOW]:
                high_quality_shortage = recyclate_high - self.stock[Component.RECYCLATE_HIGH]
                self.plastic_ratio[Component.VIRGIN] += high_quality_shortage
                self.plastic_ratio[Component.RECYCLATE_HIGH] -= high_quality_shortage

                # Stop producing parts in case there is not enough virgin plastic to replace recyclate
                if self.plastic_ratio[Component.VIRGIN] > self.stock[Component.VIRGIN]:
                    break

                # Create new part
                self.produce_part()

            elif virgin <= self.stock[Component.VIRGIN]:
                # Calculate recyclate shortages
                low_quality_shortage = recyclate_low - self.stock[Component.RECYCLATE_LOW]
                high_quality_shortage = recyclate_high - self.stock[Component.RECYCLATE_HIGH]

                # And adjust plastic ratios for part accordingly
                self.plastic_ratio[Component.VIRGIN] = virgin + low_quality_shortage + high_quality_shortage
                self.plastic_ratio[Component.RECYCLATE_HIGH] = self.stock[Component.RECYCLATE_HIGH]
                self.plastic_ratio[Component.RECYCLATE_LOW] = self.stock[Component.RECYCLATE_LOW]

                # Stop producing parts in case there is not enough virgin plastic to replace recyclate
                if self.plastic_ratio[Component.VIRGIN] > self.stock[Component.VIRGIN]:
                    break

                # Create new part
                self.produce_part()

            else:
                # Stop producing parts if there is also not enough virgin plastic
                break

    def produce_part(self):
        new_part = Part(self.plastic_ratio)
        self.stock[Component.PARTS].append(new_part)

        # Remove plastic from stock
        self.stock[Component.VIRGIN] -= self.plastic_ratio[Component.VIRGIN]
        self.stock[Component.RECYCLATE_HIGH] -= self.plastic_ratio[Component.RECYCLATE_HIGH]
        self.stock[Component.RECYCLATE_LOW] -= self.plastic_ratio[Component.RECYCLATE_LOW]

    def compute_plastic_ratio(self):
        """
        Compute the ratio of plastic that is needed to create parts.
        :return:
            plastic_ratio: dictionary {Component: float}
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
                Component.RECYCLATE_LOW: plastic_ratio[Component.RECYCLATE_LOW] / ratio_recyclables,
                Component.RECYCLATE_HIGH: plastic_ratio[Component.RECYCLATE_HIGH] / ratio_recyclables
            }

        # Adjust virgin plastic weight such that the sum of all plastic will be 1.0
        plastic_ratio[Component.VIRGIN] = max(0.0, 1.0 - ratio_recyclables)

        return plastic_ratio

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components. Also check whether it already
        has enough parts in stock.
        """

        refiners = self.all_agents[Refiner]
        recyclers = self.all_agents[Recycler]

        # Saving the low quality recyclate demand and current stock.
        low_quality_demand = self.demand[Component.RECYCLATE_LOW]
        saved_low_quality_stock = self.stock[Component.RECYCLATE_LOW]

        # Trying to buy low quality recyclate.
        recyclers_low = self.get_sorted_suppliers(suppliers=recyclers, component=Component.RECYCLATE_LOW)
        self.get_component_from_suppliers(suppliers=recyclers_low, component=Component.RECYCLATE_LOW)

        """
        If there is a shortage of low quality recyclate, we update the high quality recyclate demand. A higher
        quality recyclate can always be used for lower quality purposes.
        """
        gathered_low_quality_stock = self.stock[Component.RECYCLATE_LOW] - saved_low_quality_stock
        low_quality_demand_shortage = max(0.0, low_quality_demand - gathered_low_quality_stock)

        if low_quality_demand_shortage > 0.0:
            self.demand[Component.RECYCLATE_HIGH] += low_quality_demand_shortage

        # Saving the high quality recyclate demand and current stock.
        high_quality_demand = self.demand[Component.RECYCLATE_HIGH]
        saved_high_quality_stock = self.stock[Component.RECYCLATE_HIGH]

        # Trying to buy high quality recyclate.
        recyclers_high = self.get_sorted_suppliers(suppliers=recyclers, component=Component.RECYCLATE_HIGH)
        self.get_component_from_suppliers(suppliers=recyclers_high, component=Component.RECYCLATE_HIGH)

        """
        If there is a shortage of high and/or low quality recyclate, we update the demand for virgin materials. In 
        case this happens, parts manufacturers will not comply anymore to regulatory standards but do ensure the 
        rigidity of the supply chain.
        """
        gathered_high_quality_stock = self.stock[Component.RECYCLATE_HIGH] - saved_high_quality_stock
        high_quality_demand_shortage = max(0.0, high_quality_demand - gathered_high_quality_stock)

        if high_quality_demand_shortage > 0.0:
            self.demand[Component.VIRGIN] += high_quality_demand_shortage

        # Buy virgin plastics.
        refiners = self.get_sorted_suppliers(suppliers=refiners, component=Component.VIRGIN)
        self.get_component_from_suppliers(suppliers=refiners, component=Component.VIRGIN)

    def update(self):
        """
        Update prices and demand for the next instant depending on the sales trend within the last two instants.
        """
        self.sold_volume['second_last'] = self.sold_volume['last']
        self.sold_volume['last'] = self.current_year_sales
        self.current_year_sales = 0

        self.adjust_future_prices(component=Component.PARTS)
        self.adjust_future_demand(component=Component.PARTS)

    def adjust_future_demand(self, component):
        """
        Parts manufacturers update their demand for parts, and according to their plastic ratios they update their
        demand for raw materials.
        """
        prev_year = self.sold_volume['last']
        prev_prev_year = self.sold_volume['second_last']
        noise = self.random.normalvariate(mu=1.0, sigma=0.05)

        if prev_year != 0 and prev_prev_year != 0:  # First instant of simulation
            demand_scaling_factor = noise * min(self.max_demand_scaling,
                                                max(self.min_demand_scaling,
                                                    (prev_year / prev_prev_year) ** self.demand_elasticity))

            self.demand[component] *= demand_scaling_factor
            self.demand[component] = round(self.demand[component])

        # This will be used when an agent starts selling components or stops selling. With the current implementation
        # demand must stay significant for the model not to crash.
        elif prev_year != 0 or prev_prev_year != 0:
            self.demand[component] = max(self.default_demand[component],
                                         round(sum(self.sold_volume.values()) /
                                               len(self.all_agents[PartsManufacturer])))

        # Adjust demand for plastic as well
        self.plastic_ratio = self.compute_plastic_ratio()
        for plastic_type, ratio in self.plastic_ratio.items():
            self.demand[plastic_type] = ratio * self.demand[Component.PARTS]

    def register_sales(self, sales):
        """
        Register the sales of an agent during the current instant. This can then be used later to adjust prices and e.g.
        production of components.
        """
        self.current_year_sales += sales


class Refiner(GenericAgent):
    """
    Refiner agent that produces virgin plastic.
    """

    def __init__(self, unique_id, model, all_agents, externality_factor, shock_probability=0.0,
                 annual_price_increase=1.0):
        """
        :param annual_price_increase: float: facto by which the price increases linearly due to drying up of global oil
        :param shock_probability: float: annual probability of a shock to the oil price
        :param externality_factor: float: factor by which price is increased to include externalities
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)
        self.shock_probability = shock_probability
        self.annual_price_increase = annual_price_increase
        self.stock[Component.VIRGIN] = math.inf
        self.prices[Component.VIRGIN] = self.random.normalvariate(mu=2.5, sigma=0.2) * externality_factor

    def update(self):
        """
        Update prices for the next instant depending on the sales trend within the last two instants.
        And add a potential adjustment in case of an ail price shock.
        """
        # Normal adjustment
        self.adjust_future_prices(component=Component.VIRGIN)

        # Annual adjustment of price due to global oil drying up
        self.prices[Component.VIRGIN] += self.annual_price_increase  # Remark: compounding price increase

        # Adjustment in case of a oil price shock
        shock_factor = 1.5
        if self.random.random() < self.shock_probability:
            self.prices[Component.VIRGIN] *= shock_factor


class Recycler(GenericAgent):
    """
    Recycler agent that processes old parts and cars into recyclate plastic.
    """

    def __init__(self, unique_id, model, all_agents, annual_efficiency_increase, cohesive_factor=1.0):
        """
        :param annual_efficiency_increase: float: annual factor of how much efficiency improves
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        :param cohesive_factor: float: how much efficiency increases due to better solvable cohesives

        """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.PARTS_FOR_RECYCLER] = [Part(state=PartState.REUSED) for _ in range(10)]
        self.stock[Component.RECYCLATE_LOW] = self.random.normalvariate(mu=20.0, sigma=2)
        self.stock[Component.RECYCLATE_HIGH] = self.random.normalvariate(mu=50.0, sigma=2)
        self.stock[Component.CARS_FOR_RECYCLER] = [Car() for _ in range(10)]

        self.prices[Component.RECYCLATE_LOW] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit
        self.prices[Component.RECYCLATE_HIGH] = self.random.normalvariate(mu=3, sigma=0.2)  # cost per unit recyclate

        self.demand[Component.CARS_FOR_RECYCLER] = math.inf  # Take all cars
        self.demand[Component.PARTS_FOR_RECYCLER] = math.inf  # Take all parts

        # 'efficiency' for recyclers control how many times RECYCLATE_HIGH can be recycled as RECYCLATE_HIGH
        self.efficiency = min(1.0, 0.5 * cohesive_factor)
        self.annual_efficiency_increase = annual_efficiency_increase

        self.current_leakage = 0.0

    def update_efficiency(self):
        """
        Updates the recyclying efficiency every year.
        Assumption: Recycling technology improves every year.
        """
        self.efficiency *= self.annual_efficiency_increase
        self.efficiency = min(1.0, self.efficiency)

    def process_components(self):
        """
        Recycler recycles discarded parts and cars.
        """

        # Reset current_leakage of current instant
        self.current_leakage = 0.0

        # Recycle discarded parts and remove from inventory
        while self.stock[Component.PARTS_FOR_RECYCLER]:
            part = self.stock[Component.PARTS_FOR_RECYCLER][0]
            self.stock[Component.PARTS_FOR_RECYCLER] = self.stock[Component.PARTS_FOR_RECYCLER][1:]
            self.recycle_part(part=part)

        # Recycle cars and remove from inventory
        while self.stock[Component.CARS_FOR_RECYCLER]:
            car = self.stock[Component.CARS_FOR_RECYCLER][0]
            self.stock[Component.CARS_FOR_RECYCLER] = self.stock[Component.CARS_FOR_RECYCLER][1:]
            for part in car.parts:
                self.recycle_part(part=part)

    def recycle_part(self, part):
        """
        Recycler recycles one discarded part as follows:
            VIRGIN -> RECYCLATE_HIGH
            RECYCLATE_HIGH -> RECYCLATE_HIGH or RECYCLATE_LOW  (depending on self.efficiency)
            RECYCLATE_LOW -> RECYCLATE_LOW or leaks out of system  (via other industries or incineration)

        :param part: Part
        """
        plastic_ratio = part.extract_plastic()
        self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.VIRGIN]
        if random.uniform(0, 1) < self.efficiency:
            self.stock[Component.RECYCLATE_HIGH] += plastic_ratio[Component.RECYCLATE_HIGH]
            self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_LOW]
        else:
            self.stock[Component.RECYCLATE_LOW] += plastic_ratio[Component.RECYCLATE_HIGH]
            self.current_leakage += plastic_ratio[Component.RECYCLATE_LOW]

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """
        # Suppliers for CARS_FOR_RECYCLER
        garages = self.all_agents[Garage]
        garages = self.get_sorted_suppliers(suppliers=garages, component=Component.CARS_FOR_RECYCLER)
        self.get_component_from_suppliers(suppliers=garages, component=Component.CARS_FOR_RECYCLER)

        # Suppliers for PARTS_FOR_RECYCLER
        parts_suppliers = self.all_agents[Garage] + self.all_agents[Dismantler]
        parts_suppliers = self.get_sorted_suppliers(suppliers=parts_suppliers, component=Component.PARTS_FOR_RECYCLER)
        self.get_component_from_suppliers(suppliers=parts_suppliers, component=Component.PARTS_FOR_RECYCLER)

    def update(self):
        """
        Update prices for the next instant depending on the sales developed within the last two instants.
        """
        self.adjust_future_prices(component=Component.RECYCLATE_LOW)
        self.adjust_future_prices(component=Component.RECYCLATE_HIGH)
        self.update_efficiency()


class CarManufacturer(GenericAgent):
    """
    CarManufacturer agent which transforms parts into cars.
    """

    def __init__(self, unique_id, model, all_agents, brand, car_lifetime=10, nr_of_parts=4, break_down_probability=0.1):
        """
        :param unique_id: int
        :param model: CEPAIModel
        :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        self.brand = brand
        self.nr_of_parts = nr_of_parts
        self.break_down_probability = break_down_probability

        self.stock[Component.PARTS] = [Part() for _ in range(10)]
        self.stock[Component.CARS] = [Car(self.brand) for _ in range(60)]

        self.prices[Component.CARS] = self.random.normalvariate(mu=1000.0, sigma=0.2)  # cost per unit

        self.demand[Component.PARTS] = round(self.random.normalvariate(mu=130.0, sigma=2))
        self.demand[Component.CARS] = round(self.random.normalvariate(mu=40.0, sigma=2))  # aim to produce
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]
        # Set default demand to be equal to number of users divided by car lifetime
        self.default_demand[Component.CARS] = 1000 / car_lifetime

        self.current_year_sales = 0

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components. Also check whether it already
        has enough cars in stock.
        """
        # Check for enough cars and parts in stock
        car_stock = len(self.stock[Component.CARS])
        cars_in_parts_stock = len(self.stock[Component.PARTS]) / self.nr_of_parts
        if self.demand[Component.CARS] > car_stock + cars_in_parts_stock:

            # Suppliers
            parts_manufacturers = self.all_agents[PartsManufacturer]
            parts_manufacturers = self.get_sorted_suppliers(suppliers=parts_manufacturers, component=Component.PARTS)
            self.get_component_from_suppliers(suppliers=parts_manufacturers, component=Component.PARTS)

    def process_components(self):
        while self.stock[Component.PARTS]:
            parts = self.get_next_parts(nr_of_parts=self.nr_of_parts)
            if not parts:
                break
            else:
                new_car = Car(brand=self.brand, parts=parts, break_down_probability=self.break_down_probability)
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
            self.stock[Component.PARTS] = self.stock[Component.PARTS][nr_of_parts:]
        else:
            next_parts = []

        return next_parts

    def update(self):
        """
        Update sold volumes.
        Update prices and demand for the next instant depending on the sales trend within the last two instants.
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
        prev_year = self.sold_volume['last']
        prev_prev_year = self.sold_volume['second_last']
        noise = self.random.normalvariate(mu=1.0, sigma=0.2)

        if prev_year != 0 and prev_prev_year != 0:
            demand_scaling_factor = (prev_year / prev_prev_year) ** self.demand_elasticity
            demand_scaling_factor = noise * min(self.max_demand_scaling,
                                                max(self.min_demand_scaling,
                                                    demand_scaling_factor))
            self.demand[Component.CARS] = math.ceil(self.demand[Component.CARS] * demand_scaling_factor)
            self.demand[component] = self.demand[Component.CARS] * self.nr_of_parts

        elif prev_year != 0 or prev_prev_year != 0:
            sold_last_two_years = max(self.default_demand[component],
                                      sum(self.sold_volume.values()) / len(self.all_agents[CarManufacturer]))
            self.demand[Component.CARS] = sold_last_two_years
            self.demand[component] = self.demand[Component.CARS] * self.nr_of_parts


class User(GenericAgent):
    """
    Car user agent. Can buy a car, use it, and can bring it to a garage for repairs or for discarding it.
    """

    def __init__(self, unique_id, model, all_agents, car=None, std_use_intensity=0.1):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)
        self.std_use_intensity = std_use_intensity
        self.garages = []

        if car is None:
            self.stock[Component.CARS] = []
        else:
            self.stock[Component.CARS] = [car]

        self.demand[Component.CARS] = 1

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        For a user, this method buys a car of a CarManufacturer when it has no car in possession and its car is not
        being repaired at a garage.
        When the user has bought the car, the max_lifetime of the car is corrected by the intensity of use of the car.
        """

        if self.demand[Component.CARS] == 1:
            # Buy new car
            car_manufacturers = self.all_agents[CarManufacturer]
            car_manufacturers = self.get_sorted_suppliers(suppliers=car_manufacturers, component=Component.CARS)
            self.get_component_from_suppliers(suppliers=car_manufacturers, component=Component.CARS)

            # Adjust lifetime of car
            if self.stock[Component.CARS]:
                self.demand[Component.CARS] = 0
                car = self.stock[Component.CARS][0]
                # Add noise
                car.max_lifetime *= self.random.normalvariate(1, self.std_use_intensity)

    def bring_car_to_garage(self, car):
        """
        Bring car to garage of choice in case it is broken or total loss. Currently, garage is randomly chosen.
        """

        if car.state == CarState.BROKEN:
            garage_of_choice = self.select_garage()
            garage_of_choice.receive_car_from_user(user=self, car=car)

        if car.state == CarState.END_OF_LIFE:
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

    def process_components(self):
        """
        A user possesses a car. If it is not broken, it will simply use the car.
        In case the car is broken, the user will bring the car to the garage to be repaired.
        """
        if self.stock[Component.CARS]:
            car = self.stock[Component.CARS][0]
            self.bring_car_to_garage(car)

            if self.stock[Component.CARS]:
                car.use_car()

    def update(self):
        """
        Demand is updated for the user when buying a car and bringing its ELV to the garage.
        """
        pass


class Garage(GenericAgent):
    """
    Garages repair cars, and send ELVs to dismantlers or recyclers.
    """

    def __init__(self, unique_id, model, all_agents, customer_base=None, circularity_friendliness=0.2,
                 min_reused_parts=0.0):
        """
         :param circularity_friendliness:
         :param min_reused_parts: float
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
        """
        super().__init__(unique_id, model, all_agents)

        """
        To keep track of which user a car belongs to, a garage has a dictionary with a certain car in their possession 
        as key and the corresponding user as value. This ensures giving cars back to the rightful owner.
        """
        if customer_base is None:
            self.customer_base = {}
        else:
            self.customer_base = customer_base

        self.circularity_friendliness = circularity_friendliness

        self.stock[Component.CARS] = [car for car in customer_base.keys()]
        self.stock[Component.PARTS] = [Part() for _ in range(20)]
        self.stock[Component.PARTS_FOR_RECYCLER] = [Part() for _ in range(10)]
        self.stock[Component.CARS_FOR_RECYCLER] = []
        self.stock[Component.CARS_FOR_DISMANTLER] = []

        self.demand[Component.PARTS] = round(self.random.normalvariate(mu=60.0, sigma=2))
        self.default_demand[Component.PARTS] = self.demand[Component.PARTS]

        self.min_reused_parts = min_reused_parts
        self.current_year_demand = 0

    def get_all_components(self):
        """
        Determine the order of suppliers by personal preference and then buy components.
        """

        # Get first reused Parts according to minimum requirements
        nr_of_needed_reused_parts = math.ceil(self.demand[Component.PARTS] * self.min_reused_parts)
        dismantlers = self.all_agents[Dismantler]
        self.get_component_from_suppliers(dismantlers, component=Component.PARTS, amount=nr_of_needed_reused_parts)

        # Get remaining parts from all suppliers
        parts_suppliers = self.all_agents[PartsManufacturer] + self.all_agents[Dismantler]
        parts_suppliers = self.get_sorted_suppliers(suppliers=parts_suppliers, component=Component.PARTS)
        self.get_component_from_suppliers(suppliers=parts_suppliers, component=Component.PARTS)

    def receive_car_from_user(self, user, car):
        """
        Receive a car from User. Should be initiated by User in case car is broken, it can choose which garage to go to.
        We keep track of which user a car belongs to in the customer base.
        If the car is at the end of its life, the garage decides whether the car goes to the shredder or dismantler.
        :param user: User
        :param car: Car
        """
        component = Component.CARS
        user.provide(recipient=self, component=component, amount=1)

        if car.state == CarState.BROKEN:
            self.customer_base[car] = user
            self.current_year_demand += 1

        elif car.state == CarState.END_OF_LIFE:
            user.demand[Component.CARS] = 1
            self.stock[Component.CARS].remove(car)
            if self.random.random() < self.circularity_friendliness:
                self.stock[Component.CARS_FOR_DISMANTLER].append(car)
            else:
                self.stock[Component.CARS_FOR_RECYCLER].append(car)

    def repair_and_return_cars(self):
        """
        In the Car class is defined which component is broken and needs to be replaced, currently limited to one part.
        This function simply replaces that part.
        """
        while self.stock[Component.PARTS] and self.stock[Component.CARS]:

            car = self.stock[Component.CARS].pop(0)

            if car.state == CarState.BROKEN:
                # Repair car
                new_part = self.stock[Component.PARTS].pop(0)
                removed_part = car.parts[0]
                self.stock[Component.PARTS_FOR_RECYCLER].append(removed_part)
                car.repair_car(new_part)

                # Return car to user
                user = self.customer_base[car]
                user.stock[Component.CARS].append(car)

                # Remove user
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
        Update yearly demand for parts.
        Update prices and demand for the next instant depending on the sales trend within the last two instants.
        """
        self.sold_volume['second_last'] = self.sold_volume['last']
        self.sold_volume['last'] = self.demand[Component.PARTS]

        self.adjust_future_demand(component=Component.PARTS)
        self.adjust_future_prices(component=Component.PARTS)

    def adjust_future_demand(self, component):
        """
        Garages update their demand differently, because they are conceptually different. Garages anticipate more on
        cars to be repaired to be able to repair them in the same year. They do so by checking whether they have enough
        stock to absorb shocks.
        """
        self.demand[component] = self.current_year_demand + len(self.stock[Component.CARS])
        self.current_year_demand = 0


class Dismantler(GenericAgent):
    """
    Dismanters dismantle cars into parts and the remaining cars.
    """

    def __init__(self, unique_id, model, all_agents):
        """
         :param unique_id: int
         :param model: CEPAIModel
         :param all_agents: dictionary with {Agent: list of Agents}
         """
        super().__init__(unique_id, model, all_agents)

        self.stock[Component.PARTS] = [Part() for _ in range(40)]
        self.stock[Component.PARTS_FOR_RECYCLER] = [Part(state=PartState.REUSED) for _ in range(10)]
        self.stock[Component.CARS_FOR_DISMANTLER] = [Car() for _ in range(10)]

        self.demand[Component.CARS_FOR_DISMANTLER] = math.inf

        self.prices[Component.PARTS] = self.random.normalvariate(mu=2.5, sigma=0.2)  # cost per unit

    def process_components(self):
        """
        Dismantlers dismantle cars into parts as follows:
            STANDARD -> REUSED
            REUSED -> PARTS_FOR_RECYCLER
        """
        while self.stock[Component.CARS_FOR_DISMANTLER]:
            # Remove the car from the inventory
            car = self.stock[Component.CARS_FOR_DISMANTLER][0]
            self.stock[Component.CARS_FOR_DISMANTLER] = self.stock[Component.CARS_FOR_DISMANTLER][1:]

            for part in car.parts:
                if part.state == PartState.STANDARD:
                    part.reuse()
                    self.stock[Component.PARTS].append(part)
                else:
                    self.stock[Component.PARTS_FOR_RECYCLER].append(part)

    def get_all_components(self):
        """
        Determine the order of suppliers (Garages) by personal preference and then buy components.
        """
        garages = self.all_agents[Garage]
        garages = self.get_sorted_suppliers(suppliers=garages, component=Component.CARS_FOR_DISMANTLER)
        self.get_component_from_suppliers(suppliers=garages, component=Component.CARS_FOR_DISMANTLER)

    def update(self):
        """
        Update prices for the next instant depending on the sales developed within the last two instants.
        """
        self.adjust_future_prices(component=Component.PARTS)
