// Landing Page JavaScript Functions

// Initialize loading system
function initLoadingSystem() {
    const updateProgress = () => {
        const loadingSkeleton = document.getElementById('loadingSkeleton');
        const mainContent = document.getElementById('mainContent');
        
        if (!loadingSkeleton || !mainContent) return;
        
        // Hide loading skeleton
        loadingSkeleton.style.transition = 'opacity 0.5s ease';
        loadingSkeleton.style.opacity = '0';
        
        setTimeout(() => {
            loadingSkeleton.style.display = 'none';
            
            // Show main content
            mainContent.style.visibility = 'visible';
            mainContent.style.opacity = '0';
            mainContent.style.transition = 'opacity 1s ease';
            
            // Trigger content reveal
            setTimeout(() => {
                mainContent.style.opacity = '1';
                revealContent();
            }, 100);
        }, 500);
    };
    
    const revealContent = () => {
        // Progressive content reveal with staggered animations
        const sections = document.querySelectorAll('.hero, .section');
        
        sections.forEach((section, index) => {
            setTimeout(() => {
                section.classList.add('fade-in-up');
                
                // Add optimistic UI updates
                const interactiveElements = section.querySelectorAll('.btn, .feature-card, .demo-card, .pricing-card');
                interactiveElements.forEach((element, i) => {
                    setTimeout(() => {
                        element.classList.add('fade-in-scale');
                    }, i * 100);
                });
            }, index * 200);
        });
        
        // Initialize other components after content is revealed
        setTimeout(() => {
            initializeAllComponents();
        }, 1000);
    };
    
    const initializeAllComponents = () => {
        // Initialize all the components
        initAvatarAnimations();
        
        // Initialize particle systems (if not on mobile)
        if (window.innerWidth > 768) {
            initParticleEffects();
        }
        
        // Start stats counter animation
        startStatsAnimation();
        
        // Initialize live stats counters
        initLiveStats();
        
        // Initialize chat widget as minimized
        const chatWidget = document.getElementById('chatWidget');
        if (chatWidget) {
            chatWidget.classList.add('minimized');
        }
    };
    
    // Check if page is already loaded
    if (document.readyState === 'complete') {
        setTimeout(updateProgress, 500);
    } else {
        window.addEventListener('load', () => {
            setTimeout(updateProgress, 500);
        });
    }
}

// Avatar animations
function initAvatarAnimations() {
    const avatar = document.querySelector('.prezi-avatar-main');
    if (!avatar) return;
    
    // Mouse following for avatar
    document.addEventListener('mousemove', (e) => {
        if (window.innerWidth <= 768) return; // Skip on mobile
        
        const rect = avatar.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        const deltaX = (e.clientX - centerX) / 10;
        const deltaY = (e.clientY - centerY) / 10;
        
        avatar.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(1)`;
    });
    
    // Button click excitement
    const buttons = document.querySelectorAll('.btn, .hero-cta');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            avatar.style.animation = 'none';
            avatar.offsetHeight; // Trigger reflow
            avatar.style.animation = 'bounce 0.6s ease';
        });
    });
}

// Particle effects
function initParticleEffects() {
    const particleContainer = document.getElementById('floatingParticles');
    if (!particleContainer) return;
    
    for (let i = 0; i < 8; i++) {
        const particle = document.createElement('div');
        particle.className = 'floating-particle';
        particle.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(168, 85, 247, 0.6);
            border-radius: 50%;
            animation: float ${3 + Math.random() * 2}s ease-in-out infinite;
            animation-delay: ${Math.random() * 2}s;
            top: ${Math.random() * 100}%;
            left: ${Math.random() * 100}%;
        `;
        particleContainer.appendChild(particle);
    }
}

// Stats animation
function startStatsAnimation() {
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(stat => {
        const target = parseInt(stat.getAttribute('data-target'));
        let current = 0;
        const increment = target / 50;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            stat.textContent = Math.floor(current);
        }, 40);
    });
}

