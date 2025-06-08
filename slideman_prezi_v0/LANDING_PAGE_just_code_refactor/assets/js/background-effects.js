// Background Effects and Animation Systems

// Matrix Rain Effect
function createMatrixRain(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    const columns = Math.floor(container.offsetWidth / 20);
    
    container.innerHTML = '';
    container.style.position = 'relative';
    container.style.overflow = 'hidden';

    for (let i = 0; i < columns; i++) {
        const column = document.createElement('div');
        column.className = 'matrix-column';
        column.style.cssText = `
            position: absolute;
            left: ${i * 20}px;
            top: -100%;
            font-family: monospace;
            font-size: 14px;
            color: var(--accent-green);
            animation: matrixFall ${Math.random() * 3 + 2}s linear infinite;
            animation-delay: ${Math.random() * 2}s;
            white-space: nowrap;
            opacity: 0.7;
        `;
        
        // Generate random characters for this column
        let columnText = '';
        for (let j = 0; j < 30; j++) {
            columnText += characters.charAt(Math.floor(Math.random() * characters.length)) + '\n';
        }
        column.textContent = columnText;
        
        container.appendChild(column);
    }
}

// Neural Network Background
function createNeuralNetwork(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const nodeCount = 20;
    const nodes = [];
    
    container.innerHTML = '';
    container.style.position = 'relative';
    container.style.overflow = 'hidden';

    // Create nodes
    for (let i = 0; i < nodeCount; i++) {
        const node = document.createElement('div');
        node.className = 'neural-node';
        node.style.cssText = `
            position: absolute;
            width: 8px;
            height: 8px;
            background: var(--primary);
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: pulse ${Math.random() * 2 + 2}s ease-in-out infinite;
            animation-delay: ${Math.random() * 2}s;
        `;
        
        container.appendChild(node);
        nodes.push({
            element: node,
            x: parseFloat(node.style.left),
            y: parseFloat(node.style.top)
        });
    }

    // Create connections
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const distance = Math.sqrt(
                Math.pow(nodes[i].x - nodes[j].x, 2) + 
                Math.pow(nodes[i].y - nodes[j].y, 2)
            );
            
            if (distance < 30) { // Only connect nearby nodes
                const connection = document.createElement('div');
                connection.className = 'neural-connection';
                
                const angle = Math.atan2(nodes[j].y - nodes[i].y, nodes[j].x - nodes[i].x);
                const length = distance;
                
                connection.style.cssText = `
                    position: absolute;
                    left: ${nodes[i].x}%;
                    top: ${nodes[i].y}%;
                    width: ${length}%;
                    height: 1px;
                    background: linear-gradient(90deg, transparent 0%, var(--primary) 50%, transparent 100%);
                    transform-origin: 0 0;
                    transform: rotate(${angle}rad);
                    animation: dataFlow ${Math.random() * 3 + 3}s ease-in-out infinite;
                    animation-delay: ${Math.random() * 2}s;
                    opacity: 0.3;
                `;
                
                container.appendChild(connection);
            }
        }
    }
}

// Particle System
function createParticleSystem(containerId, particleCount = 50) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';
    container.style.position = 'relative';
    container.style.overflow = 'hidden';

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--primary);
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: 100%;
            opacity: 0.6;
            animation: particleFloat ${Math.random() * 8 + 8}s linear infinite;
            animation-delay: ${Math.random() * 8}s;
        `;
        
        container.appendChild(particle);
    }
}

// Gradient Orbs Animation
function createGradientOrbs(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const orbConfigs = [
        {
            size: 200,
            color: 'rgba(102, 126, 234, 0.4)',
            position: { top: '20%', left: '10%' },
            delay: '0s'
        },
        {
            size: 150,
            color: 'rgba(168, 85, 247, 0.3)',
            position: { top: '60%', right: '15%' },
            delay: '-4s'
        },
        {
            size: 300,
            color: 'rgba(59, 130, 246, 0.2)',
            position: { bottom: '10%', left: '30%' },
            delay: '-8s'
        }
    ];

    orbConfigs.forEach((config, index) => {
        const orb = document.createElement('div');
        orb.className = `gradient-orb gradient-orb-${index + 1}`;
        orb.style.cssText = `
            position: absolute;
            width: ${config.size}px;
            height: ${config.size}px;
            background: radial-gradient(circle, ${config.color} 0%, transparent 70%);
            border-radius: 50%;
            filter: blur(40px);
            animation: orbFloat 12s ease-in-out infinite;
            animation-delay: ${config.delay};
        `;
        
        // Set position
        Object.keys(config.position).forEach(key => {
            orb.style[key] = config.position[key];
        });
        
        container.appendChild(orb);
    });
}

// Breathing Animation for Elements
function addBreathingAnimation(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('breathe');
    }
}

// Morphing Animation for Shapes
function addMorphingAnimation(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('morph');
    }
}

// Initialize background effects based on page type
function initializeBackgroundEffects(pageType) {
    switch(pageType) {
        case 'thinking-process':
            createNeuralNetwork('neuralBackground');
            break;
        case 'element-intelligence':
            createMatrixRain('matrixBackground');
            break;
        case 'hero':
            createGradientOrbs('heroBackground');
            createParticleSystem('heroParticles', 30);
            break;
        case 'keyword-integration':
            createParticleSystem('keywordParticles', 20);
            break;
        default:
            // Create subtle particle system for all pages
            createParticleSystem('defaultParticles', 15);
    }
}

// Add CSS keyframes for animations
function addBackgroundCSS() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes matrixFall {
            to {
                transform: translateY(100vh);
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
                opacity: 0.6;
            }
            50% {
                transform: scale(1.5);
                opacity: 1;
            }
        }
        
        @keyframes dataFlow {
            0% {
                opacity: 0;
                transform: scaleX(0);
            }
            50% {
                opacity: 1;
                transform: scaleX(1);
            }
            100% {
                opacity: 0;
                transform: scaleX(0);
            }
        }
        
        @keyframes particleFloat {
            0% {
                transform: translateY(0) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 0.6;
            }
            90% {
                opacity: 0.6;
            }
            100% {
                transform: translateY(-100vh) rotate(360deg);
                opacity: 0;
            }
        }
        
        @keyframes orbFloat {
            0%, 100% { 
                transform: translate(0, 0) scale(1); 
                opacity: 0.6;
            }
            25% { 
                transform: translate(30px, -20px) scale(1.1); 
                opacity: 0.8;
            }
            50% { 
                transform: translate(-20px, -30px) scale(0.9); 
                opacity: 0.4;
            }
            75% { 
                transform: translate(-30px, 20px) scale(1.05); 
                opacity: 0.7;
            }
        }
    `;
    document.head.appendChild(style);
}

// Initialize background effects when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    addBackgroundCSS();
});