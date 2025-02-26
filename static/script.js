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

            // Redirect to the host screen with the event ID
            window.location.href = `/event/${data.event_id}`;
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

// Run the appropriate handler based on the current page
if (window.location.pathname === '/') {
    setupFormHandler();
}