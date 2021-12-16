"""
This module contains the plastic model which concerns the circular economy of plastic in the automotive industry.
"""

from mesa import Model
from mesa.time import RandomActivation
from model.agents import *


class PlasticModel(Model):
    """
    The model which concerns the circular economy of plastic in the automotive industry.
    """

    def __init__(self, agent_counts=None):
        """
        :param agent_counts: dictionary with {Agent: int}
        """
        super().__init__()

        self.car_manufacturers = {x: False for x in Brand}

        self.model_step_counter = 0
        if agent_counts is None:
            self.agent_counts = {
                PartsManufacturer: 3,
                Refiner: 3,
                PostShredder: 2,
                CarManufacturer: 4,
                FakeUser: 2
            }
        else:
            self.agent_counts = agent_counts

        self.schedule = RandomActivation(self)
        self.all_agents = self.create_all_agents()

    def get_next_brand(self):
        try:
            for car_manufacturer, exists in self.car_manufacturers.items():
                if not exists:
                    self.car_manufacturers[car_manufacturer] = True
                    return car_manufacturer
        except ValueError:
            raise "You want to create too many brands for CarManufacturers. Your number should be smaller than 4!"

    def create_all_agents(self):
        """
        Create all agents for this model.
        :return: 
            all_agents: dictionary with {Agent: list with this kind of Agents}
        """
        all_agents = {}
        for agent, agent_count in self.agent_counts.items():
            for _ in range(agent_count):
                if agent is CarManufacturer:
                    new_agent = agent(self.next_id(), self, all_agents, self.get_next_brand())
                else:
                    new_agent = agent(self.next_id(), self, all_agents)
                self.schedule.add(new_agent)
                if agent in all_agents:
                    all_agents[agent].append(new_agent)
                else:
                    all_agents[agent] = [new_agent]
        return all_agents

    def step(self):
        """
        Executes a model step.
        """
        self.schedule.step()
        # print(f'Model step #{self.model_step_counter}')
        self.model_step_counter += 1
