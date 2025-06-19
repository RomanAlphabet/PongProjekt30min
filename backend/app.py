from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import uuid
import os

app = Flask(__name__)
CORS(app)

# MongoDB setup
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['pong']
scores_collection = db['scores']

games = {}  # In-memory game state, keyed by game_id

# Game constants
GAME_WIDTH = 800
GAME_HEIGHT = 600
PADDLE_HEIGHT = 100
PADDLE_WIDTH = 16
BALL_SIZE = 16
PADDLE_SPEED = 32
BALL_SPEED = 12
WIN_SCORE = 5

# Helper: create new game state
def new_game_state():
    return {
        'player_y': (GAME_HEIGHT - PADDLE_HEIGHT) // 2,
        'computer_y': (GAME_HEIGHT - PADDLE_HEIGHT) // 2,
        'ball_x': (GAME_WIDTH - BALL_SIZE) // 2,
        'ball_y': (GAME_HEIGHT - BALL_SIZE) // 2,
        'ball_vx': BALL_SPEED,
        'ball_vy': BALL_SPEED,
        'player_score': 0,
        'computer_score': 0,
        'game_over': False,
        'winner': None
    }

# Helper: imperfect AI for computer paddle
def computer_ai(game):
    # Add randomness to make it beatable
    import random
    if random.random() < 0.7:  # 70% chance to move towards ball
        if game['computer_y'] + PADDLE_HEIGHT // 2 < game['ball_y']:
            game['computer_y'] += PADDLE_SPEED
        elif game['computer_y'] + PADDLE_HEIGHT // 2 > game['ball_y']:
            game['computer_y'] -= PADDLE_SPEED
    # Clamp
    game['computer_y'] = max(0, min(GAME_HEIGHT - PADDLE_HEIGHT, game['computer_y']))

# Helper: update ball and check collisions
def update_game(game):
    if game['game_over']:
        return
    # Move ball
    game['ball_x'] += game['ball_vx']
    game['ball_y'] += game['ball_vy']
    # Top/bottom collision
    if game['ball_y'] <= 0 or game['ball_y'] + BALL_SIZE >= GAME_HEIGHT:
        game['ball_vy'] *= -1
    # Player paddle collision
    if (game['ball_x'] <= PADDLE_WIDTH and
        game['player_y'] < game['ball_y'] + BALL_SIZE and
        game['player_y'] + PADDLE_HEIGHT > game['ball_y']):
        game['ball_vx'] = abs(game['ball_vx'])
    # Computer paddle collision
    if (game['ball_x'] + BALL_SIZE >= GAME_WIDTH - PADDLE_WIDTH and
        game['computer_y'] < game['ball_y'] + BALL_SIZE and
        game['computer_y'] + PADDLE_HEIGHT > game['ball_y']):
        game['ball_vx'] = -abs(game['ball_vx'])
    # Score for computer
    if game['ball_x'] < 0:
        game['computer_score'] += 1
        reset_ball(game, direction=1)
    # Score for player
    if game['ball_x'] > GAME_WIDTH:
        game['player_score'] += 1
        reset_ball(game, direction=-1)
    # Check win
    if game['player_score'] >= WIN_SCORE:
        game['game_over'] = True
        game['winner'] = 'player'
    elif game['computer_score'] >= WIN_SCORE:
        game['game_over'] = True
        game['winner'] = 'computer'

def reset_ball(game, direction=1):
    game['ball_x'] = (GAME_WIDTH - BALL_SIZE) // 2
    game['ball_y'] = (GAME_HEIGHT - BALL_SIZE) // 2
    game['ball_vx'] = BALL_SPEED * direction
    game['ball_vy'] = BALL_SPEED

@app.route('/start', methods=['POST'])
def start_game():
    game_id = str(uuid.uuid4())
    games[game_id] = new_game_state()
    return jsonify({'game_id': game_id, 'state': games[game_id]})

@app.route('/move', methods=['POST'])
def move_paddle():
    data = request.json
    game_id = data.get('game_id')
    direction = data.get('direction')  # 'up' or 'down'
    if game_id not in games:
        return jsonify({'error': 'Invalid game_id'}), 400
    game = games[game_id]
    if direction == 'up':
        game['player_y'] -= PADDLE_SPEED
    elif direction == 'down':
        game['player_y'] += PADDLE_SPEED
    # Clamp
    game['player_y'] = max(0, min(GAME_HEIGHT - PADDLE_HEIGHT, game['player_y']))
    # Computer AI
    computer_ai(game)
    # Update game
    update_game(game)
    return jsonify({'state': game})

@app.route('/state', methods=['GET'])
def get_state():
    game_id = request.args.get('game_id')
    if game_id not in games:
        return jsonify({'error': 'Invalid game_id'}), 400
    game = games[game_id]
    # Computer AI
    computer_ai(game)
    # Update game
    update_game(game)
    return jsonify({'state': game})

@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.json
    username = data.get('username')
    score = data.get('score')
    date = datetime.utcnow().isoformat()
    scores_collection.insert_one({
        'username': username,
        'score': score,
        'date': date
    })
    return jsonify({'status': 'ok'})

@app.route('/high_scores', methods=['GET'])
def high_scores():
    scores = list(scores_collection.find({}, {'_id': 0}).sort('score', -1).limit(10))
    return jsonify({'high_scores': scores})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 