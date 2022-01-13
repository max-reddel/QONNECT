"""
This module is used to run a simple simulation.
"""

from model.cepai_model import *

if __name__ == "__main__":
    model = CEPAIModel()
    model.run(steps=50, time_tracking=True)
