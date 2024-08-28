import random

class Agent:
    def __init__(self):
        self.loads = 0  # Keeps track of energy points
        self.used_mirror = False  # Tracks if mirror has been used

    def play(self, opponent_last_move):
        # Use mirror if opponent used fireball or tsunami and mirror hasn't been used yet
        if opponent_last_move in ['fireball', 'tsunami'] and not self.used_mirror:
            self.used_mirror = True
            return 'mirror'

        # Use tsunami if we have enough energy
        if self.loads >= 2:
            self.loads -= 2
            return 'tsunami'
        
        # If we have 1 energy, decide between loading more or using fireball
        elif self.loads == 1:
            if random.random() < 0.7:  # 70% chance to load more
                self.loads += 1
                return 'load'
            else:
                self.loads -= 1
                return 'fireball'
        
        # If we don't have energy, either load or shield
        else:
            if random.random() < 0.8:  # 80% chance to load
                self.loads += 1
                return 'load'
            else:
                return 'shield'

# Create an instance of the agent
agent = Agent()

# Define the play function for the tournament to use
def play(opponent_last_move):
    return agent.play(opponent_last_move)

