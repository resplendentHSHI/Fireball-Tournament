from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os
import re
import logging
import traceback
from logging.handlers import RotatingFileHandler
import threading
import json

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['LOADING_GIF'] = 'static/cute-dancing.gif'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agents.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
db = SQLAlchemy(app)

# Constants
OUTPUT_FILE = 'tournament_output.txt'
PROGRESS_FILE = 'tournament_progress.json'

# Global variables
tournament_running = False

# Logging setup
if not os.path.exists('logs'):
    os.mkdir('logs')

logging.basicConfig(level=logging.INFO)
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

# Database model
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, default=0)

# Routes

@app.route('/')
def index():
    try:
        with open('tournament_results.json', 'r') as f:
            results = json.load(f)
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        return render_template('index.html', agents=sorted_results)
    except FileNotFoundError:
        app.logger.error("tournament_results.json not found. Initializing with empty results.")
        return render_template('index.html', agents=[])

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        
        if not name or not code:
            flash('Name and code are required!', 'error')
            return render_template('submit.html')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            flash('Name should only contain letters, numbers, and underscores!', 'error')
            return render_template('submit.html')
        
        agent_name = f"{name}_agent" if not name.endswith('_agent') else name
        
        # Save the agent file
        save_agent_file(agent_name, code)
        
        # Update the JSON file
        with open('tournament_results.json', 'r') as f:
            results = json.load(f)
        
        if agent_name not in results:
            results[agent_name] = 0
            with open('tournament_results.json', 'w') as f:
                json.dump(results, f)
            flash('Agent submitted successfully!', 'success')
        else:
            flash('Agent updated successfully!', 'success')
        
        return redirect(url_for('index'))
    return render_template('submit.html')

@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit(id):
    try:
        with open('tournament_results.json', 'r') as f:
            results = json.load(f)
        
        if id not in results:
            flash('Agent not found!', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            code = request.form['code']
            save_agent_file(id, code)
            flash('Agent updated successfully!', 'success')
            return redirect(url_for('index'))
        
        with open(f'{id}.py', 'r') as f:
            code = f.read()
        
        return render_template('edit.html', agent={'name': id, 'code': code})
    except FileNotFoundError:
        flash('Agent file not found!', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<string:id>')
def delete(id):
    try:
        with open('tournament_results.json', 'r') as f:
            results = json.load(f)
        
        if id in results:
            del results[id]
            with open('tournament_results.json', 'w') as f:
                json.dump(results, f)
            
            os.remove(f'{id}.py')
            flash('Agent deleted successfully!', 'success')
        else:
            flash('Agent not found!', 'error')
    except FileNotFoundError:
        flash('Tournament results file not found!', 'error')
    
    return redirect(url_for('index'))

@app.route('/run_tournament')
def run_tournament():
    global tournament_running
    if not tournament_running:
        tournament_running = True
        threading.Thread(target=run_tournament_script).start()
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'already_running'})

