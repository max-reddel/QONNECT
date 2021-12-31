from model.cepai_model import *

if __name__ == "__main__":
    model = CEPAIModel(agent_counts={
                PartsManufacturer: 3,
                Refiner: 3,
                Recycler: 2,
                CarManufacturer: 4,
                User: 10,
                Garage: 2,
                Dismantler: 1
            })

    model.run(steps=50)
