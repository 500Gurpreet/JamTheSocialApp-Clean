// Function to handle the setup form submission
function setupFormHandler() {
    const setupForm = document.getElementById('setupForm');
    if (setupForm) {
        setupForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const submitButton = setupForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = 'Starting Event...';

            try {
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

                window.location.href = `/event/${data.event_id}`;
            } catch (error) {
                alert('An error occurred. Please try again.');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = 'Start Event';
            }
        });
    }
}

// Run the appropriate handler based on the current page
if (window.location.pathname === '/') {
    setupFormHandler();
}