"""
This module contains the Experiment class with which all experiments can be run.
"""

from model.cepai_model import *
import pandas as pd
import itertools
import pickle


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

    def run(self, n_replications=20, steps=50):
        """
        This function runs the entire experiment with all its variations.
        """
        print('Running the experiment...\n')

        self.all_results = {}  # {idx of condition: results_of_a_condition}

        for idx, row in self.experimental_conditions.iterrows():

            if idx % 10 == 0 and not idx == 0:
                print(f'Condition #{idx}/{len(self.experimental_conditions)}')

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
                'L5': row.loc['L5'],
            }

            # Save all output for one condition
            results_for_a_condition = {}  # {replication_number: output}

            for i in range(n_replications):

                cepai_model = CEPAIModel(levers=levers, uncertainties=uncertainties)
                results = cepai_model.run(steps=steps)
                results_for_a_condition[i+1] = results

            # Save to all results
            self.all_results[idx] = results_for_a_condition

            # To execute a quick test
            if idx == 20:
                break

        self.save_results()

    def save_results(self, folder='./output/'):
        """
        Saves the data of your results in a pickle.
        :param folder:
        """
        # with open(f'{folder}results.csv', 'w') as handle:
        data = pd.DataFrame.from_dict(self.all_results)
        data.to_pickle(f'{folder}results.pickle')

    @staticmethod
    def load_results(folder='./output/'):
        """
        Loads the data of two pickles and returns them.
        :param folder:

        :return:
            results: dictionary with all results
        """
        # with open(f'{folder}results.csv', 'r') as handle:
        results = pd.read_pickle(f'{folder}results.pickle')

        return results


if __name__ == "__main__":
    experiment = Experiment()
    experiment.run(n_replications=1, steps=1)
