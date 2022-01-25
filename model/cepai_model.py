"""
This module contains the plastic model which concerns the Dutch circular economy of plastic in the automotive industry.
"""

from mesa import Model
from mesa.time import StagedActivation
from mesa.datacollection import DataCollector
from model.agents import *
import time


class CEPAIModel(Model):
    """
    The model which concerns the circular economy of plastic in the automotive industry.
    """

    def __init__(self,
                 levers=None,
                 uncertainties=None,
                 agent_counts=None,
                 nr_of_parts=4,
                 break_down_probability=0.3,
                 std_use_intensity=0.1):
        """
        :param levers: dictionary with {"Name": float}
        :param uncertainties: dictionary with {"Name": float}
        :param agent_counts: dictionary with {Agent: int}
        :param nr_of_parts: int: how many parts are needed to create a Car object
        :param break_down_probability: float: probability of a car breaking down at any given year
        :param std_use_intensity: float: standard value of how intensely a user uses a car
        """
        print('Simulation starting...')

        super().__init__()

        # TODO: specify value ranges for levers.
        if levers is None:
            self.levers = {
                "L1": 0.0,  # Minimal requirement for reused parts
                "L2": 0.0,  # Minimal requirement for high-quality plastic
                "L3": 1.0,  # Use better solvable adhesives
                "L4": 1.0,  # Include externality for virgin plastic
                "L5": 0.0   # Minimal requirement for recyclate
            }
        else:
            self.levers = levers

        # TODO: specify value ranges for uncertainties.
        if uncertainties is None:
            self.uncertainties = {
                "X1": 1.0,  # Annual increase factor of oil price
                "X2": 0.0,  # Annual probability for global oil shock
                "X3": 1.0   # Annual increase of recycling efficiency
            }
        else:
            self.uncertainties = uncertainties

        self.brands = {brand: False for brand in Brand}
        self.nr_of_parts = nr_of_parts
        self.break_down_probability = break_down_probability
        self.std_use_intensity = std_use_intensity

        if agent_counts is None:
            self.agent_counts = {
                PartsManufacturer: 3,
                Refiner: 3,
                Recycler: 1,
                CarManufacturer: len(self.brands),
                User: 1000,
                Garage: 2,
                Dismantler: 1
            }
        else:
            self.agent_counts = agent_counts
            self.agent_counts[CarManufacturer] = len(self.brands)

        self.schedule = StagedActivation(self, stage_list=["get_all_components", "process_components", "update"])
        self.all_agents = self.create_all_agents()
        self.datacollector = DataCollector(model_reporters={
            "amount virgin": self.get_amount_virgin,
            "amount recyclate high": self.get_amount_recyclate_high,
            "amount recyclate low": self.get_amount_recyclate_low,
            "amount reused parts": self.get_amount_reused_parts,
            "amount standard parts": self.get_amount_standard_parts,
            "amount leakage": self.get_amount_of_leakage,
            "price virgin": self.get_price_of_virgin,
            "price recyclate": self.get_price_of_recyclate
        })

    def run(self, steps=50, time_tracking=False):
        """
        Runs the model for a specific amount of steps.
        :param steps: int: number of steps (in years)
        :param time_tracking: Boolean
        :return:
            output: Dataframe: all information that the datacollector gathered

        """

        start_time = time.time()

        for _ in range(steps):
            print(f'Step: {_}')
            self.step()

        if time_tracking:
            run_time = round(time.time() - start_time, 2)
            print(f'Run time: {run_time} seconds')

            print('Simulation completed!')

        results = self.datacollector.get_model_vars_dataframe()
        return results

    def get_next_brand(self):
        for car_manufacturer, exists in self.brands.items():
            if not exists:
                self.brands[car_manufacturer] = True
                return car_manufacturer

    def get_car(self, lifetime_vehicle=10):
        """
        To setup users with cars initially. If the lifetime of the assigned car is zero, it means that the user will
        buy a new car in the first tick. Else its car is assigned a random brand, state, current lifetime and parts.
        :param lifetime_vehicle: int
        :return: car: Car
        """
        brand = self.random.choice(list(Brand))
        lifetime_current = random.randint(0, lifetime_vehicle)
        part_states = self.random.choices(list(PartState), weights=(1, 9), k=self.nr_of_parts)
        parts = [Part(state=state) for state in part_states]

        if lifetime_current == 0:
            car = None
        else:
            if lifetime_current == lifetime_vehicle:
                state = CarState.FUNCTIONING
            else:
                state = self.random.choices(
                    list(CarState)[:2],
                    weights=[self.break_down_probability, 1 - self.break_down_probability])[0]

            car = Car(brand=brand, lifetime_current=lifetime_current, state=state, parts=parts)
        return car

    def create_all_agents(self):
        """
        Create all agents for this model.
        :return: 
            all_agents: dictionary with {Agent: list with this kind of Agents}
        """
        all_agents = {}
        for agent_type, agent_count in self.agent_counts.items():
            for _ in range(agent_count):

                if agent_type is Refiner:
                    externality_factor = self.levers["L4"]
                    shock_probability = self.uncertainties["X2"]
                    annual_price_increase = self.uncertainties["X1"]
                    new_agent = agent_type(self.next_id(), self, all_agents, externality_factor, shock_probability,
                                           annual_price_increase)

                elif agent_type is PartsManufacturer:
                    requirement_high = self.levers["L2"]
                    requirement_low = self.levers["L5"] - requirement_high
                    minimal_requirements = {Component.RECYCLATE_HIGH: requirement_high,
                                            Component.RECYCLATE_LOW: requirement_low}
                    new_agent = agent_type(self.next_id(), self, all_agents, minimal_requirements)

                elif agent_type is CarManufacturer:
                    new_agent = agent_type(self.next_id(), self, all_agents, self.get_next_brand(), self.nr_of_parts,
                                           self.break_down_probability)
                elif agent_type is User:
                    new_agent = self.create_user(all_agents)

                elif agent_type is Garage:
                    minimal_requirement = self.levers["L1"]
                    new_agent = agent_type(self.next_id(), self, all_agents, min_reused_parts=minimal_requirement)

                elif agent_type is Recycler:
                    cohesive_factor = self.levers["L3"]
                    annual_efficiency_increase = self.uncertainties["X3"]
                    new_agent = agent_type(self.next_id(), self, all_agents, annual_efficiency_increase,
                                           cohesive_factor)

                else:
                    """
                    With the current model, in which garages receive cars and repair them in the same tick, I didn't
                    think it would make any sense to initialise garages with cars of users. This would simply mean
                    that there is initially a parts shortage. Not implementing this setup, also means a less 
                    complicated setup procedure.
                    """
                    new_agent = agent_type(self.next_id(), self, all_agents)

                self.schedule.add(new_agent)
                if agent_type in all_agents:
                    all_agents[agent_type].append(new_agent)
                else:
                    all_agents[agent_type] = [new_agent]
        return all_agents

    def create_user(self, all_agents):
        """
        To set up users and assign them cars of which the max_lifetime is based on the intensity of the usage of cars.
        :param all_agents: dictionary with {Agent: list with this kind of Agents}
        :return: new_agent: Agent
        """
        new_agent = User(self.next_id(), self, all_agents, self.get_car(), self.std_use_intensity)
        if new_agent.stock[Component.CARS]:
            new_agent.demand[Component.CARS] = 0
            car = new_agent.stock[Component.CARS][0]
            use_intensity = random.normalvariate(1, self.std_use_intensity)
            use_intensity = max(0.0, use_intensity)

            if use_intensity > 0.0:
                car.max_lifetime = round(
                    car.max_lifetime / use_intensity)  # NOTE: Check whether resulting max_lifetime values make sense

                if car.max_lifetime <= car.lifetime_current:
                    car.lifetime_current = car.max_lifetime

        return new_agent

    def step(self):
        """
        Executes a model step.
        """
        self.schedule.step()
        self.datacollector.collect(self)

    def get_amount_virgin(self):
        """
        Get total amount of VIRGIN plastic in all cars of all users.
        :return:
            amount: float
        """
        amount = self.get_amount_of_plastic(Component.VIRGIN)
        return amount

    def get_amount_recyclate_high(self):
        """
        Get total amount of RECYCLATE_HIGH plastic in all cars of all users.
        :return:
            amount: float
        """
        amount = self.get_amount_of_plastic(Component.RECYCLATE_HIGH)
        return amount

    def get_amount_recyclate_low(self):
        """
        Get total amount of RECYCLATE_LOW plastic in all cars of all users.
        :return:
            amount: float
        """
        amount = self.get_amount_of_plastic(Component.RECYCLATE_LOW)
        return amount

    def get_amount_of_plastic(self, component):
        """
        Get total amount of a specific plastic in all cars of all users.
        :param component: Component in {VIRGIN, RECYCLATE_HIGH, RECYCLATE_LOW}
        :return:
            amount: float
        """
        users = self.all_agents[User]
        amount = 0.0

        for user in users:
            if user.stock[Component.CARS]:
                car = user.stock[Component.CARS][0]
                parts = car.parts
                for part in parts:
                    amount += part.plastic_ratio[component]

        return amount

    def get_amount_reused_parts(self):
        """
        Get total amount of reused parts in all cars of all users.
        :return:
            amount: int
        """
        amount = self.get_amount_of_parts(PartState.REUSED)
        return amount

    def get_amount_standard_parts(self):
        """
        Get total amount of standard parts in all cars of all users.
        :return:
            amount: int
        """
        amount = self.get_amount_of_parts(PartState.STANDARD)
        return amount

    def get_amount_of_parts(self, part_state):
        """
        Get total amount of a specific part in all cars of all users.
        :param part_state: PartState
        :return:
            amount: int
        """
        users = self.all_agents[User]
        amount = 0

        for user in users:
            if user.stock[Component.CARS]:
                car = user.stock[Component.CARS][0]
                parts = car.parts
                for part in parts:
                    if part.state == part_state:
                        amount += 1

        return amount

    def get_amount_of_leakage(self):
        """
        Get total amount of leaked plastic that the recyclers are getting rid off.
        :return:
            amount: float
        """
        amount = 0.0

        recyclers = self.all_agents[Recycler]

        for recycler in recyclers:
            amount += recycler.current_leakage

        return amount

    def get_price_of_virgin(self):
        """
        Get the average price of VIRGIN plastic over all Refiners.
        :return:
            price: float
        """
        refiners = self.all_agents[Refiner]
        prices = []
        for refiner in refiners:
            prices.append(refiner.prices[Component.VIRGIN])

        price = sum(prices) / len(prices)
        return price

    def get_price_of_recyclate(self):
        """
        Get the average price of recyclate plastic over all Recyclers.
        :return:
            price: float
        """

        recyclers = self.all_agents[Recycler]
        prices = []
        for recycler in recyclers:
            price_high = recycler.prices[Component.RECYCLATE_HIGH]
            price_low = recycler.prices[Component.RECYCLATE_LOW]
            prices.append(price_high)
            prices.append(price_low)

        price = sum(prices) / len(prices)
        return price
