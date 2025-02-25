// Function to handle the setup form submission
function setupFormHandler() {
    const setupForm = document.getElementById('setupForm');
    if (setupForm) {
        setupForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const eventType = document.getElementById('eventType').value;
            const tone = document.getElementById('tone').value;
            const ageFrom = document.getElementById('ageFrom').value;
            const ageTo = document.getElementById('ageTo').value;
            const numQuestions = document.getElementById('numQuestions').value;

            const response = await fetch('/start_event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ eventType, tone, ageFrom, ageTo, numQuestions }),
            });

            const data = await response.json();
            if (data.error) {
                alert(data.error);
                return;
            }

            // Debugging: Print received questions
            console.log("Received Questions:", data.questions);

            // Save questions to localStorage
            localStorage.setItem('questions', JSON.stringify(data.questions));
            localStorage.setItem('currentQuestionIndex', 0);

            // Redirect to participants page
            window.location.href = '/participants';
        });

        // Update the number of questions value dynamically
        const numQuestionsInput = document.getElementById('numQuestions');
        if (numQuestionsInput) {
            numQuestionsInput.addEventListener('input', function() {
                document.getElementById('numQuestionsValue').textContent = this.value;
            });
        }
    }
}

// Function to handle the participants page logic
function participantsPageHandler() {
    const questions = JSON.parse(localStorage.getItem('questions'));
    if (questions) {
        // Debugging: Print questions from localStorage
        console.log("Questions from localStorage:", questions);

        let currentQuestionIndex = parseInt(localStorage.getItem('currentQuestionIndex'));
        const questionsContainer = document.getElementById('questionsContainer');
        const nextQuestionButton = document.getElementById('nextQuestion');
        const finishMessage = document.getElementById('finishMessage');
        const progressBar = document.getElementById('progress');

        function displayQuestion() {
            if (currentQuestionIndex < questions.length) {
                questionsContainer.innerHTML = `
                    <p>${questions[currentQuestionIndex]}</p>
                    <input type="text" id="answer" placeholder="Enter name">
                    <button onclick="submitAnswer()">${currentQuestionIndex < questions.length - 1 ? 'Next' : 'Submit'}</button>
                `;
                nextQuestionButton.style.display = 'none';
                updateProgressBar();
            } else {
                questionsContainer.style.display = 'none';
                nextQuestionButton.style.display = 'none';
                finishMessage.style.display = 'block';
            }
        }

        function updateProgressBar() {
            const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
            progressBar.style.width = `${progress}%`;
        }

        window.submitAnswer = function() {
            const answer = document.getElementById('answer').value;
            // Save the answer or process it as needed
            currentQuestionIndex++;
            localStorage.setItem('currentQuestionIndex', currentQuestionIndex);
            displayQuestion();
        }

        displayQuestion();
    } else {
        console.log("No questions found in localStorage.");
    }
}

// Run the appropriate handler based on the current page
if (window.location.pathname === '/') {
    setupFormHandler();
} else if (window.location.pathname === '/participants') {
    participantsPageHandler();
}