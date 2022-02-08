"""
This module contains the Experiment class with which all experiments can be run.
"""

from model.cepai_model import *
import pandas as pd
import itertools
import os
from os import listdir
from os.path import isfile, join
import time


class Experiment:
    """
    The Experiment class wraps all features that relate to running an experiment and data collection.
    """

    def __init__(self, uncertainty_values=None, lever_values=None):
        print('Setting up the experiment...\n')
        self.start_time = time.time()

        # Uncertainties
        if uncertainty_values is None:
            self.uncertainty_values = {
                'X1': [1.0, 1.001, 1.01],  # Annual increasing oil price
                'X2': [0.0, 0.001, 0.01],  # Annual probability for a global oil price shock
                'X3': [1.0, 1.001, 1.01],  # Annual increasing recycling efficiency
            }
        else:
            self.uncertainty_values = uncertainty_values

        # Levers
        if lever_values is None:
            self.lever_values = {
                'L1': [0.0, 0.2],  # minimum requirement for reused parts
                'L2': [0.0, 0.2],  # minimum requirement for high-quality recyclate
                'L3': [1.0, 1.2],  # better solvable cohesives
                'L4': [1.0, 1.2],  # externality for virgin plastic
                'L5': [0.0, 0.4],  # minimum requirement for recyclate
            }
        else:
            self.lever_values = lever_values

        self.experimental_conditions = self.prepare_experimental_conditions()

    def prepare_experimental_conditions(self):
        """
        Prepare experimental conditions by creating combinations of all uncertainty and lever values.
        :return:
            experimental_conditions: Dataframe (with column names being X1, ..., X3, L1, ..., L5
        """
        dictionary = {**self.uncertainty_values, **self.lever_values}
        columns = ['X1', 'X2', 'X3', 'L1', 'L2', 'L3', 'L4', 'L5']

        all_values = [dictionary[x] for x in columns]
        rows = list(itertools.product(*all_values))

        experimental_conditions = pd.DataFrame(data=rows, columns=columns)
        return experimental_conditions

    def run(self, n_replications=20, steps=50, n_segments=1, segment_idx=0):
        """
        This function runs the entire experiment with all its variations.
        :param n_replications: int: number of replications per condition
        :param steps: int: length of each run ('years' for which the simulation is run)
        :param n_segments: into how many segments the experimental conditions should be split (distributed runs)
        :param segment_idx: which segment (of experimental conditions) should be run
        """
        print('Running the experiment...\n')

        self.all_results = {}  # {idx of condition: results_of_a_condition}

        # For distributed computation, select conditions
        segment_borders = self.get_segment_borders(n_segments, segment_idx)

        # For printing
        total_length = len(self.experimental_conditions)
        segment_length = math.floor(total_length / n_segments)
        condition_idx = 1

        for idx, row in self.experimental_conditions.iterrows():

            if segment_borders[0] <= idx <= segment_borders[1]:

                if condition_idx % 5 == 0:
                    print(f'Running experimental condition #{condition_idx}/{segment_length}')
                condition_idx += 1

                uncertainties = {
                    'X1': row.loc['X1'],
                    'X2': row.loc['X2'],
                    'X3': row.loc['X3']
                }

                levers = {
                    'L1': row.loc['L1'],
                    'L2': row.loc['L2'],
                    'L3': row.loc['L3'],
                    'L4': row.loc['L4'],
                    'L5': row.loc['L5']
                }

                # Save all output for one condition
                results_for_a_condition = None

                for i in range(n_replications):

                    cepai_model = CEPAIModel(levers=levers, uncertainties=uncertainties)
                    results = cepai_model.run(steps=steps)

                    frames = [results_for_a_condition, results]
                    results_for_a_condition = pd.concat(frames)

                # Save to all results
                self.all_results[idx] = results_for_a_condition

        self.save_results()
        # print(f'Running experimental condition #{segment_length}/{segment_length}')
        print('\nExperiment completed!')

    def get_segment_borders(self, n_segments, segment_idx):
        """
        Calculates the border indices of a segment for distributed computation.
        E.g., if in total, there are 100 conditions and
            n_segments = 10
            segment_idx = 4
            --> borders = (40, 49)
        :param n_segments: into how many segments the experimental conditions should be split (distributed runs)
        :param segment_idx: which segment (of experimental conditions) should be run, starting from 0
        :return: borders: tuple: start and end idx
        """
        total_length = len(self.experimental_conditions)
        segment_length = math.floor(total_length / n_segments)
        start = segment_length * segment_idx
        end = start + (segment_length - 1)
        borders = (start, end)

        return borders

    def save_results(self, folder='./output/'):
        """
        Saves the data of your results in a pickle.
        :param folder: string
        """

        for condition_idx, df in self.all_results.items():
            path = f'{folder}condition_{condition_idx}.csv'
            df.to_csv(path)

    @staticmethod
    def load_results(folder='./output/'):
        """
        Loads the data of two pickles and returns them.
        :param folder: string
        :return:
            results: dictionary with all results
        TODO: Load all CSVs and combine them
        """
        mypath = os.getcwd() + '/output/'
        outputs = [f for f in listdir(mypath) if isfile(join(mypath, f))]

        all_results = {}

        for condition_output in outputs:
            path = f'{folder}{condition_output}'
            df = pd.read_csv(path)

            condition_idx = int(condition_output[10:-4])  # Takes only the number of the condition
            all_results[condition_idx] = df

        return all_results


if __name__ == "__main__":
    """
    Remarks on the experiment:
    - In order to enable distributed computation, we came up with the following.
    - Each of us runs the experiment with several segment_idx values (0-7).
          - Anmol:    0, 1, 2, 3
          - Felicity: 4, 5, 6, 7
          - Max:      8, 9, 10, 11
          - Ryan:     12, 13, 14, 15
    - All remaining parameters stay constant.
    - Data will be saved as CSV files into the directory 'experiments/output'.
    
    Remarks for later data analysis:
    - In 'results.ipynb', you can use the load function as shown which loads all CSV files and re-combines them into
      one dictionary 'all_results'. 
    """
    start_time = time.time()

    experiment = Experiment()
    # TODO: Adjust segment_idx and run this script twice (once for each of your segment_idx')
    experiment.run(n_replications=20, steps=50, n_segments=16, segment_idx=10)

    run_time = round(time.time() - start_time, 2)
    print(f'Run time: {run_time} seconds')
