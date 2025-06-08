// Thinking Process Demo JavaScript

// Create neural network background
function createNeuralNetwork() {
    const network = document.getElementById('neuralNetwork');
    const nodes = [];
    
    // Create nodes
    for (let i = 0; i < 20; i++) {
        const node = document.createElement('div');
        node.className = 'neural-node';
        node.style.left = Math.random() * 100 + '%';
        node.style.top = Math.random() * 100 + '%';
        node.style.animationDelay = Math.random() * 4 + 's';
        network.appendChild(node);
        nodes.push(node);
    }
    
    // Create connections
    for (let i = 0; i < 10; i++) {
        const connection = document.createElement('div');
        connection.className = 'neural-connection';
        const node1 = nodes[Math.floor(Math.random() * nodes.length)];
        const node2 = nodes[Math.floor(Math.random() * nodes.length)];
        
        const x1 = parseFloat(node1.style.left);
        const y1 = parseFloat(node1.style.top);
        const x2 = parseFloat(node2.style.left);
        const y2 = parseFloat(node2.style.top);
        
        const distance = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
        
        connection.style.width = distance + '%';
        connection.style.left = x1 + '%';
        connection.style.top = y1 + '%';
        connection.style.transform = `rotate(${angle}deg)`;
        connection.style.animationDelay = Math.random() * 3 + 's';
        
        network.appendChild(connection);
    }
}

// Create pattern grid
function createPatternGrid() {
    const grid = document.getElementById('patternGrid');
    for (let i = 0; i < 16; i++) {
        const cell = document.createElement('div');
        cell.className = 'pattern-cell';
        grid.appendChild(cell);
    }
}

// Create knowledge graph
function createKnowledgeGraph() {
    const graph = document.getElementById('knowledgeGraph');
    const nodes = [
        { label: 'Sales', x: 20, y: 30 },
        { label: 'Healthcare', x: 70, y: 20 },
        { label: 'Pitch', x: 40, y: 60 },
        { label: 'ROI', x: 80, y: 70 },
        { label: 'Benefits', x: 30, y: 80 },
        { label: 'Client', x: 60, y: 40 }
    ];
    
    // Create connections first (so they appear behind nodes)
    nodes.forEach((node1, i) => {
        nodes.slice(i + 1).forEach(node2 => {
            if (Math.random() > 0.6) {
                const connection = document.createElement('div');
                connection.className = 'node-connection';
                
                const dx = node2.x - node1.x;
                const dy = node2.y - node1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const angle = Math.atan2(dy, dx) * 180 / Math.PI;
                
                connection.style.width = distance + '%';
                connection.style.left = node1.x + '%';
                connection.style.top = node1.y + '%';
                connection.style.transform = `rotate(${angle}deg)`;
                
                graph.appendChild(connection);
            }
        });
    });
    
    // Create nodes
    nodes.forEach(node => {
        const nodeEl = document.createElement('div');
        nodeEl.className = 'knowledge-node';
        nodeEl.textContent = node.label;
        nodeEl.style.left = node.x + '%';
        nodeEl.style.top = node.y + '%';
        nodeEl.style.transform = 'translate(-50%, -50%)';
        graph.appendChild(nodeEl);
    });
}

