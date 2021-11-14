from mesa import Agent


class SimpleAgent(Agent):
    """ An agent with fixed initial wealth."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        print(f'Step by agent #{self.unique_id}.')
