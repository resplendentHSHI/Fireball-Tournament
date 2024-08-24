import importlib
import os
import sys
import time
import json

MOVES = ['shield', 'load', 'fireball', 'tsunami', 'mirror']
OUTPUT_FILE = 'tournament_output.txt'
PROGRESS_FILE = 'tournament_progress.json'

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
        write_output(f"{self.agent1.__class__.__name__} vs {self.agent2.__class__.__name__}: {move1} vs {move2}")

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
                write_output(f"{self.agent1.__class__.__name__} wins!")
                break
            elif winner == 1:
                score2 += 1
                write_output(f"{self.agent2.__class__.__name__} wins!")
                break
            last_move1, last_move2 = move1, move2
        else:
            score1 += 1.1
            score2 += 1.1
            write_output("Draw!")

        return score1, score2

def write_output(message):
    with open(OUTPUT_FILE, 'a') as f:
        f.write(message + '\n')

def update_progress(current, total):
    progress = {
        'current': current,
        'total': total,
        'percentage': (current / total) * 100
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    open(OUTPUT_FILE, 'w').close()
    open(PROGRESS_FILE, 'w').close()

    agent_files = [f for f in os.listdir('.') if f.endswith('_agent.py')]
    agent_classes = {}

    write_output("Loading agents...")
    for agent_file in agent_files:
        module_name = agent_file[:-3]
        module = importlib.import_module(module_name)
        agent_classes[module_name] = module.Agent
        write_output(f"Loaded: {module_name}")

    scores = {agent_name: 0 for agent_name in agent_classes.keys()}
    write_output(f"Loaded {len(agent_classes)} agents.")

    agent_names = list(agent_classes.keys())
    total_matches = len(agent_names) * (len(agent_names) - 1) * 100
    matches_played = 0

    write_output("\nStarting tournament...")
    for i, agent_name1 in enumerate(agent_names):
        for j, agent_name2 in enumerate(agent_names):
            if i != j:
                write_output(f"\nMatch: {agent_name1} vs {agent_name2}")
                for k in range(100):
                    match = Match(agent_classes[agent_name1](), agent_classes[agent_name2]())
                    score1, score2 = match.run()
                    scores[agent_name1] += score1
                    scores[agent_name2] += score2
                    matches_played += 1
                    update_progress(matches_played, total_matches)
                    write_output(f"Progress: {matches_played}/{total_matches} matches completed")
                    time.sleep(0.01)  # Small delay to allow for smoother output

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    write_output("\nTournament Results:")
    for agent_name, score in sorted_scores:
        write_output(f"{agent_name}: {score} points")

if __name__ == '__main__':
    main()