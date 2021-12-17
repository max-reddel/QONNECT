"""
This module contains the plastic model which concerns the circular economy of plastic in the automotive industry.
"""

from mesa import Model
from mesa.time import RandomActivation
from model.agents import *


class CEPAIModel(Model):
    """
    The model which concerns the circular economy of plastic in the automotive industry.
    """

    def __init__(self, agent_counts=None):
        """
        :param agent_counts: dictionary with {Agent: int}
        """
        print('Simulation starting...')
        super().__init__()
        self.brands = {brand: False for brand in Brand}

        if agent_counts is None:
            self.agent_counts = {
                PartsManufacturer: 3,
                Refiner: 3,
                Recycler: 2,
                CarManufacturer: len(self.brands),
                User: 1
            }
        else:
            self.agent_counts = agent_counts
            self.agent_counts[CarManufacturer] = len(self.brands)

        # Separate schedules for diffenent agent types
        self.schedules = {agent_type: RandomActivation(self) for agent_type in GenericAgent.__subclasses__()}
        self.schedule_order = [User, CarManufacturer, PartsManufacturer, Refiner, Recycler, Dismantler, Garage]

        self.all_agents = self.create_all_agents()

    def run(self, steps=50):
        """
        Runs the model for a specific amount of steps.
        :param steps: int: number of steps (in years)
        """
        for _ in range(steps):
            self.step()
        print('Simulation completed!')

    def get_next_brand(self):
        for car_manufacturer, exists in self.brands.items():
            if not exists:
                self.brands[car_manufacturer] = True
                return car_manufacturer

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
                    new_agent = agent_type(self.next_id(), self, all_agents, self.get_next_brand())
                else:
                    new_agent = agent_type(self.next_id(), self, all_agents)
                self.schedules[agent_type].add(new_agent)
                if agent_type in all_agents:
                    all_agents[agent_type].append(new_agent)
                else:
                    all_agents[agent_type] = [new_agent]
        return all_agents

    def step(self):
        """
        Executes a model step.
        """
        for agent_type in self.schedule_order:
            self.schedules[agent_type].step()
