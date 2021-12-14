"""
This module contains the plastic model which concerns the circular economy of plastic in the automotive industry.
"""

from mesa import Model
from mesa.time import StagedActivation
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

        if agent_counts is None:
            self.agent_counts = {PartsManufacturer: 3, MinerRefiner: 3, Shredder: 2}
        else:
            self.agent_counts = agent_counts

        self.id_counter = 0
        self.schedule = StagedActivation(self, stage_list=["offer_preferences", "satisfy_preferences"])
        self.all_agents = self.create_all_agents()

    def create_all_agents(self):
        """
        Create all agents for this model.
        :return: 
            all_agents: dictionary with {GenericAgent: list of this kind of agent}
        """
        all_agents = {}
        for agent, agent_count in self.agent_counts.items():
            for _ in range(agent_count):
                new_agent = agent(self.get_new_id(), self, all_agents)
                self.schedule.add(new_agent)
                if agent in all_agents:
                    all_agents[agent].append(new_agent)
                else:
                    all_agents[agent] = [new_agent]
        return all_agents

    def get_new_id(self):
        """
        Returns a new unique ID for agents.
        :return:
            self.id_counter: int
        """
        self.id_counter += 1
        return self.id_counter - 1

    def step(self):
        """
        Executes a model step.
        """
        self.schedule.step()
        print(f'Model step.')
