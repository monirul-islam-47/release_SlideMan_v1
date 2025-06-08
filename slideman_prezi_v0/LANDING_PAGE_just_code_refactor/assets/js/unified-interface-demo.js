// Unified Interface Demo JavaScript

// Command bar functionality
const commandInput = document.getElementById('commandInput');
const searchSuggestions = document.getElementById('searchSuggestions');
const preziAssistant = document.getElementById('preziAssistant');

// Rotating placeholders
const placeholders = [
    "Search slides, create presentations, or ask PrezI anything...",
    "Try: 'Find all Q4 revenue charts'",
    "Try: 'Create investor pitch for BigCorp'",
    "Try: 'Update all slides with new brand colors'",
    "Try: 'Which slides need professional formatting?'"
];

let placeholderIndex = 0;
setInterval(() => {
    placeholderIndex = (placeholderIndex + 1) % placeholders.length;
    commandInput.placeholder = placeholders[placeholderIndex];
}, 5000);

// Search suggestions
commandInput.addEventListener('focus', () => {
    searchSuggestions.classList.add('active');
});

commandInput.addEventListener('blur', () => {
    setTimeout(() => {
        searchSuggestions.classList.remove('active');
    }, 200);
});

// PrezI toggle
function togglePrezi() {
    preziAssistant.classList.toggle('active');
}

// Keyword interactions
document.querySelectorAll('.keyword-pill').forEach(pill => {
    pill.addEventListener('click', function() {
        this.classList.toggle('active');
        updateSlideFiltering();
    });
});

// Slide card interactions
document.querySelectorAll('.slide-card').forEach(card => {
    card.addEventListener('click', function() {
        // Toggle selection
        this.classList.toggle('selected');
    });
    
    // Drag to assembly
    card.draggable = true;
    card.addEventListener('dragstart', (e) => {
        e.dataTransfer.effectAllowed = 'copy';
        card.style.opacity = '0.5';
    });
    
    card.addEventListener('dragend', () => {
        card.style.opacity = '';
    });
});

// Assembly dropzone
const dropzone = document.querySelector('.assembly-dropzone');

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.style.background = 'rgba(102, 126, 234, 0.1)';
});

dropzone.addEventListener('dragleave', () => {
    dropzone.style.background = '';
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.style.background = '';
    // Add slide to assembly
    addSlideToAssembly();
});

// Quick actions
document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const action = this.textContent;
        showStatus(`${action} action initiated...`);
    });
});

// Export functionality
document.querySelectorAll('.export-button, .export-btn-large').forEach(btn => {
    btn.addEventListener('click', () => {
        showStatus('Exporting professional presentation...');
        setTimeout(() => {
            showStatus('✅ Export complete! BigCorp_Pitch_2025.pptx ready');
        }, 2000);
    });
});

// Helper functions
function updateSlideFiltering() {
    const activeKeywords = document.querySelectorAll('.keyword-pill.active');
    console.log(`Filtering by ${activeKeywords.length} keywords`);
}

function addSlideToAssembly() {
    const assemblyCount = document.querySelector('.assembly-count');
    const currentCount = parseInt(assemblyCount.textContent);
    assemblyCount.textContent = `${currentCount + 1} slides`;
    
    // Update duration
    const duration = document.querySelector('.duration-value');
    duration.textContent = `${Math.ceil((currentCount + 1) * 1.5)} minutes`;
}

function showStatus(message) {
    const statusBar = document.querySelector('.status-bar');
    const tempStatus = document.createElement('div');
    tempStatus.className = 'status-item';
    tempStatus.style.position = 'absolute';
    tempStatus.style.left = '50%';
    tempStatus.style.transform = 'translateX(-50%)';
    tempStatus.style.background = 'var(--bg-card)';
    tempStatus.style.padding = '4px 16px';
    tempStatus.style.borderRadius = '12px';
    tempStatus.textContent = message;
    
    statusBar.appendChild(tempStatus);
    
    setTimeout(() => {
        tempStatus.style.transition = 'opacity 0.5s';
        tempStatus.style.opacity = '0';
        setTimeout(() => tempStatus.remove(), 500);
    }, 3000);
}

// Animate on load
window.addEventListener('load', () => {
    // Animate slide cards
    document.querySelectorAll('.slide-card').forEach((card, index) => {
        card.style.animationDelay = `${index * 0.05}s`;
        card.classList.add('fade-in');
    });
    
    // Show welcome status
    showStatus('Welcome to PrezI! Your AI assistant is ready.');
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + K to focus command bar
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        commandInput.focus();
    }
    
    // Escape to close PrezI
    if (e.key === 'Escape' && preziAssistant.classList.contains('active')) {
        togglePrezi();
    }
});