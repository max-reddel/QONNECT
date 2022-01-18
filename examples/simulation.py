"""
This module is used to run a simple simulation.
"""

from model.cepai_model import *

if __name__ == "__main__":

    levers = {"L1: Minimal requirement for reused parts": 0.2,
              "L2: Minimal requirement for high-quality plastic": 0.2,
              "L3: Use better solvable cohesives": 1.0,
              "L4: Include externality for virgin plastic": 1.1,
              "L5: Minimal requirement for recyclate": 0.4
              }

    uncertainties = {"X1: Annual increase factor of oil price": 1.0,
                     "X2: Annual probability for global oil shock": 0.0,
                     "X3: Annual increase of recycling efficiency": 1.01
                     }

    model = CEPAIModel(levers, uncertainties)
    model.run(steps=50, time_tracking=True)
