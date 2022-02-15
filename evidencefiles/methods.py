"""This script has functions used for data reporting and plotting graphs in the evidence files."""


import matplotlib.pyplot as plt
import collections
# import pandas as pd
# import math
from model.cepai_model import *


def plot_results(results):
    """
    Plots the line plots for the model outputs
    :param results: dictionary
    """
    fig, axs = plt.subplots(3, 3, sharex='True', sharey='False', figsize=(10, 10))
    columns = results.columns
    i = 0
    for x in range(0, 3):
        for y in range(0, 3):
            column = columns[i]
            axs[x, y].plot(results[column])
            axs[x, y].set_title(column)
            axs[x, y].set_xlabel('steps')
            i += 1


def get_stocks(agent):
    """
    :param agent: Agent
    :return: agent_stocks: dictionary
    """
    agent_stocks = {}

    for comp, stocks in agent.stock.items():
        if isinstance(stocks, (float or int)):
            agent_stocks[comp] = stocks
        elif isinstance(stocks, list):
            agent_stocks[comp] = len(stocks)

    return agent_stocks


def micro_validation(levers, uncertainities, steps=10):
    """"
    Performs micro validation using levers and uncertainties for given steps and plots agent stocks.
    This function is taken from the calibration notebook and adapted for validation.
    :param levers: dictionary
    :param uncertainities: dictionary
    :param steps: int
    """
    model = CEPAIModel(levers=levers, uncertainties=uncertainities)

    data = []
    for _ in range(steps):
        """
        Collect every step of the model the values for stocks and demands of all agent classes except users and 
        refiners and save them in a Pandas dataframe.
        """
        # Garages, check both demand and stock
        for i, garage in enumerate(model.all_agents[Garage]):
            if i == 0:
                garage_stocks = get_stocks(garage)
                garage_demands = garage.demand
            else:
                garage_stock_to_add = get_stocks(garage)
                garage_stocks = dict(collections.Counter(garage_stocks) + collections.Counter(garage_stock_to_add))
                garage_demands = dict(collections.Counter(garage_demands) + collections.Counter(garage.demand))

            garage_stocks = {k: v / i for k, v in garage_stocks.items()}
            garage_demands = {k: v / i for k, v in garage_demands.items()}

        # Parts manufacturers, check both demand and stock
        for i, PM in enumerate(model.all_agents[PartsManufacturer]):
            if i == 0:
                PM_stocks = get_stocks(PM)
                PM_demands = PM.demand
            else:
                PM_stock_to_add = get_stocks(PM)
                PM_stocks = dict(collections.Counter(PM_stocks) + collections.Counter(PM_stock_to_add))
                PM_demands = dict(collections.Counter(PM_demands) + collections.Counter(PM.demand))

            PM_stocks = {k: v / i for k, v in PM_stocks.items()}
            PM_demands = {k: v / i for k, v in PM_demands.items()}

        # Car manufacturers, check both demand and stock
        for i, CM in enumerate(model.all_agents[CarManufacturer]):
            if i == 0:
                CM_stocks = get_stocks(CM)
                CM_demands = CM.demand
            else:
                CM_stock_to_add = get_stocks(CM)
                CM_stocks = dict(collections.Counter(CM_stocks) + collections.Counter(CM_stock_to_add))
                CM_demands = dict(collections.Counter(CM_demands) + collections.Counter(CM.demand))

            CM_stocks = {k: v / i for k, v in CM_stocks.items()}
            CM_demands = {k: v / i for k, v in CM_demands.items()}

        # Dismantlers, check stock
        for i, dismantler in enumerate(model.all_agents[Dismantler]):
            if i == 0:
                dismantler_stocks = get_stocks(dismantler)
            else:
                dismantler_stock_to_add = get_stocks(dismantler)
                dismantler_stocks = dict(
                    collections.Counter(dismantler_stocks) + collections.Counter(dismantler_stock_to_add))

            garage_stocks = {k: v / i for k, v in dismantler_stocks.items()}

        # Recyclers, check stock
        for i, recycler in enumerate(model.all_agents[Recycler]):
            if i == 0:
                recycler_stocks = get_stocks(recycler)
            else:
                recycler_stock_to_add = get_stocks(recycler)
                recycler_stocks = dict(
                    collections.Counter(recycler_stocks) + collections.Counter(recycler_stock_to_add))

            recycler_stocks = {k: v / i for k, v in recycler_stocks.items()}

        # Update the dataframes
        update_list = [garage_stocks, garage_demands, PM_stocks, PM_demands, CM_stocks, CM_demands, dismantler_stocks,
                       recycler_stocks]
        data.append(update_list)

        # And advance the model one step again.
        model.step()

    columns = ['Garage_stock', 'Garage_demand',
               'PartsManufacturer_stock', 'PartsManufacturer_demand',
               'CarManufacturer_stock', 'CarManufacturer_demand',
               'Dismantler_stock',
               'Recycler_stock']
    stock_and_demand_df = pd.DataFrame(data=data, columns=columns)

    index = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4],
             [1, 0], [1, 1], [1, 2], [1, 3], [1, 4],
             [2, 0], [2, 1], [2, 2], [2, 3], [2, 4],
             [3, 0], [3, 1], [3, 2], [3, 3], [3, 4],
             [4, 0], [4, 1], [4, 2], [4, 3], [4, 4]]
    fig, axs = plt.subplots(5, 5, sharex=True, sharey=False, figsize=(15, 15))
    _ = 0
    for column in stock_and_demand_df:
        dictionary = stock_and_demand_df[column].iloc[0]
        relevant = []

        for k, v in dictionary.items():
            if round(v) > 0.0:
                relevant.append(k)

        dictionary_relevant = {k: dictionary[k] for k in relevant}
        for component in dictionary_relevant.keys():
            x = list(stock_and_demand_df.index)
            data_list = []
            for step in x:
                data_list.append(stock_and_demand_df[column].iloc[step][component])

            i, j = index[_]
            _ += 1
            axs[i, j].plot(x, data_list)
            axs[i, j].set_title(column)
            axs[i, j].set_xlabel('steps')
            axs[i, j].set_xlabel(component)
