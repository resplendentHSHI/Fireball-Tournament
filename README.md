# Agent Tournament

This project implements a tournament system for AI agents that play a strategic game. Agents compete against each other in a round-robin tournament, with their performance recorded and displayed on a leaderboard.

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Creating an Agent](#creating-an-agent)
- [Game Rules](#game-rules)
- [Tournament System](#tournament-system)
- [Web Interface](#web-interface)
- [Contributing](#contributing)

## Overview

The Agent Tournament is a Flask-based web application that allows users to submit AI agents, run tournaments, and view results. Agents compete in a game where they must choose between different moves (shield, load, fireball, tsunami, mirror) in a strategic manner.

## Project Structure

- `app.py`: Main Flask application
- `tournament.py`: Tournament logic and execution
- `base.html`: Base template for web pages
- `index.html`: Leaderboard and tournament control page
- `submit.html`: Page for submitting new agents
- `edit.html`: Page for editing existing agents
- `*_agent.py`: Individual agent implementations (e.g., `dj_agent.py`, `passive_agent.py`)

## Setup

1. Ensure you have Python 3.7+ installed.
2. Install required packages:
   ```
   pip install flask flask_sqlalchemy
   ```
3. Initialize the database:
   ```python
   from app import app, db
   with app.app_context():
       db.create_all()
   ```

## Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```
2. Open a web browser and navigate to `http://localhost:5000`

## Creating an Agent

To create a new agent:

1. Navigate to the "Submit Agent" page.
2. Enter a unique name for your agent.
3. Implement the `play` method in the provided code editor.
4. Click "Submit" to add your agent to the tournament.

Example agent implementation:

```python
class Agent:
    def __init__(self):
        self.loads = 0
        self.used_mirror = False

    def play(self, opponent_last_move):
        # Implement your strategy here
        return 'load'  # Example: always choose 'load'

# Create an instance of the agent
agent = Agent()

# Define the play function for the tournament to use
def play(opponent_last_move):
    return agent.play(opponent_last_move)
```

## Game Rules

- Agents can choose from five moves: shield, load, fireball, tsunami, mirror
- `load` increases the agent's load count
- `fireball` requires 1 load to use
- `tsunami` requires 2 loads to use
- `mirror` can only be used once per match
- Certain moves are effective against others (e.g., fireball beats load)

## Tournament System

- Agents play against each other in a round-robin format
- Multiple matches are played between each pair of agents
- Points are awarded based on win/loss/draw outcomes
- Results are stored and displayed on the leaderboard

## Web Interface

- Leaderboard: View current standings of all agents
- Submit Agent: Add a new agent to the tournament
- Edit Agent: Modify an existing agent's code
- Run Tournament: Start a new tournament with all submitted agents

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Implement your changes
4. Submit a pull request with a clear description of your improvements

Feel free to submit issues or feature requests through the project's issue tracker.