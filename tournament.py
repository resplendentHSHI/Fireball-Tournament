import importlib
import os
import sys
import time
import json
import concurrent.futures
import threading

MOVES = ['shield', 'load', 'fireball', 'tsunami', 'mirror']
OUTPUT_FILE = 'tournament_output.txt'
PROGRESS_FILE = 'tournament_progress.json'
MATCH_FOLDER = 'match_results'

# Thread-safe writing to output file
output_lock = threading.Lock()
def write_output(message):
    with output_lock:
        with open(OUTPUT_FILE, 'a') as f:
            f.write(message + '\n')

# Thread-safe progress update
progress_lock = threading.Lock()
def update_progress(current, total):
    with progress_lock:
        progress = {
            'current': current,
            'total': total,
            'percentage': (current / total) * 100
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f)

class Match:
    def __init__(self, agent1, agent2):
        self.agent1 = agent1
        self.agent2 = agent2
        self.loads1 = 0
        self.loads2 = 0
        self.mirror1 = True
        self.mirror2 = True
        self.match_log = []

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
        if (move2 == 'fireball' or move2 == 'tsunami') and move1 in ['load']:
            return 1
        if (move1 == 'shield') and move2 == 'tsunami':
            return 1
        return None  # Draw

    def run_round(self, last_move1, last_move2):
        move1 = self.agent1.play(last_move2)
        move2 = self.agent2.play(last_move1)

        move1 = self.validate_move(move1, self.loads1, self.mirror1)
        move2 = self.validate_move(move2, self.loads2, self.mirror2)
        round_result = f"{self.agent1.__class__.__name__} vs {self.agent2.__class__.__name__}: {move1} vs {move2}"
        self.match_log.append(round_result)
        write_output(round_result)

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
                result = f"{self.agent1.__class__.__name__} wins!"
                self.match_log.append(result)
                write_output(result)
                break
            elif winner == 1:
                score2 += 1
                result = f"{self.agent2.__class__.__name__} wins!"
                self.match_log.append(result)
                write_output(result)
                break
            last_move1, last_move2 = move1, move2
        else:
            score1 += 1.1
            score2 += 1.1
            result = "Draw!"
            self.match_log.append(result)
            write_output(result)

        return score1, score2

def run_match_series(agent_class1, agent_class2, num_matches=100):
    total_score1, total_score2 = 0, 0
    agent1_name = agent_class1.__module__
    agent2_name = agent_class2.__module__
    match_folder = os.path.join(MATCH_FOLDER, f"{agent1_name}_vs_{agent2_name}")
    os.makedirs(match_folder, exist_ok=True)

    for match_num in range(num_matches):
        match = Match(agent_class1(), agent_class2())
        score1, score2 = match.run()
        total_score1 += score1
        total_score2 += score2

        # Save individual match result
        match_file = os.path.join(match_folder, f"match_{match_num+1}.txt")
        with open(match_file, 'w') as f:
            f.write(f"{agent1_name} vs {agent2_name}\n")
            f.write("\n".join(match.match_log))
            f.write(f"\nFinal Score: {score1} - {score2}\n")

    return total_score1, total_score2

def main():
    open(OUTPUT_FILE, 'w').close()
    open(PROGRESS_FILE, 'w').close()
    os.makedirs(MATCH_FOLDER, exist_ok=True)

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
    total_matches = len(agent_names) * (len(agent_names) - 1)
    matches_played = 0

    write_output("\nStarting tournament...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_match = {}
        for i, agent_name1 in enumerate(agent_names):
            for j, agent_name2 in enumerate(agent_names):
                if i != j:
                    future = executor.submit(run_match_series, agent_classes[agent_name1], agent_classes[agent_name2])
                    future_to_match[future] = (agent_name1, agent_name2)

        for future in concurrent.futures.as_completed(future_to_match):
            agent_name1, agent_name2 = future_to_match[future]
            try:
                score1, score2 = future.result()
                scores[agent_name1] += score1
                scores[agent_name2] += score2
                matches_played += 1
                update_progress(matches_played, total_matches)
                write_output(f"Match completed: {agent_name1} vs {agent_name2}")
                write_output(f"Progress: {matches_played}/{total_matches} matches completed")
            except Exception as exc:
                import traceback
                error_msg = f"""
        Error in match between {agent_name1} and {agent_name2}:
        Exception type: {type(exc).__name__}
        Exception message: {str(exc)}
        Traceback:
        {traceback.format_exc()}
        """
                write_output(error_msg)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    write_output("\nTournament Results:")
    for agent_name, score in sorted_scores:
        write_output(f"{agent_name}: {score} points")

if __name__ == '__main__':
    main()