// Simulate thinking process
function simulateThinking() {
    const input = document.getElementById('demoInput').value || 'Create a sales pitch for healthcare clients';
    
    // Clear previous thoughts
    const thoughtStream = document.getElementById('thoughtStream');
    thoughtStream.innerHTML = '';
    
    const intentTags = document.getElementById('intentTags');
    intentTags.innerHTML = '';
    
    // Simulate thought generation
    const thoughts = [
        { text: "Understanding request: '" + input + "'", type: 'primary', delay: 0 },
        { text: "Identifying key concepts: sales, healthcare, pitch", type: 'secondary', delay: 500 },
        { text: "Searching 1,247 slides for healthcare content...", type: 'secondary', delay: 1000 },
        { text: "Found 42 relevant slides with healthcare case studies", type: 'insight', delay: 1500 },
        { text: "Analyzing successful pitch patterns...", type: 'secondary', delay: 2000 },
        { text: "Detected winning formula: Problem → Solution → ROI", type: 'insight', delay: 2500 },
        { text: "Building narrative structure...", type: 'primary', delay: 3000 },
        { text: "Applying professional design patterns", type: 'secondary', delay: 3500 },
        { text: "Optimizing for 10-minute presentation", type: 'secondary', delay: 4000 },
        { text: "Ready to create McKinsey-level presentation!", type: 'insight', delay: 4500 }
    ];
    
    // Add thoughts with animation
    thoughts.forEach((thought, index) => {
        setTimeout(() => {
            const bubble = document.createElement('div');
            bubble.className = `thought-bubble ${thought.type}`;
            bubble.textContent = thought.text;
            
            // Random positioning
            bubble.style.left = (10 + Math.random() * 70) + '%';
            bubble.style.top = (10 + Math.random() * 70) + '%';
            
            thoughtStream.appendChild(bubble);
            
            // Add connections between related thoughts
            if (index > 0 && Math.random() > 0.5) {
                const prevBubble = thoughtStream.children[index - 1];
                const connection = document.createElement('div');
                connection.className = 'thought-connection';
                
                const rect1 = prevBubble.getBoundingClientRect();
                const rect2 = bubble.getBoundingClientRect();
                const containerRect = thoughtStream.getBoundingClientRect();
                
                const x1 = rect1.left - containerRect.left + rect1.width / 2;
                const y1 = rect1.top - containerRect.top + rect1.height / 2;
                const x2 = rect2.left - containerRect.left + rect2.width / 2;
                const y2 = rect2.top - containerRect.top + rect2.height / 2;
                
                const distance = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
                const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
                
                connection.style.width = distance + 'px';
                connection.style.left = x1 + 'px';
                connection.style.top = y1 + 'px';
                connection.style.transform = `rotate(${angle}deg)`;
                
                thoughtStream.appendChild(connection);
            }
        }, thought.delay);
    });
    
    // Simulate intent tags
    const intents = [
        { text: 'Create Presentation', primary: true, delay: 500 },
        { text: 'Sales Focus', primary: false, delay: 1000 },
        { text: 'Healthcare Industry', primary: false, delay: 1500 },
        { text: 'Client Pitch', primary: false, delay: 2000 }
    ];
    
    intents.forEach(intent => {
        setTimeout(() => {
            const tag = document.createElement('div');
            tag.className = `intent-tag ${intent.primary ? 'primary' : ''}`;
            tag.textContent = intent.text;
            intentTags.appendChild(tag);
        }, intent.delay);
    });
    
    // Animate progress bars
    animateProgressBar('confidenceBar', 95, 5000);
    animateProgressBar('patternBar', 87, 4000);
    
    // Animate pattern grid
    animatePatternGrid();
    
    // Animate knowledge nodes
    animateKnowledgeNodes();
}

function animateProgressBar(id, targetWidth, duration) {
    const bar = document.getElementById(id);
    const steps = 50;
    const stepDuration = duration / steps;
    let currentStep = 0;
    
    const interval = setInterval(() => {
        currentStep++;
        const progress = (currentStep / steps) * targetWidth;
        bar.style.width = progress + '%';
        
        if (currentStep >= steps) {
            clearInterval(interval);
        }
    }, stepDuration);
}

function animatePatternGrid() {
    const cells = document.querySelectorAll('.pattern-cell');
    cells.forEach((cell, index) => {
        setTimeout(() => {
            if (Math.random() > 0.5) {
                cell.classList.add('active');
                setTimeout(() => cell.classList.remove('active'), 2000);
            }
        }, index * 100 + Math.random() * 500);
    });
}

function animateKnowledgeNodes() {
    const nodes = document.querySelectorAll('.knowledge-node');
    nodes.forEach((node, index) => {
        setTimeout(() => {
            node.style.transform = 'translate(-50%, -50%) scale(1.2)';
            node.style.boxShadow = '0 0 30px rgba(168, 85, 247, 0.5)';
            setTimeout(() => {
                node.style.transform = 'translate(-50%, -50%) scale(1)';
                node.style.boxShadow = 'none';
            }, 500);
        }, index * 300 + Math.random() * 500);
    });
}

// Initialize on load
createNeuralNetwork();
createPatternGrid();
createKnowledgeGraph();

// Auto-simulate on load after a delay
setTimeout(() => simulateThinking(), 1000);