@app.route('/tournament_status')
def tournament_status():
    app.logger.info("Received request for tournament status")
    results = {}
    if os.path.exists(OUTPUT_FILE):
        app.logger.info(f"Output file found: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'r') as f:
            lines = f.readlines()
            app.logger.info(f"Read {len(lines)} lines from output file")
            results = parse_tournament_results(lines)
    else:
        app.logger.warning(f"Output file not found: {OUTPUT_FILE}")
    
    # Read progress from PROGRESS_FILE
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
    
    # Read full results from tournament_results.json
    full_results = {}
    if os.path.exists('tournament_results.json'):
        with open('tournament_results.json', 'r') as f:
            full_results = json.load(f)
    
    response = {
        'running': tournament_running,
        'results': results,
        'progress': progress,
        'full_results': full_results
    }
    app.logger.info(f"Sending tournament status response: {response}")
    return jsonify(response)


# Helper functions
def save_agent_file(agent_name, code):
    filename = f"{agent_name}_agent.py" if not agent_name.endswith('_agent') else f"{agent_name}.py"
    with open(filename, 'w') as f:
        f.write(code)

def delete_agent_file(agent_name):
    try:
        os.remove(f'{agent_name}_agent.py')
    except FileNotFoundError:
        pass

def parse_tournament_results(lines):
    results = {}
    parsing_results = False
    app.logger.info("--- Starting to parse tournament results ---")
    for line in lines:
        #app.logger.info(f"Reading line: {line.strip()}")
        if line.strip() == "Tournament Results:":
            parsing_results = True
            app.logger.info("Found 'Tournament Results:' line, starting to parse results")
            continue
        if parsing_results:
            parts = line.strip().split(": ")
            if len(parts) == 2:
                agent, score = parts
                try:
                    numeric_score = float(score.split()[0])
                    results[agent] = numeric_score
                    app.logger.info(f"Parsed result: {agent} = {numeric_score}")
                except ValueError:
                    app.logger.error(f"Error parsing score for {agent}: {score}")
            else:
                app.logger.warning(f"Skipping line (not in expected format): {line.strip()}")
    app.logger.info("--- Finished parsing tournament results ---")
    app.logger.info(f"Final parsed results: {results}")
    return results

def update_agent_scores(results):
    app.logger.info("Updating agent scores in the database")
    for agent_name, score in results.items():
        db_agent_name = f"{agent_name}_agent" if not agent_name.endswith('_agent') else agent_name
        agent = Agent.query.filter_by(name=db_agent_name).first()
        if agent:
            agent.score = score
            app.logger.info(f"Updated {db_agent_name} score to {score}")
        else:
            app.logger.warning(f"Agent {db_agent_name} not found in database")
    db.session.commit()
    app.logger.info("Database update completed")

def initialize_tournament_results():
    if not os.path.exists('tournament_results.json'):
        results = {}
        for filename in os.listdir('.'):
            if filename.endswith('_agent.py'):
                agent_name = filename[:-3]  # Remove '.py' from the end
                results[agent_name] = 0
        
        with open('tournament_results.json', 'w') as f:
            json.dump(results, f)
        
        app.logger.info(f"Initialized tournament_results.json with {len(results)} agents")
    else:
        app.logger.info("tournament_results.json already exists, skipping initialization")

def run_tournament_script():
    global tournament_running
    try:
        open(OUTPUT_FILE, 'w').close()
        open(PROGRESS_FILE, 'w').close()

        process = subprocess.Popen(
            ['python', 'tournament.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                app.logger.info(f"Tournament output: {output.strip()}")
                with open(OUTPUT_FILE, 'a') as f:
                    f.write(output)

        stdout, stderr = process.communicate()
        if stdout:
            app.logger.info(f"Tournament final output: {stdout}")
            with open(OUTPUT_FILE, 'a') as f:
                f.write(stdout)
        if stderr:
            app.logger.error(f"Tournament error output: {stderr}")
            with open(OUTPUT_FILE, 'a') as f:
                f.write(f"Error: {stderr}")

        if process.returncode != 0:
            app.logger.error(f"Tournament script exited with error code {process.returncode}")
            with open(OUTPUT_FILE, 'a') as f:
                f.write(f"Tournament script exited with error code {process.returncode}\n")

        # Parse results after tournament completion
        with open(OUTPUT_FILE, 'r') as f:
            lines = f.readlines()
            new_results = parse_tournament_results(lines)
        
        # Round scores to 2 decimal points
        new_results = {agent: round(score, 2) for agent, score in new_results.items()}
        
        app.logger.info(f"Tournament results parsed: {new_results}")

        # Read existing results
        with open('tournament_results.json', 'r') as f:
            existing_results = json.load(f)

        # Update results, preserving agents with existing scores
        for agent, score in existing_results.items():
            if agent not in new_results:
                new_results[agent] = round(score, 2)

        # Write updated results to JSON file
        with open('tournament_results.json', 'w') as f:
            json.dump(new_results, f)

    except Exception as e:
        app.logger.exception(f"Error running tournament: {str(e)}")
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"Error running tournament: {str(e)}\n")
    finally:
        tournament_running = False

# Main execution
if __name__ == '__main__':
    with app.app_context():
        initialize_tournament_results()
    app.run(debug=True)