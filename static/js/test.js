document.addEventListener('DOMContentLoaded', function() {
    // Test timer functionality
    const timerElement = document.getElementById('timer');
    
    if (timerElement) {
        const durationMinutes = parseInt(timerElement.getAttribute('data-duration'), 10);
        let totalSeconds = durationMinutes * 60;
        let timerInterval;
        
        // Function to format time as MM:SS
        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
        }
        
        // Function to update the timer
        function updateTimer() {
            totalSeconds--;
            
            if (totalSeconds <= 0) {
                // Time's up - submit the test
                clearInterval(timerInterval);
                timerElement.textContent = "00:00";
                alert("Time's up! Submitting your test...");
                document.getElementById('test-form').submit();
                return;
            }
            
            // Update the timer display
            timerElement.textContent = formatTime(totalSeconds);
            
            // Add warning class when less than 5 minutes remaining
            if (totalSeconds <= 300) {
                timerElement.classList.add('warning');
            }
        }
        
        // Start the timer
        timerElement.textContent = formatTime(totalSeconds);
        timerInterval = setInterval(updateTimer, 1000);
        
        // Handle page unload (browser close/refresh)
        window.addEventListener('beforeunload', function(e) {
            // Show a confirmation dialog
            const confirmationMessage = 'If you leave this page, your test progress will be lost.';
            e.returnValue = confirmationMessage;
            return confirmationMessage;
        });
        
        // Handle form submission
        document.getElementById('test-form').addEventListener('submit', function() {
            // Remove the beforeunload handler when form is submitted normally
            window.removeEventListener('beforeunload', function() {});
        });
    }
});