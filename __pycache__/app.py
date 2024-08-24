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
    agents = Agent.query.order_by(Agent.score.desc()).all()
    return render_template('index.html', agents=agents)

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
        
        existing_agent = Agent.query.filter_by(name=name).first()
        if existing_agent:
            existing_agent.code = code
            db.session.commit()
            flash('Agent updated successfully!', 'success')
        else:
            new_agent = Agent(name=name, code=code, score=0.0)
            db.session.add(new_agent)
            db.session.commit()
            flash('Agent submitted successfully!', 'success')
        
        save_agent_file(name, code)
        return redirect(url_for('index'))
    return render_template('submit.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    agent = Agent.query.get_or_404(id)
    if request.method == 'POST':
        agent.name = request.form['name']
        agent.code = request.form['code']
        
        if not agent.name or not agent.code:
            flash('Name and code are required!', 'error')
            return render_template('edit.html', agent=agent)
        
        if not re.match(r'^[a-zA-Z0-9_]+$', agent.name):
            flash('Name should only contain letters, numbers, and underscores!', 'error')
            return render_template('edit.html', agent=agent)
        
        db.session.commit()
        save_agent_file(agent.name, agent.code)
        flash('Agent updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', agent=agent)

@app.route('/delete/<int:id>')
def delete(id):
    agent = Agent.query.get_or_404(id)
    db.session.delete(agent)
    db.session.commit()
    delete_agent_file(agent.name)
    flash('Agent deleted successfully!', 'success')
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
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            try:
                progress = json.load(f)
            except json.JSONDecodeError:
                progress = {}

    results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            lines = f.readlines()
            results = parse_tournament_results(lines)

    return jsonify({
        'running': tournament_running,
        'progress': progress,
        'results': results
    })

# Helper functions
def save_agent_file(agent_name, code):
    with open(f'{agent_name}_agent.py', 'w') as f:
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
        app.logger.info(f"Reading line: {line.strip()}")
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
        agent = Agent.query.filter_by(name=agent_name).first()
        if agent:
            agent.score = score
            app.logger.info(f"Updated {agent_name} score to {score}")
        else:
            app.logger.warning(f"Agent {agent_name} not found in database")
    db.session.commit()
    app.logger.info("Database update completed")

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
            results = parse_tournament_results(lines)
        app.logger.info(f"Tournament results parsed: {results}")

        # Update the database with new scores
        with app.app_context():
            update_agent_scores(results)

    except Exception as e:
        app.logger.exception(f"Error running tournament: {str(e)}")
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"Error running tournament: {str(e)}\n")
    finally:
        tournament_running = False

# Main execution
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)