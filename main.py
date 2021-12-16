from model.plastic_model import *

model = PlasticModel()
car_manufactuers = model.all_agents[CarManufacturer]
for i in range(1):
    model.step()

print()