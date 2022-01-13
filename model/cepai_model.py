"""
This module contains the plastic model which concerns the circular economy of plastic in the automotive industry.
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
                 agent_counts=None,
                 nr_of_parts=4,
                 break_down_probability=0.3,
                 std_use_intensity=0.1):
        """
        :param nr_of_parts: int: how many parts are needed to create a Car object
        :param break_down_probability: float: probability of a car breaking down at any given year
        :param std_use_intensity: float: standard deviation of how intensely a user uses a car
        :param agent_counts: dictionary with {Agent: int}
        """
        print('Simulation starting...')

        super().__init__()
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
                User: 10,
                Garage: 2,
                Dismantler: 1
            }
        else:
            self.agent_counts = agent_counts
            self.agent_counts[CarManufacturer] = len(self.brands)

        self.schedule = StagedActivation(self, stage_list=["get_all_components", "process_components", "update"])
        self.all_agents = self.create_all_agents()
        self.datacollector = DataCollector(model_reporters={})

    def run(self, steps=50, time_tracking=False):
        """
        Runs the model for a specific amount of steps.
        :param steps: int: number of steps (in years)
        """

        start_time = time.time()

        for _ in range(steps):
            self.step()

        if time_tracking:
            run_time = round(time.time() - start_time, 2)
            print(f'Run time: {run_time} seconds')

        print('Simulation completed!')

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
                state = self.random.choices(list(CarState)[:2], weights=[self.break_down_probability,
                                                                         1 - self.break_down_probability])[0]

            car = Car(brand=brand, lifetime_current=lifetime_current, state=state, parts=parts)
        return car

    def create_user(self, agent_type, all_agents):
        """
        To set up users and assign them cars of which the ELV is based on the intensity of the usage of cars.
        :param agent_type: Agent
        :param all_agents: dictionary with {Agent: list with this kind of Agents}
        :return: new_agent: Agent
        """
        new_agent = agent_type(self.next_id(), self, all_agents, self.get_car(), self.std_use_intensity)
        if new_agent.stock[Component.CARS]:
            car = new_agent.stock[Component.CARS][0]
            use_intensity = random.normalvariate(1, self.std_use_intensity)
            use_intensity = max(0.0, use_intensity)

            if use_intensity > 0:
                car.ELV = round(car.ELV / use_intensity)

                if car.ELV < car.lifetime_current:
                    car.lifetime_current = car.ELV

        return new_agent

    def create_all_agents(self):
        """
        Create all agents for this model.
        :return: 
            all_agents: dictionary with {Agent: list with this kind of Agents}
        """
        all_agents = {}
        for agent_type, agent_count in self.agent_counts.items():
            for _ in range(agent_count):
                if agent_type is CarManufacturer:
                    new_agent = agent_type(self.next_id(), self, all_agents, self.get_next_brand(), self.nr_of_parts,
                                           self.break_down_probability)
                elif agent_type is User:
                    new_agent = self.create_user(agent_type, all_agents)

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

    def step(self):
        """
        Executes a model step.
        """
        self.schedule.step()
