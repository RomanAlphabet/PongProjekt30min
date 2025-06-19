const API_URL = 'http://localhost:5000';
let gameId = null;
let gameState = null;
let polling = null;
let upPressed = false;
let downPressed = false;

const canvas = document.getElementById('pong-canvas');
const ctx = canvas.getContext('2d');
const scoreboard = document.getElementById('scoreboard');
const endgameModal = document.getElementById('endgame-modal');
const endgameMessage = document.getElementById('endgame-message');
const usernameInput = document.getElementById('username');
const saveScoreBtn = document.getElementById('save-score-btn');
const playAgainBtn = document.getElementById('play-again-btn');
const highscoresDiv = document.getElementById('highscores');

function drawGame(state) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Draw paddles
  ctx.fillStyle = '#f1f1f1';
  ctx.fillRect(0, state.player_y, 16, 100);
  ctx.fillRect(800 - 16, state.computer_y, 16, 100);
  // Draw ball
  ctx.fillStyle = '#ffb300';
  ctx.fillRect(state.ball_x, state.ball_y, 16, 16);
  // Draw center line
  ctx.strokeStyle = '#444';
  ctx.setLineDash([16, 16]);
  ctx.beginPath();
  ctx.moveTo(400, 0);
  ctx.lineTo(400, 600);
  ctx.stroke();
  ctx.setLineDash([]);
  // Draw scores
  scoreboard.textContent = `Player: ${state.player_score}  |  Computer: ${state.computer_score}`;
}

function showEndgame(winner) {
  endgameModal.classList.remove('hidden');
  endgameMessage.textContent = winner === 'player' ? 'You win! 🎉' : 'Computer wins! 😢';
}

function hideEndgame() {
  endgameModal.classList.add('hidden');
  usernameInput.value = '';
}

function pollState() {
  fetch(`${API_URL}/state?game_id=${gameId}`)
    .then(res => res.json())
    .then(data => {
      gameState = data.state;
      drawGame(gameState);
      if (gameState.game_over) {
        clearInterval(polling);
        showEndgame(gameState.winner);
      }
    });
}

function startGame() {
  fetch(`${API_URL}/start`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      gameId = data.game_id;
      gameState = data.state;
      drawGame(gameState);
      hideEndgame();
      polling = setInterval(pollState, 200);
    });
}

function movePaddle(direction) {
  fetch(`${API_URL}/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId, direction })
  })
    .then(res => res.json())
    .then(data => {
      gameState = data.state;
      drawGame(gameState);
    });
}

function saveScore() {
  const username = usernameInput.value.trim();
  if (!username) return;
  fetch(`${API_URL}/save_score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, score: gameState.player_score })
  })
    .then(() => {
      loadHighScores();
      saveScoreBtn.disabled = true;
    });
}

function loadHighScores() {
  fetch(`${API_URL}/high_scores`)
    .then(res => res.json())
    .then(data => {
      highscoresDiv.innerHTML = '<h3>High Scores</h3>' +
        '<ol>' +
        data.high_scores.map(s => `<li>${s.username} - ${s.score} (${new Date(s.date).toLocaleString()})</li>`).join('') +
        '</ol>';
    });
}

// Keyboard controls
window.addEventListener('keydown', e => {
  if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') upPressed = true;
  if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') downPressed = true;
});
window.addEventListener('keyup', e => {
  if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') upPressed = false;
  if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') downPressed = false;
});

setInterval(() => {
  if (!gameState || gameState.game_over) return;
  if (upPressed) movePaddle('up');
  if (downPressed) movePaddle('down');
}, 100);

saveScoreBtn.addEventListener('click', saveScore);
playAgainBtn.addEventListener('click', startGame);

document.addEventListener('DOMContentLoaded', () => {
  startGame();
  loadHighScores();
}); 