// Progress Management System

class ProgressManager {
    constructor() {
        this.progressSteps = [];
        this.currentStep = 0;
        this.isRunning = false;
    }

    showProgress(steps = null) {
        if (steps) {
            this.progressSteps = steps;
        }
        const overlay = document.getElementById('progressOverlay');
        if (overlay) {
            overlay.classList.add('active');
        }
        this.isRunning = true;
    }

    hideProgress() {
        const overlay = document.getElementById('progressOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
        this.isRunning = false;
        this.currentStep = 0;
    }

    updateProgressStep(stepIndex, message = '') {
        this.currentStep = stepIndex;
        const progressText = document.getElementById('progressText');
        const progressFill = document.querySelector('.progress-fill');
        
        if (progressText && message) {
            progressText.textContent = message;
        }
        
        if (progressFill && this.progressSteps.length > 0) {
            const percentage = ((stepIndex + 1) / this.progressSteps.length) * 100;
            animateProgressBar(progressFill, percentage);
        }
    }

    runProgressSequence(steps, interval = 2000) {
        this.progressSteps = steps;
        this.showProgress();
        
        let currentIndex = 0;
        const runStep = () => {
            if (currentIndex < steps.length && this.isRunning) {
                this.updateProgressStep(currentIndex, steps[currentIndex]);
                currentIndex++;
                setTimeout(runStep, interval);
            } else if (this.isRunning) {
                setTimeout(() => this.hideProgress(), 1000);
            }
        };
        
        setTimeout(runStep, 500);
    }

    emergencyStop() {
        this.isRunning = false;
        this.hideProgress();
        this.showEmergencyMessage();
    }

    showEmergencyMessage() {
        const emergencyOverlay = document.getElementById('emergencyOverlay');
        if (emergencyOverlay) {
            emergencyOverlay.classList.add('active');
            setTimeout(() => {
                emergencyOverlay.classList.remove('active');
            }, 3000);
        }
    }
}

// Create global progress manager instance
window.progressManager = new ProgressManager();

// Common progress sequences
const PROGRESS_SEQUENCES = {
    urgentPitch: [
        "🔍 Analyzing your request...",
        "📊 Finding relevant slides...",
        "🧠 Understanding context...",
        "⚡ Generating presentation...",
        "✨ Finalizing layout...",
        "🎯 Presentation ready!"
    ],
    
    aiThinking: [
        "🧠 Initializing neural pathways...",
        "📝 Processing slide content...",
        "🔗 Building knowledge connections...",
        "💡 Generating insights...",
        "🎯 Optimizing recommendations..."
    ],
    
    keywordIntegration: [
        "🏷️ Analyzing keyword patterns...",
        "🔍 Scanning slide database...",
        "📊 Building semantic connections...",
        "⚡ Updating classifications...",
        "✅ Integration complete!"
    ],
    
    elementAnalysis: [
        "🎯 Scanning slide elements...",
        "🧠 AI analysis in progress...",
        "🏷️ Applying smart tags...",
        "📊 Building element map...",
        "✨ Analysis complete!"
    ]
};

// Utility functions for different progress types
function showUrgentPitchProgress() {
    window.progressManager.runProgressSequence(PROGRESS_SEQUENCES.urgentPitch, 1500);
}

function showAIThinkingProgress() {
    window.progressManager.runProgressSequence(PROGRESS_SEQUENCES.aiThinking, 2000);
}

function showKeywordProgress() {
    window.progressManager.runProgressSequence(PROGRESS_SEQUENCES.keywordIntegration, 1200);
}

function showElementAnalysisProgress() {
    window.progressManager.runProgressSequence(PROGRESS_SEQUENCES.elementAnalysis, 1800);
}