// Live stats
function initLiveStats() {
    const liveVisitors = document.getElementById('liveVisitors');
    const presentationsCreated = document.getElementById('presentationsCreated');
    const timeSaved = document.getElementById('timeSaved');
    
    if (!liveVisitors || !presentationsCreated || !timeSaved) return;
    
    // Base values
    const baseVisitors = 2847;
    const basePresentations = 15432;
    const baseTimeSaved = 89235;
    
    // Update functions
    const updateVisitors = () => {
        const variation = Math.floor(Math.random() * 20) - 10; // ±10
        const newCount = Math.max(baseVisitors + variation, baseVisitors - 50);
        animateNumber(liveVisitors, parseInt(liveVisitors.textContent.replace(',', '')), newCount);
    };
    
    const updatePresentations = () => {
        const increment = Math.floor(Math.random() * 5) + 1; // 1-5
        const currentCount = parseInt(presentationsCreated.textContent.replace(',', ''));
        const newCount = currentCount + increment;
        animateNumber(presentationsCreated, currentCount, newCount);
    };
    
    const updateTimeSaved = () => {
        const increment = Math.floor(Math.random() * 20) + 10; // 10-30
        const currentCount = parseInt(timeSaved.textContent.replace(',', ''));
        const newCount = currentCount + increment;
        animateNumber(timeSaved, currentCount, newCount);
    };
    
    const animateNumber = (element, start, end) => {
        const duration = 1000;
        const startTime = Date.now();
        
        const update = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };
        
        update();
    };
    
    // Start intervals
    setInterval(updateVisitors, 8000 + Math.random() * 7000); // 8-15 seconds
    setInterval(updatePresentations, 45000 + Math.random() * 15000); // 45-60 seconds
    setInterval(updateTimeSaved, 30000 + Math.random() * 10000); // 30-40 seconds
}

// Chat widget functionality
let chatMinimized = true;

function toggleChat() {
    const chatWidget = document.getElementById('chatWidget');
    chatMinimized = !chatMinimized;
    
    if (chatMinimized) {
        chatWidget.classList.add('minimized');
    } else {
        chatWidget.classList.remove('minimized');
        // Focus input when opening
        setTimeout(() => {
            document.getElementById('chatInput').focus();
        }, 300);
    }
}

function askQuestion(type) {
    const questions = {
        security: "How secure is PrezI?",
        models: "What AI models do you use?", 
        pricing: "How much does it cost?",
        accuracy: "How accurate is element detection?"
    };
    
    const answers = {
        security: "PrezI takes security seriously! We use enterprise-grade encryption, GDPR compliance, SOC 2 Type II certification, and zero-trust architecture. Your presentations are processed locally when possible, and we never store sensitive content without explicit permission.",
        models: "PrezI uses a hybrid approach: GPT-4 for natural language understanding, specialized computer vision models for element detection (95%+ accuracy), and our proprietary SlideMan AI for presentation logic. Everything is optimized for speed and accuracy.",
        pricing: "PrezI starts at $29/month for individuals (Starter plan), $89/month for professionals, and custom enterprise pricing. All plans include unlimited slide analysis, AI presentation building, and 24/7 support. Try it free for 14 days!",
        accuracy: "Our element detection achieves 95%+ accuracy across text, charts, images, and tables. We continuously train on diverse presentation styles and use human feedback to improve. The AI gets smarter with every presentation you process!"
    };
    
    addMessage('user', questions[type]);
    
    setTimeout(() => {
        addMessage('bot', answers[type]);
    }, 1000);
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message) {
        addMessage('user', message);
        input.value = '';
        
        // Simulate AI response
        setTimeout(() => {
            const response = generateAIResponse(message);
            addMessage('bot', response);
        }, 1500);
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function addMessage(type, content) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}-message`;
    
    const avatar = type === 'bot' ? '🤖' : '👤';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p>${content}</p>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function generateAIResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('secure') || lowerMessage.includes('privacy')) {
        return "Security is our top priority! PrezI uses bank-level encryption, processes data locally when possible, and is fully GDPR compliant. We're also SOC 2 Type II certified and use zero-trust architecture.";
    } else if (lowerMessage.includes('price') || lowerMessage.includes('cost')) {
        return "PrezI starts at just $29/month for individuals. That's less than the cost of a single presentation consultant hour, but you get unlimited AI-powered slide management! Want to see our full pricing? Check out the pricing section above.";
    } else if (lowerMessage.includes('accurate') || lowerMessage.includes('precision')) {
        return "Our element detection is 95%+ accurate! We've trained on millions of slides across different industries and continuously improve based on user feedback. The AI gets smarter every day.";
    } else if (lowerMessage.includes('model') || lowerMessage.includes('ai')) {
        return "PrezI combines multiple AI models: GPT-4 for language understanding, specialized computer vision for element detection, and our proprietary SlideMan AI for presentation logic. It's like having a team of AI experts working on your slides!";
    } else if (lowerMessage.includes('time') || lowerMessage.includes('save')) {
        return "PrezI typically saves 80-90% of your presentation prep time! What used to take 4-5 hours now takes just minutes. Our users report saving 10+ hours per week on average.";
    } else {
        return "Great question! PrezI is designed to make presentation creation effortless and professional. Is there something specific about our AI-powered slide management you'd like to know more about?";
    }
}

// Global functions
window.toggleChat = toggleChat;
window.askQuestion = askQuestion;
window.sendMessage = sendMessage;
window.handleChatKeypress = handleChatKeypress;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initLoadingSystem();
});