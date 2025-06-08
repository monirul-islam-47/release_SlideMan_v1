// Element Intelligence Demo JavaScript

// Create matrix rain effect
function createMatrixRain() {
    const rain = document.getElementById('matrixRain');
    const characters = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    
    for (let i = 0; i < 20; i++) {
        const column = document.createElement('div');
        column.className = 'matrix-column';
        column.style.left = Math.random() * 100 + '%';
        column.style.animationDelay = Math.random() * 20 + 's';
        column.style.animationDuration = (15 + Math.random() * 10) + 's';
        
        let text = '';
        for (let j = 0; j < 50; j++) {
            text += characters[Math.floor(Math.random() * characters.length)] + '\n';
        }
        column.textContent = text;
        
        rain.appendChild(column);
    }
}

// Toggle overlay visibility
function toggleOverlays() {
    const container = document.getElementById('overlaysContainer');
    const switch_ = document.getElementById('overlaySwitch');
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        switch_.classList.add('active');
    } else {
        container.style.display = 'none';
        switch_.classList.remove('active');
    }
}

// Select element and show details
function selectElement(overlay, type) {
    // Remove previous selection
    document.querySelectorAll('.element-overlay').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Add selection to clicked element
    overlay.classList.add('selected');
    
    // Update details panel based on element type
    const detailsContainer = document.getElementById('elementDetails');
    
    let detailsHTML = '';
    
    switch(type) {
        case 'title':
            detailsHTML = `
                <div class="element-info">
                    <div class="info-row">
                        <span class="info-label">Element Type</span>
                        <span class="info-value">Title Text</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Content</span>
                        <span class="info-value">Q4 2024 Performance</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Font</span>
                        <span class="info-value">Arial Bold 36pt</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Position</span>
                        <span class="info-value">Top Center</span>
                    </div>
                </div>
                
                <div class="ai-analysis">
                    <h4 class="analysis-title">🧠 PrezI Analysis</h4>
                    <div class="analysis-item">
                        <span>Context:</span>
                        <span style="margin-left: 8px;">Quarterly Review</span>
                    </div>
                    <div class="analysis-item">
                        <span>Sentiment:</span>
                        <span style="margin-left: 8px;">Positive</span>
                    </div>
                    <div class="analysis-item">
                        <span>Keywords:</span>
                        <div class="confidence-bar" style="margin-left: 8px;">
                            <div class="confidence-fill" style="width: 95%;"></div>
                        </div>
                        <span style="margin-left: 8px;">95%</span>
                    </div>
                </div>
                
                <div class="tag-input-container">
                    <h4 style="font-size: 14px; margin-bottom: 12px;">Element Keywords</h4>
                    <div class="tag-input-wrapper">
                        <input type="text" class="tag-input" placeholder="Add keyword...">
                        <button class="add-tag-btn">Add</button>
                    </div>
                    <div class="current-tags">
                        <div class="tag">
                            Title
                            <span class="tag-remove">×</span>
                        </div>
                        <div class="tag">
                            Q4
                            <span class="tag-remove">×</span>
                        </div>
                        <div class="tag">
                            Performance
                            <span class="tag-remove">×</span>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 'chart':
            detailsHTML = `
                <div class="element-info">
                    <div class="info-row">
                        <span class="info-label">Element Type</span>
                        <span class="info-value">Chart</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Chart Type</span>
                        <span class="info-value">Column Chart</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Data Points</span>
                        <span class="info-value">12</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Range</span>
                        <span class="info-value">$2.3M - $8.7M</span>
                    </div>
                </div>
                
                <div class="ai-analysis">
                    <h4 class="analysis-title">🧠 PrezI Analysis</h4>
                    <div class="analysis-item">
                        <span>Data Type:</span>
                        <span style="margin-left: 8px;">Revenue Trend</span>
                    </div>
                    <div class="analysis-item">
                        <span>Pattern:</span>
                        <span style="margin-left: 8px;">Upward Growth</span>
                    </div>
                    <div class="analysis-item">
                        <span>Insight:</span>
                        <div class="confidence-bar" style="margin-left: 8px;">
                            <div class="confidence-fill" style="width: 89%;"></div>
                        </div>
                        <span style="margin-left: 8px;">89%</span>
                    </div>
                </div>
                
                <div class="tag-input-container">
                    <h4 style="font-size: 14px; margin-bottom: 12px;">Suggested Keywords</h4>
                    <div class="current-tags">
                        <div class="tag" style="background: rgba(16, 185, 129, 0.1); border-color: var(--accent-green);">
                            + Revenue Chart
                        </div>
                        <div class="tag" style="background: rgba(16, 185, 129, 0.1); border-color: var(--accent-green);">
                            + Monthly Trend
                        </div>
                        <div class="tag" style="background: rgba(16, 185, 129, 0.1); border-color: var(--accent-green);">
                            + Growth Data
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 'bullets':
            detailsHTML = `
                <div class="element-info">
                    <div class="info-row">
                        <span class="info-label">Element Type</span>
                        <span class="info-value">Bullet List</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Items</span>
                        <span class="info-value">4 Points</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Style</span>
                        <span class="info-value">Standard Bullets</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Keywords Found</span>
                        <span class="info-value">8</span>
                    </div>
                </div>
                
                <div class="ai-analysis">
                    <h4 class="analysis-title">🧠 PrezI Analysis</h4>
                    <div class="analysis-item">
                        <span>Content:</span>
                        <span style="margin-left: 8px;">Key Metrics</span>
                    </div>
                    <div class="analysis-item">
                        <span>Numbers:</span>
                        <span style="margin-left: 8px;">142%, 87%, 24%, 72</span>
                    </div>
                    <div class="analysis-item">
                        <span>Topics:</span>
                        <div class="confidence-bar" style="margin-left: 8px;">
                            <div class="confidence-fill" style="width: 92%;"></div>
                        </div>
                        <span style="margin-left: 8px;">92%</span>
                    </div>
                </div>
                
                <div class="tag-input-container">
                    <h4 style="font-size: 14px; margin-bottom: 12px;">Element Keywords</h4>
                    <div class="current-tags">
                        <div class="tag">
                            Key Metrics
                            <span class="tag-remove">×</span>
                        </div>
                        <div class="tag">
                            Results
                            <span class="tag-remove">×</span>
                        </div>
                        <div class="tag" style="background: rgba(168, 85, 247, 0.1); border-color: var(--accent-purple);">
                            ✨ YoY Growth
                        </div>
                    </div>
                </div>
            `;
            break;
    }
    
    detailsContainer.innerHTML = detailsHTML;
    
    // Add tag functionality
    setupTagHandlers();
}

