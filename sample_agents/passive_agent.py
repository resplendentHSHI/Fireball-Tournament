import random

class Agent:
    def __init__(self):
        self.loads = 0
        self.used_mirror = False

    def play(self, opponent_last_move):
        return 'load'

# create an instance of the agent
agent = Agent()

# define the play function for the tournament to use
def play(opponent_last_move):
    return agent.play(opponent_last_move)
