// Keyword Integration Demo JavaScript

// Keyword input with AI suggestions
const keywordInput = document.getElementById('keywordInput');
const aiSuggestions = document.getElementById('aiSuggestions');

keywordInput.addEventListener('focus', () => {
    setTimeout(() => {
        aiSuggestions.classList.add('active');
    }, 300);
});

keywordInput.addEventListener('blur', () => {
    setTimeout(() => {
        aiSuggestions.classList.remove('active');
    }, 200);
});

keywordInput.addEventListener('input', (e) => {
    const value = e.target.value.toLowerCase();
    if (value.length > 2) {
        // Simulate AI suggestions based on input
        updateAISuggestions(value);
    }
});

function updateAISuggestions(query) {
    const suggestions = [
        { text: query + ' analysis', confidence: 92 },
        { text: query + ' trends', confidence: 87 },
        { text: query + ' forecast', confidence: 85 },
        { text: query + ' comparison', confidence: 82 }
    ];
    
    const suggestionsHtml = suggestions.map(s => `
        <div class="suggestion-item">
            <span>${s.text}</span>
            <span class="suggestion-confidence">${s.confidence}%</span>
        </div>
    `).join('');
    
    aiSuggestions.innerHTML = suggestionsHtml;
}

// Category tabs
document.querySelectorAll('.category-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        // Filter keywords based on category
        filterKeywords(tab.textContent);
    });
});

// Keyword selection
document.querySelectorAll('.keyword-item').forEach(item => {
    item.addEventListener('click', () => {
        item.classList.toggle('active');
        // Update slide filtering
        updateSlideFiltering();
    });
});

// Draw relationship lines
function drawRelationshipLines() {
    const graph = document.getElementById('relationshipGraph');
    const central = graph.querySelector('.central');
    const nodes = graph.querySelectorAll('.relationship-node:not(.central)');
    
    const centralRect = central.getBoundingClientRect();
    const graphRect = graph.getBoundingClientRect();
    
    nodes.forEach(node => {
        const nodeRect = node.getBoundingClientRect();
        
        const x1 = centralRect.left - graphRect.left + centralRect.width / 2;
        const y1 = centralRect.top - graphRect.top + centralRect.height / 2;
        const x2 = nodeRect.left - graphRect.left + nodeRect.width / 2;
        const y2 = nodeRect.top - graphRect.top + nodeRect.height / 2;
        
        const distance = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
        
        const line = document.createElement('div');
        line.className = 'relationship-line';
        line.style.width = distance + 'px';
        line.style.left = x1 + 'px';
        line.style.top = y1 + 'px';
        line.style.transform = `rotate(${angle}deg)`;
        
        graph.insertBefore(line, graph.firstChild);
    });
}

// Initialize relationship graph
setTimeout(drawRelationshipLines, 100);

// Smart action interactions
document.querySelectorAll('.smart-action').forEach(action => {
    action.addEventListener('click', () => {
        const title = action.querySelector('.action-title').textContent;
        showTooltip(action, `Executing: ${title}`);
        
        // Simulate action execution
        setTimeout(() => {
            hideTooltip();
            // Show success animation
            action.style.background = 'rgba(16, 185, 129, 0.1)';
            action.style.borderColor = 'var(--accent-green)';
            setTimeout(() => {
                action.style.background = '';
                action.style.borderColor = '';
            }, 1000);
        }, 1500);
    });
});

// Tooltip functions
function showTooltip(element, text) {
    const tooltip = document.getElementById('tooltip');
    const rect = element.getBoundingClientRect();
    
    tooltip.textContent = text;
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.bottom + 10) + 'px';
    tooltip.classList.add('active');
}

function hideTooltip() {
    document.getElementById('tooltip').classList.remove('active');
}

// Slide card hover effects
document.querySelectorAll('.slide-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        // Show keyword connections
        const keywords = card.querySelectorAll('.slide-keyword-tag');
        keywords.forEach(k => k.style.transform = 'scale(1.1)');
    });
    
    card.addEventListener('mouseleave', () => {
        const keywords = card.querySelectorAll('.slide-keyword-tag');
        keywords.forEach(k => k.style.transform = 'scale(1)');
    });
});

// Search functionality
const searchInput = document.querySelector('.search-input');
searchInput.addEventListener('input', (e) => {
    // Simulate PrezI understanding the query
    if (e.target.value.includes('chart') || e.target.value.includes('graph')) {
        document.querySelectorAll('.filter-chip')[0].style.background = 'rgba(16, 185, 129, 0.2)';
        document.querySelectorAll('.filter-chip')[0].style.borderColor = 'var(--accent-green)';
    }
});

// Animate elements on load
window.addEventListener('load', () => {
    // Animate keyword counts
    document.querySelectorAll('.keyword-count').forEach(count => {
        const value = parseInt(count.textContent);
        let current = 0;
        const increment = value / 20;
        const interval = setInterval(() => {
            current += increment;
            if (current >= value) {
                current = value;
                clearInterval(interval);
            }
            count.textContent = Math.floor(current);
        }, 50);
    });
});

// Mock functions for demo
function filterKeywords(category) {
    console.log('Filtering keywords by category:', category);
}

function updateSlideFiltering() {
    console.log('Updating slide filtering based on selected keywords');
}