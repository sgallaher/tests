
    function redirectToToken(event) {
        event.preventDefault(); // Prevent the default form submission
        const tokenInput = document.getElementById('token');
        const token = tokenInput.value.trim(); // Get the token value and trim whitespace
        if (token) {
            window.location.href = `/test/${token}`; // Redirect to the /test/<token> URL
        } else {
            alert('Please enter a valid token.'); // Handle empty input
        }
    }


let puzzle = JSON.parse(document.getElementById('puzzle-data').textContent || '[]');
let wordScores = new Array(puzzle.length).fill(0);
let totalScore = 0;
let timers = {};
let activeInputs = {};

function calculateScore(seconds) {
    if (seconds < 2) return 100;
    if (seconds < 4) return 75;
    if (seconds < 6) return 50;
    if (seconds < 8) return 25;
    if (seconds < 10) return 10;
    return 0;
}

function startInputTimer(wordIndex, letterIndex) {
    const input = document.getElementById(`tb_${wordIndex}_${letterIndex}`);
    if (input.disabled) return;

    const timerId = `timer_${wordIndex}_${letterIndex}`;
    let startTime = Date.now();
    activeInputs[timerId] = true;

    timers[timerId] = setInterval(() => {
        if (!activeInputs[timerId]) return;

        let elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        const timerElem = document.getElementById(timerId);
        if (timerElem) timerElem.innerText = elapsed;

        if (elapsed >= 10) {
            input.value = puzzle[wordIndex][0][letterIndex];
            input.disabled = true;
            input.classList.remove('incorrect');
            input.classList.add('correct');
            clearInterval(timers[timerId]);
            checkWordSolved(wordIndex);
        }
    }, 100);
}

function pauseInputTimer(wordIndex, letterIndex) {
    const timerId = `timer_${wordIndex}_${letterIndex}`;
    activeInputs[timerId] = false;
}

function checkWordSolved(wordIndex) {
    const word = puzzle[wordIndex][0];
    const hints = puzzle[wordIndex][1];
    let isSolved = true;
    let score = 0;

    for (let i = 0; i < word.length; i++) {
        const input = document.getElementById(`tb_${wordIndex}_${i}`);
        const timerId = `timer_${wordIndex}_${i}`;
        const value = input.value.toLowerCase();

        if (hints.includes(i)) continue;

        if (input.disabled) {
            const timeText = document.getElementById(timerId)?.innerText || "10";
            const time = parseFloat(timeText);
            score += calculateScore(time);
            continue;
        }

        if (value === word[i].toLowerCase()) {
            input.disabled = true;
            input.classList.remove('incorrect');
            input.classList.add('correct');
            clearInterval(timers[timerId]);
            const time = parseFloat(document.getElementById(timerId).innerText);
            score += calculateScore(time);
        } else {
            isSolved = false;
            input.classList.add('incorrect');
        }
    }

    if (isSolved) {
        wordScores[wordIndex] = score;
        totalScore = wordScores.reduce((a, b) => a + b, 0);

        const next = document.getElementById(`word_${wordIndex + 1}`);
        if (next) {
            next.style.display = 'block';
        } else {
            document.getElementById('final-score-container').style.display = 'block';
            document.getElementById('total-score').innerText = totalScore;
            confetti({ particleCount: 150, spread: 100, origin: { y: 0.6 } });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.textbox').forEach(input => {
        const wordIndex = parseInt(input.dataset.word);
        const letterIndex = parseInt(input.dataset.idx);

        if (!input.disabled) input.classList.add('incorrect');

        input.addEventListener('focus', () => startInputTimer(wordIndex, letterIndex));
        input.addEventListener('blur', () => pauseInputTimer(wordIndex, letterIndex));
        input.addEventListener('input', () => checkWordSolved(wordIndex));
    });

    document.getElementById('puzzleForm')?.addEventListener('submit', (e) => {
        document.getElementById('scores').value = wordScores.join(',');
    });
});