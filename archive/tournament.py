import importlib.util
import os
import sys

MOVES = ['shield', 'load', 'fireball', 'tsunami', 'mirror']

class Match:
    def __init__(self, agent1, agent2):
        self.agent1 = agent1
        self.agent2 = agent2
        self.loads1 = 0
        self.loads2 = 0
        self.mirror1 = True
        self.mirror2 = True

    def validate_move(self, move, loads, mirrorStatus):
        if move == 'fireball' and loads < 1:
            return 'load'
        if move == 'tsunami' and loads < 2:
            return 'load'
        if move == 'mirror' and not mirrorStatus:
            return 'load'
        if move not in MOVES:
            return 'load'
        return move

    def determine_winner(self, move1, move2):
        if move1 == move2:
            return None  # Draw
        if move1 == 'fireball':
            if move2 in ['load']:
                return 0
            elif move2 in ['mirror']:
                return 1
        if move1 == 'tsunami':
            if move2 in ['load', 'shield']:
                return 0
            elif move2 in ['mirror']:
                return 1
        if move1 == 'mirror':
            if move2 in ['fireball', 'tsunami']:
                return 0
        if (move2 == 'fireball' or move2 == 'tsunami') and move1 == 'load':
            return 1
        return None  # Draw

    def run_round(self, last_move1, last_move2):
        move1 = self.agent1.play(last_move2)
        move2 = self.agent2.play(last_move1)

        move1 = self.validate_move(move1, self.loads1, self.mirror1)
        move2 = self.validate_move(move2, self.loads2, self.mirror2)

        if move1 == 'load':
            self.loads1 += 1
        if move2 == 'load':
            self.loads2 += 1
        if move1 == 'fireball':
            self.loads1 -= 1
        if move2 == 'fireball':
            self.loads2 -= 1
        if move1 == 'tsunami':
            self.loads1 -= 2
        if move2 == 'tsunami':
            self.loads2 -= 2
        if move1 == 'mirror':
            self.mirror1 = False
        if move2 == 'mirror':
            self.mirror2 = False

        winner = self.determine_winner(move1, move2)
        return winner, move1, move2

    def run(self, rounds=100):
        score1, score2 = 0, 0
        last_move1, last_move2 = None, None

        for _ in range(rounds):
            winner, move1, move2 = self.run_round(last_move1, last_move2)
            if winner == 0:
                score1 += 1
                break
            elif winner == 1:
                score2 += 1
                break
            last_move1, last_move2 = move1, move2
        else:
            score1 += 0.5
            score2 += 0.5

        return score1, score2

def load_agent(agent_name):
    spec = importlib.util.spec_from_loader(agent_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    with open(f'{agent_name}_agent.py', 'r') as file:
        exec(file.read(), module.__dict__)
    return module.Agent()

def main(agent_names):
    agent_classes = {name: load_agent(name) for name in agent_names}
    scores = {agent_name: 0 for agent_name in agent_classes.keys()}

    for i, agent_name1 in enumerate(agent_names):
        for j, agent_name2 in enumerate(agent_names):
            if i != j:
                for _ in range(100):  # Run 100 matches for each pair
                    match = Match(agent_classes[agent_name1], agent_classes[agent_name2])
                    score1, score2 = match.run()
                    scores[agent_name1] += score1
                    scores[agent_name2] += score2

                # Reset agents after each set of matches
                agent_classes[agent_name1] = load_agent(agent_name1)
                agent_classes[agent_name2] = load_agent(agent_name2)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # print the results
    print("Tournament Results:")
    for agent_name, score in sorted_scores:
        print(f"{agent_name}: {score}")

if __name__ == '__main__':
    agent_names = sys.argv[1:]  # Get agent names from command-line arguments
    main(agent_names)