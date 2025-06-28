const canvas = document.getElementById('pong');
const ctx = canvas.getContext('2d');

// Game settings
const paddleWidth = 16;
const paddleHeight = 100;
const ballSize = 18;
const playerX = 20;
const aiX = canvas.width - playerX - paddleWidth;

// Paddle state
let playerY = (canvas.height - paddleHeight) / 2;
let aiY = (canvas.height - paddleHeight) / 2;

// Ball state
let ballX = canvas.width / 2 - ballSize / 2;
let ballY = canvas.height / 2 - ballSize / 2;
let ballSpeedX = 5;
let ballSpeedY = 4;

// Score
let playerScore = 0;
let aiScore = 0;

// Mouse control for player paddle
canvas.addEventListener('mousemove', function (evt) {
    const rect = canvas.getBoundingClientRect();
    let mouseY = evt.clientY - rect.top;
    playerY = mouseY - paddleHeight / 2;
    if (playerY < 0) playerY = 0;
    if (playerY + paddleHeight > canvas.height) playerY = canvas.height - paddleHeight;
});

// Draw functions
function drawRect(x, y, w, h, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, w, h);
}

function drawCircle(x, y, r, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2, false);
    ctx.closePath();
    ctx.fill();
}

function drawText(text, x, y, size, color) {
    ctx.fillStyle = color;
    ctx.font = `${size}px monospace`;
    ctx.fillText(text, x, y);
}

// Collision with paddle
function collide(x, y, w, h, bx, by, bs) {
    return (
        x < bx + bs &&
        x + w > bx &&
        y < by + bs &&
        y + h > by
    );
}

// Reset the ball to the center
function resetBall() {
    ballX = canvas.width / 2 - ballSize / 2;
    ballY = canvas.height / 2 - ballSize / 2;
    // Randomize direction
    ballSpeedX = (Math.random() < 0.5 ? 1 : -1) * 5;
    ballSpeedY = (Math.random() < 0.5 ? 1 : -1) * 4;
}

// AI movement (simple follow)
function moveAI() {
    let aiCenter = aiY + paddleHeight / 2;
    if (aiCenter < ballY + ballSize / 2 - 10) {
        aiY += 6;
    } else if (aiCenter > ballY + ballSize / 2 + 10) {
        aiY -= 6;
    }
    // Clamp within canvas
    if (aiY < 0) aiY = 0;
    if (aiY + paddleHeight > canvas.height) aiY = canvas.height - paddleHeight;
}

function update() {
    // Move ball
    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Wall collision
    if (ballY <= 0 || ballY + ballSize >= canvas.height) {
        ballSpeedY = -ballSpeedY;
    }

    // Player paddle collision
    if (collide(playerX, playerY, paddleWidth, paddleHeight, ballX, ballY, ballSize)) {
        ballSpeedX = Math.abs(ballSpeedX);
        // Add effect based on hit position
        let deltaY = (ballY + ballSize / 2) - (playerY + paddleHeight / 2);
        ballSpeedY = deltaY * 0.25;
    }

    // AI paddle collision
    if (collide(aiX, aiY, paddleWidth, paddleHeight, ballX, ballY, ballSize)) {
        ballSpeedX = -Math.abs(ballSpeedX);
        let deltaY = (ballY + ballSize / 2) - (aiY + paddleHeight / 2);
        ballSpeedY = deltaY * 0.25;
    }

    // Score update
    if (ballX < 0) {
        aiScore++;
        resetBall();
    } else if (ballX + ballSize > canvas.width) {
        playerScore++;
        resetBall();
    }

    moveAI();
}

function render() {
    // Clear
    drawRect(0, 0, canvas.width, canvas.height, '#111');

    // Middle line
    for (let i = 0; i < canvas.height; i += 35) {
        drawRect(canvas.width / 2 - 2, i, 4, 20, '#333');
    }

    // Paddles
    drawRect(playerX, playerY, paddleWidth, paddleHeight, '#fff');
    drawRect(aiX, aiY, paddleWidth, paddleHeight, '#fff');

    // Ball
    drawRect(ballX, ballY, ballSize, ballSize, '#fff');

    // Scores
    drawText(playerScore, canvas.width / 2 - 80, 50, 48, '#0f0');
    drawText(aiScore, canvas.width / 2 + 50, 50, 48, '#f44');
}

function gameLoop() {
    update();
    render();
    requestAnimationFrame(gameLoop);
}

// Start game
resetBall();
gameLoop();