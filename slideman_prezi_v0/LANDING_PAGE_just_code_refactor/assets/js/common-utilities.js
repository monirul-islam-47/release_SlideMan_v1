// Common Utility Functions

// Animation utilities
function animateValue(element, start, end, duration) {
    const startTime = performance.now();
    const startNum = parseInt(start);
    const endNum = parseInt(end);
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentValue = Math.floor(startNum + (endNum - startNum) * progress);
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    requestAnimationFrame(updateValue);
}

// Progress bar animation
function animateProgressBar(element, targetWidth, duration = 1000) {
    const startWidth = parseFloat(element.style.width) || 0;
    const startTime = performance.now();
    
    function updateProgress(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentWidth = startWidth + (targetWidth - startWidth) * progress;
        element.style.width = currentWidth + '%';
        
        if (progress < 1) {
            requestAnimationFrame(updateProgress);
        }
    }
    requestAnimationFrame(updateProgress);
}

// Fade in animation for elements
function fadeInElement(element, duration = 500) {
    element.style.opacity = '0';
    element.style.display = 'block';
    
    const startTime = performance.now();
    
    function updateOpacity(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        element.style.opacity = progress;
        
        if (progress < 1) {
            requestAnimationFrame(updateOpacity);
        }
    }
    requestAnimationFrame(updateOpacity);
}

// Show tooltip
function showTooltip(element, text, position = 'top') {
    const tooltip = document.getElementById('tooltip') || createTooltip();
    tooltip.textContent = text;
    tooltip.className = `tooltip tooltip-${position}`;
    
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left, top;
    switch(position) {
        case 'top':
            left = rect.left + (rect.width - tooltipRect.width) / 2;
            top = rect.top - tooltipRect.height - 8;
            break;
        case 'bottom':
            left = rect.left + (rect.width - tooltipRect.width) / 2;
            top = rect.bottom + 8;
            break;
        case 'left':
            left = rect.left - tooltipRect.width - 8;
            top = rect.top + (rect.height - tooltipRect.height) / 2;
            break;
        case 'right':
            left = rect.right + 8;
            top = rect.top + (rect.height - tooltipRect.height) / 2;
            break;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.classList.add('active');
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.classList.remove('active');
    }
}

function createTooltip() {
    const tooltip = document.createElement('div');
    tooltip.id = 'tooltip';
    tooltip.className = 'tooltip';
    document.body.appendChild(tooltip);
    return tooltip;
}

// Theme management
function toggleTheme() {
    const theme = document.documentElement.getAttribute('data-theme');
    const newTheme = theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Element selection utilities
function toggleElementSelection(element) {
    element.classList.toggle('selected');
    return element.classList.contains('selected');
}

function selectElement(element) {
    element.classList.add('selected');
}

function deselectElement(element) {
    element.classList.remove('selected');
}

function deselectAll(selector) {
    document.querySelectorAll(selector).forEach(el => {
        el.classList.remove('selected');
    });
}

// Intersection Observer for scroll animations
function setupScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Initialize common utilities when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    setupScrollAnimations();
});