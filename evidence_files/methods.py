'''This script has functions used for data reporting and plotting graphs in the evidence files'''

import collections
import pandas as pd
import matplotlib.pyplot as plt


def plot_results(results):
    """
    Plots the line plots for the model outputs
    """
    fig, axs = plt.subplots(3, 3, sharex= True, sharey= False, figsize=(10,10))
    columns = results.columns
    i = 0
    for x in range(0,3):
        for y in range(0,3):
            column = columns[i]
            axs[x,y].plot(results[column])
            axs[x,y].set_title(column)
            axs[x,y].set_xlabel('steps')
            i+=1

def get_stocks(agent):
    agent_stocks = {}

    for comp, stocks in agent.stock.items():
        if isinstance(stocks, (float or int)):
            agent_stocks[comp] = stocks
        elif isinstance(stocks, list):
            agent_stocks[comp] = len(stocks)

    return agent_stocks