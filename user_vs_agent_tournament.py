import importlib
import os

MOVES = ['shield', 'load', 'fireball', 'tsunami', 'mirror']

class Match:
    def __init__(self, agent):
        self.agent = agent
        self.user_loads = 0
        self.agent_loads = 0
        self.user_mirror = True
        self.agent_mirror = True
        self.match_log = []

    def validate_move(self, move, loads, mirror_status):
        if move == 'fireball' and loads < 1:
            return 'load'
        if move == 'tsunami' and loads < 2:
            return 'load'
        if move == 'mirror' and not mirror_status:
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
        if (move2 == 'fireball' or move2 == 'tsunami') and move1 in 'load':
            return 1
        if (move1 == 'shield') and move2 == 'tsunami':
            return 1
        return None  # Draw

    def run_round(self, user_move, last_agent_move):
        agent_move = self.agent.play(last_agent_move)

        user_move = self.validate_move(user_move, self.user_loads, self.user_mirror)
        agent_move = self.validate_move(agent_move, self.agent_loads, self.agent_mirror)
        
        round_result = f"User vs {self.agent.__class__.__name__}: {user_move} vs {agent_move}"
        self.match_log.append(round_result)
        print(round_result)

        if user_move == 'load':
            self.user_loads += 1
        if agent_move == 'load':
            self.agent_loads += 1
        if user_move == 'fireball':
            self.user_loads -= 1
        if agent_move == 'fireball':
            self.agent_loads -= 1
        if user_move == 'tsunami':
            self.user_loads -= 2
        if agent_move == 'tsunami':
            self.agent_loads -= 2
        if user_move == 'mirror':
            self.user_mirror = False
        if agent_move == 'mirror':
            self.agent_mirror = False

        winner = self.determine_winner(user_move, agent_move)

        return winner, user_move, agent_move

def load_agent(agent_file):
    module_name = agent_file[:-3]
    module = importlib.import_module(module_name)
    return module.Agent()

def main():
    print("Welcome to the User vs Agent Tournament!")
    
    # List available agents
    agent_files = [f for f in os.listdir('.') if f.endswith('_agent.py')]
    print("\nAvailable agents:")
    for i, agent_file in enumerate(agent_files, 1):
        print(f"{i}. {agent_file[:-3]}")
    
    # Let user choose an agent
    while True:
        try:
            choice = int(input("\nChoose an agent to play against (enter the number): "))
            if 1 <= choice <= len(agent_files):
                chosen_agent = load_agent(agent_files[choice - 1])
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    match = Match(chosen_agent)
    user_score, agent_score = 0, 0
    last_user_move = None
    last_agent_move = None

    print("\nLet the tournament begin!")
    print("Valid moves are: shield, load, fireball, tsunami, mirror")
    print("The game starts with no previous moves.")

    for round_num in range(1, 101):  # 100 rounds
        print(f"\nRound {round_num}")
        print(f"Your loads: {match.user_loads}, Agent loads: {match.agent_loads}")
        print(f"Your mirror available: {match.user_mirror}, Agent mirror available: {match.agent_mirror}")
        
        while True:
            user_move = input("Enter your move: ").lower()
            if user_move in MOVES:
                break
            print("Invalid move. Please try again.")

        winner, last_user_move, last_agent_move = match.run_round(user_move, last_user_move)

        if winner == 0:
            user_score += 1
            print("You win this round!")
            break
        elif winner == 1:
            agent_score += 1
            print("Agent wins this round!")
            break

    print("\nTournament Results:")
    print(f"Your score: {user_score}")
    print(f"Agent score: {agent_score}")

    if user_score > agent_score:
        print("Congratulations! You win the tournament!")
    elif user_score < agent_score:
        print("The agent wins the tournament. Better luck next time!")
    else:
        print("It's a tie!")

if __name__ == '__main__':
    main()