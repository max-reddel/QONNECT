from model.cepai_model import *

if __name__ == "__main__":
    # model = CEPAIModel(agent_counts={User: 10})
    model = CEPAIModel()

    model.run(steps=50)
