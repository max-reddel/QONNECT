"""
This module is used to run a simple simulation.
"""

from model.cepai_model import *

if __name__ == "__main__":

    levers = {
        "L1": 0.1,  # Minimal requirement for reused parts
        "L2": 0.1,  # Minimal requirement for high-quality plastic
        "L3": 1.0,  # Use better solvable cohesives
        "L4": 1.0,  # Include externality for virgin plastic
        "L5": 0.3  # Minimal requirement for recyclate
    }

    uncertainties = {
        "X1": 1.0,  # Annual increase factor of oil price
        "X2": 0.0,  # Annual probability for global oil shock
        "X3": 1.0  # Annual increase of recycling efficiency
    }

    model = CEPAIModel(levers, uncertainties)
    model.run(steps=50, time_tracking=True)
