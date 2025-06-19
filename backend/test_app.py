import pytest
from app import app, games, WIN_SCORE

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_start_game(client):
    rv = client.post('/start')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'game_id' in data
    assert 'state' in data

def test_move_and_state(client):
    rv = client.post('/start')
    game_id = rv.get_json()['game_id']
    # Move up
    rv2 = client.post('/move', json={'game_id': game_id, 'direction': 'up'})
    assert rv2.status_code == 200
    state = rv2.get_json()['state']
    assert 'player_y' in state
    # Get state
    rv3 = client.get(f'/state?game_id={game_id}')
    assert rv3.status_code == 200
    state2 = rv3.get_json()['state']
    assert 'ball_x' in state2

def test_game_over_and_save_score(client):
    rv = client.post('/start')
    game_id = rv.get_json()['game_id']
    # Simulate player win
    games[game_id]['player_score'] = WIN_SCORE - 1
    games[game_id]['ball_x'] = 801  # force score
    client.get(f'/state?game_id={game_id}')
    state = games[game_id]
    assert state['game_over']
    assert state['winner'] == 'player'
    # Save score
    rv2 = client.post('/save_score', json={'username': 'testuser', 'score': WIN_SCORE})
    assert rv2.status_code == 200
    assert rv2.get_json()['status'] == 'ok'

def test_high_scores(client):
    rv = client.get('/high_scores')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'high_scores' in data
    assert isinstance(data['high_scores'], list) 