// Setup tag handlers
function setupTagHandlers() {
    // Remove tag handlers
    document.querySelectorAll('.tag-remove').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            this.parentElement.style.transform = 'scale(0)';
            setTimeout(() => this.parentElement.remove(), 200);
        });
    });
    
    // Add tag handler
    const addBtn = document.querySelector('.add-tag-btn');
    const tagInput = document.querySelector('.tag-input');
    
    if (addBtn && tagInput) {
        addBtn.addEventListener('click', () => {
            const value = tagInput.value.trim();
            if (value) {
                const tagsContainer = document.querySelector('.current-tags');
                const newTag = document.createElement('div');
                newTag.className = 'tag';
                newTag.innerHTML = `
                    ${value}
                    <span class="tag-remove">×</span>
                `;
                tagsContainer.appendChild(newTag);
                tagInput.value = '';
                
                // Add remove handler to new tag
                newTag.querySelector('.tag-remove').addEventListener('click', function(e) {
                    e.stopPropagation();
                    newTag.style.transform = 'scale(0)';
                    setTimeout(() => newTag.remove(), 200);
                });
            }
        });
        
        tagInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addBtn.click();
            }
        });
    }
}

// Animate stats on scroll
function animateStats() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statValues = entry.target.querySelectorAll('.stat-value');
                statValues.forEach(stat => {
                    const value = stat.textContent;
                    if (value.includes('%')) {
                        animatePercentage(stat, parseInt(value));
                    } else if (value.includes(',')) {
                        animateNumber(stat, parseInt(value.replace(',', '')));
                    } else if (value.includes('s')) {
                        stat.classList.add('pulse');
                    }
                });
                observer.unobserve(entry.target);
            }
        });
    });
    
    const preziBox = document.querySelector('.prezi-box');
    if (preziBox) {
        observer.observe(preziBox);
    }
}

function animatePercentage(element, target) {
    let current = 0;
    const increment = target / 30;
    const interval = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(interval);
        }
        element.textContent = Math.floor(current) + '%';
    }, 50);
}

function animateNumber(element, target) {
    let current = 0;
    const increment = target / 30;
    const interval = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(interval);
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 50);
}

// Initialize
createMatrixRain();
animateStats();

// Auto-select title element after delay
setTimeout(() => {
    const titleOverlay = document.querySelector('.element-overlay');
    if (titleOverlay) {
        selectElement(titleOverlay, 'title');
    }
}, 1000);