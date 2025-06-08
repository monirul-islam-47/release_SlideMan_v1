// Urgent Pitch Demo JavaScript

function showProgress() {
    document.getElementById('progressOverlay').classList.add('active');
    document.getElementById('emergencyStop').classList.add('active');
    
    // Simulate progress
    let progress = 0;
    const progressFill = document.querySelector('.progress-fill');
    const progressStatus = document.querySelector('.progress-status');
    
    const messages = [
        "Searching through 1000+ slides for Q4 content...",
        "Found 47 relevant slides, selecting the best ones...",
        "Applying consistent formatting and brand guidelines...",
        "Creating smooth transitions between sections...",
        "Generating executive summary...",
        "Finalizing professional presentation..."
    ];
    
    let messageIndex = 0;
    const interval = setInterval(() => {
        progress += 5;
        progressFill.style.width = progress + '%';
        
        if (progress % 20 === 0 && messageIndex < messages.length) {
            progressStatus.textContent = messages[messageIndex];
            messageIndex++;
        }
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                hideProgress();
                alert('✨ Presentation ready! BigCorp Investor Pitch has been created.');
            }, 500);
        }
    }, 200);
}

function hideProgress() {
    document.getElementById('progressOverlay').classList.remove('active');
    document.getElementById('emergencyStop').classList.remove('active');
}

// Initialize demo-specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects
    document.querySelectorAll('.plan-step').forEach(step => {
        step.addEventListener('mouseenter', () => {
            step.style.borderColor = 'var(--accent-purple)';
        });
        step.addEventListener('mouseleave', () => {
            step.style.borderColor = 'var(--border)';
        });
    });
    
    // Emergency stop functionality
    const emergencyStop = document.getElementById('emergencyStop');
    if (emergencyStop) {
        emergencyStop.addEventListener('click', () => {
            if (confirm('Stop PREZI from building the presentation?')) {
                hideProgress();
                alert('PREZI stopped. Your work has been saved.');
            }
        });
    }
});