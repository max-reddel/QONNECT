# The CEPAI Model

The Circular Economy of Plastic in the Automotive Industry (CEPAI) Model is an agent-based simulation model that concerns the circular economy of plastic in the automotive industry within the Netherlands. 

## Contributors
- Max Reddel
- Felicitas Reddel
- Anmol Soni
- Ryan van der Plas




## Table of Contents
1. [General Remarks](#1-general-remarks)
2. [Current State of the Project](#2-current-state-of-the-project)
3. [Repository Structure](#3-repository-structure)
4. [The CEPAI Model](#4-the-cepai-model)
   1. [Agents](#41-agents)
   2. [Model Flow](#42-model-flow)
   3. [Components](#43-components)
   4. [Cars and Parts](#44-the-composition-of-cars-and-parts)
5. [XLRM Framework](#5-xlrm)
   1. [KPIs](#51-kpis)
   2. [Policies](#52-policies)
   3. [Scenarios](#53-scenarios)
    

## 1. General Remarks

This is a project for the course SEN9120 Advanced Agent Based Modelling (2021/22 Q2) at TU Delft in collaboration with the RIVM.

---

## 2. Current State of the Project

### 2.1 Changes in Stages and Steps

We ran into quite some problems with the two-stage-process of the agents. The potential solutions were not pretty. One such solution would have consisted in creating something like a `MarketAgent` which would take care of determining who gets what components from whom. Additional stages would have been necessary as well for this. To keep the design simple, we went back to square one and created a new design.

Now, the `GenericAgent` has the following three stages:
- `get_all_components()` which gets or buys components from the agent's corresponding suppliers.
- `process_components()` which manufactures, uses, or repairs specific components.
- `update()` which updates the agent's demand for the next instant.

#### Example

Let's say for instance, a `PartsManufacturer` `pm1` is activated. This agent wants first to buy plastic from the `Refiner`s and `Recycler`s. The agent `pm1` will compute its preferences and thus determine to which supplier `pm1` wants to go to first to attempt to buy a specific kind of plastic. Then, it will go through the suppliers according to these preferences. When `pm1` is done with buying all plastic that it demands, it is the turn of the next `PartsManufacturer` `pm2`. When all agents executed the first stage, the second stage starts for all agents. When it is `pm1`'s turn, it will manufacture parts out of plastic (the analogous is the case for all other agents). In the last step, every agent will adjust its demand for the next instant.

### 2.2 Changes in Components

Earlier, we had `PlasticType` where we had `REUSE`, `VIRGIN`, `RECYCLATE_LOW`, and `RECYCLATE_HIGH`. However, we needed to restructure a bit as we also want to include parts and cars. For this purpose, we have now components (see section on [Cars and Parts](#44-the-composition-of-cars-and-parts)).

### 2.3 Changes in Agents (Updated)

1. Add more details to the following agents:
   - `Dismantler`
      - `process_components` method is implemented. It Dismantles the car, reuses the STANDARD parts and adds them to the stock. As per the current version, all every part is reused only once. All the reused parts are sent to the `Recycler`.

         TODO/Suggestion: Add an `efficiency` factor for implementing multiple times REUSE of a part.

      - `get_all_components` and  `get_component_from_suppliers` are updated. Now a `Dismantler` will accept all the cars from the `Garage`.

         TODO: Create a flag if `stock[Component.CARS_FOR_DISMANTLER] == 0`. This can happen if somehow most `Garages` start sending all the cars to `Recyclers`. What should be done in this case? Think about implications?
      - `update()` is implemented along with `adjust_future_prices`. 
         TODO: Test `update()`

   - `Recycler`
      - `process_components` method is implemented. This function extracts the plastic from both `CARS_FOR_SHREDDER` and `DISCARDED_PART`. `efficiency` of the `Recycler` determines how often can a plastic be recycled without degrading its quality. For instance, efficiency of recycler will control if RECYCLATE_HIGH will be recycled as RECYCLATE_HIGH RECYCLATE_LOW. VIRGIN plastic is always recycled as RECYCLATE_HIGH. RECYCLATE_HIGH present in the parts can be converted into RECYCLATE_LOW or RECYCLATE_HIGH depending on the `efficiency`. Similarly, RECYCLATE_LOW can either be discarded or again recycled as RECYCLATE_LOW.

         TODO: Should we implement upcycling (i.e. RECYCLATE_LOW --> RECYCLATE_High)?

         Also, `efficiency` can either be made constant or variable for each tick. What do you think is the best?
      - `get_all_components` and  `get_component_from_suppliers` are updated. Now the `Recycler` will accept all the cars and discarded parts from the `Garage` and `Dismantler` respectively.

      - `update()` is implemented along with `adjust_future_prices`. 
         TODO: Test `update()`

PS: All these implementations are tested and are running as expected. Please let me know if you find a bug or want me to change something.

PSS: I found an additional bug which is quite similar to the problem Ryan faced. If its the same error then please ignore. In the `receive()` of `GenericAgent`, in the last line, the variable `supplies` is a list.  Therefore, `extend` or `+` should be used instead of `append`.

---
## 3. Repository Structure

```
./QONNECT/
├── examples                  # Contains examples on how to run the model
│   ├── simulation.ipynb   
│   └── simulation.py                    
├── images
├── model                                 
│   ├── agents.py             # Contains all agents
│   ├── cepai_model.py        # Contains main model
│   ├── bigger_components.py  # Contains classes for Parts and Cars
│   ├── enumerations.py       # Contains custom-made enumerations (Component, PartState, CarState, Brand)
│   └── preferences.py        # Contains a Preferences class to determine which supplier an agent prefers
└── README.md          
```

The `model` directory contains all model relevant components, including the main model `cepai_model.py`, `agents.py`, `bigger_components`, `enumerations`, and `preferences`. You can run the model by using the notebook `simulation.ipynb` or the script `simulation.py` from the `examples` directory. 

---
## 4. The CEPAI Model

### 4.1 Agents

Every single agent inherits its attributes and methods from `GenericAgent`. A list of these agents is provided in the following table.

(The values in the `Count` column are only suggestions for now.)

| Agent Type          | Count | Description                                                                                                   |
|---------------------|-------|---------------------------------------------------------------------------------------------------------------|
| `User`              | 1000  | A user of a car.                                                                                              |
| `CarManufacturer`   | 4     | A facility that manufatures cars of a specific car brand with brand ϵ {VW, GM, Toyota, Mercedes}.             |
| `PartsManufacturer` | 10    | A facility (= parts manufacturer or original equipment manufacturer) who takes plastic in and produces parts. |
| `Refiner`           | 6    | A facility (= miners and refiners) that produces virgin plastic.                                               |
| `Recycler`          | 1     | A facility (= shredder and post-shredder) that creates recyclate.                                             |
| `Dismantler`        | 1     | A facility that dismantles cars.                                                                              |
| `Garage`            | 20    | A facility that repairs cars or sends them for final processing.                                              |
<figcaption align = "center"><b>Tab.1 - Agents</b></figcaption>


### 4.2 Model Flow 

Figure 1 shows the various agents in this network and how several kinds of components (plastic, parts, and cars) flow through the network.

![image info](images/material_flow.png)
<figcaption align = "center"><b>Fig.1 - Material flow between the agents</b></figcaption>

      TODO: Update the figure: `DISCARDED_PARTS` are sent from Dismantler to Recycler. 

### 4.3 Components

The enumeration `Component` defines that there are different kinds of plastics, but also parts and cars. This comes in handy when dealing with polymorphic methods that handle stock and demand. The table below shows the different values in the first column. For the plastics, it is the case that both data types for stock and demand are floats. We refer here to mass in e.g., kilogram or tonnes. The data types for `PARTS` and `CARS` differs. A `Part` is a custom-made object that consists of a ratio of plastics and a state `PartState` which is either `STANDARD` or `REUSED`. A `Car` consist mainly of a number of `Part`s. So, the stocks for these two components are lists because they contain these objects. Their demand data types are integers, however. **And this has to be adjusted further!** 

Currenlty, everything works. But for `PARTS` and `CARS`, it's a simple way of just stating how many parts and how many cars an agent wants/demands. We need to discuss how we want to proceed here.

| Component        | Stock Data Type | Demand Data Type |
|------------------|-----------------|------------------|
| `VIRGIN`         | float           | float            |
| `RECYCLATE_LOW`  | float           | float            |
| `RECYCLATE_HIGH` | float           | float            |
| `PARTS`          | list            | int              |
| `CARS`           | list            | int              |
| `DISCARDED_PARTS`| list            | int              |
| `CARS_FOR_DISMANTLER`| list        | int              |
| `CARS_FOR_SHREDDER`| list          | int              |
<figcaption align = "center"><b>Tab.2 - Components and their data types</b></figcaption>

### 4.4 The Composition of Cars and Parts

Figure 2 shows what an instance of the `Car` class can look like. Additionally, we can see what a `Part` consists of. The number of parts can of course still be adjusted. 

![image info](images/car.png)
<figcaption align = "center"><b>Fig.2 -The composition of cars and parts</b></figcaption>


## 5. XLRM

The XLRM framework describes the analysis of a model by distinguishing:
- X: Uncertainty variables which define the Scenarios
- L: Lever varaibles which define the policies or solutions
- R: Relations which describe the inner working of the model
- M: Metrics which define the key performance indicators (KPIs)

The following sub-sections describe X, L, and M in more detail. An overview is provided here:

![image info](images/xlrm.png)
<figcaption align = "center"><b>Fig.3 -The XLRM framework applied to the CEPAI model</b></figcaption>

### 5.1 Metrics
### 5.2 Levers
### 5.3 Uncertainties
