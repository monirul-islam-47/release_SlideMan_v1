        // Loading System - Progressive Content Reveal
        const initLoadingSystem = () => {
            const loadingSkeleton = document.getElementById('loadingSkeleton');
            const mainContent = document.getElementById('mainContent');
            const progressFill = document.getElementById('loadingProgressFill');
            const progressText = document.getElementById('loadingProgressText');
            
            const loadingSteps = [
                { progress: 0, text: 'Initializing PrezI...' },
                { progress: 15, text: 'Loading AI models...' },
                { progress: 30, text: 'Preparing presentation engine...' },
                { progress: 45, text: 'Setting up element detection...' },
                { progress: 60, text: 'Configuring smart search...' },
                { progress: 75, text: 'Optimizing performance...' },
                { progress: 90, text: 'Almost ready...' },
                { progress: 100, text: 'Welcome to PrezI!' }
            ];
            
            let currentStep = 0;
            
            // Simulate realistic loading with variable timing
            const updateProgress = () => {
                if (currentStep < loadingSteps.length) {
                    const step = loadingSteps[currentStep];
                    progressFill.style.width = step.progress + '%';
                    progressText.textContent = step.text;
                    
                    currentStep++;
                    
                    // Variable timing for more realistic feel
                    const delay = currentStep <= 2 ? 800 : 
                                 currentStep <= 5 ? 600 : 
                                 currentStep <= 7 ? 400 : 800;
                    
                    setTimeout(updateProgress, delay);
                } else {
                    // Loading complete, show content
                    setTimeout(() => {
                        showMainContent();
                    }, 500);
                }
            };
            
            const showMainContent = () => {
                // Hide skeleton with fade out
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
                // Initialize all the components that were previously in window.load
                if (typeof initRequestForm === 'function') initRequestForm();
                if (typeof initLivePerformance === 'function') initLivePerformance();
                if (typeof initOnboardingVideo === 'function') initOnboardingVideo();
                if (typeof initSandbox === 'function') initSandbox();
                if (typeof initSwipeGestures === 'function') initSwipeGestures();
                
                // Initialize chat widget as minimized
                const chatWidget = document.getElementById('chatWidget');
                if (chatWidget) {
                    chatWidget.classList.add('minimized');
                }
                
                // Initialize avatar animations
                initAvatarAnimations();
                
                // Initialize particle systems (if not on mobile)
                if (window.innerWidth > 768) {
                    initParticleEffects();
                }
                
                // Start stats counter animation
                startStatsAnimation();
                
                // Initialize live stats counters
                initLiveStats();
            };
            
            const initAvatarAnimations = () => {
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
                
                // Global error handler for avatar shake
                window.triggerAvatarError = (message) => {
                    avatar.style.animation = 'none';
                    avatar.offsetHeight; // Trigger reflow
                    avatar.style.animation = 'errorShake 0.5s ease';
                    
                    // Optional: Show error message near avatar
                    if (message) {
                        showAvatarMessage(message, 'error');
                    }
                };
                
                // Global success handler for avatar celebration
                window.triggerAvatarSuccess = (message) => {
                    avatar.style.animation = 'none';
                    avatar.offsetHeight; // Trigger reflow
                    avatar.style.animation = 'bounce 0.6s ease';
                    
                    if (message) {
                        showAvatarMessage(message, 'success');
                    }
                };
                
                const showAvatarMessage = (message, type) => {
                    const existingMessage = document.querySelector('.avatar-message');
                    if (existingMessage) {
                        existingMessage.remove();
                    }
                    
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `avatar-message ${type}`;
                    messageDiv.textContent = message;
                    messageDiv.style.cssText = `
                        position: absolute;
                        top: -60px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: ${type === 'error' ? 'var(--accent-red)' : 'var(--accent-green)'};
                        color: white;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 14px;
                        font-weight: 600;
                        z-index: 100;
                        opacity: 0;
                        transition: all 0.3s ease;
                        pointer-events: none;
                        white-space: nowrap;
                    `;
                    
                    avatar.parentElement.style.position = 'relative';
                    avatar.parentElement.appendChild(messageDiv);
                    
                    // Animate in
                    setTimeout(() => {
                        messageDiv.style.opacity = '1';
                        messageDiv.style.transform = 'translateX(-50%) translateY(-10px)';
                    }, 100);
                    
                    // Animate out
                    setTimeout(() => {
                        messageDiv.style.opacity = '0';
                        messageDiv.style.transform = 'translateX(-50%) translateY(-20px)';
                        setTimeout(() => messageDiv.remove(), 300);
                    }, 3000);
                };
            };
            
            const initParticleEffects = () => {
                // Initialize floating particles around avatar
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
            };
            
            const startStatsAnimation = () => {
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
            };
            
            const initLiveStats = () => {
                const liveVisitors = document.getElementById('liveVisitors');
                const presentationsCreated = document.getElementById('presentationsCreated');
                const timeSaved = document.getElementById('timeSaved');
                
                if (!liveVisitors || !presentationsCreated || !timeSaved) return;
                
                // Base values
                const baseVisitors = 2847;
                const basePresentations = 15432;
                const baseTimeSaved = 89235;
                
                // Update live visitor count every 5-15 seconds
                const updateVisitors = () => {
                    const variation = Math.floor(Math.random() * 20) - 10; // ±10
                    const newCount = Math.max(baseVisitors + variation, baseVisitors - 50);
                    animateNumber(liveVisitors, parseInt(liveVisitors.textContent.replace(',', '')), newCount);
                };
                
                // Update presentations count every 30-60 seconds
                const updatePresentations = () => {
                    const increment = Math.floor(Math.random() * 5) + 1; // 1-5
                    const currentCount = parseInt(presentationsCreated.textContent.replace(',', ''));
                    const newCount = currentCount + increment;
                    animateNumber(presentationsCreated, currentCount, newCount);
                };
                
                // Update time saved every 20-40 seconds
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
            };
            
            // Check if page is already loaded (in case script runs after load)
            if (document.readyState === 'complete') {
                setTimeout(updateProgress, 500);
            } else {
                window.addEventListener('load', () => {
                    setTimeout(updateProgress, 500);
                });
            }
        };
        
        // Initialize loading system immediately
        initLoadingSystem();
        
        // Chat widget functionality
        let chatMinimized = true;
        
        window.toggleChat = () => {
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
        };
        
        window.askQuestion = (type) => {
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
        };
        
        window.sendMessage = () => {
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
        };
        
        window.handleChatKeypress = (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        };
        
        const addMessage = (type, content) => {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${type}-message`;
            
            const avatar = type === 'bot' ? '🤖' : '👤';
            const messageClass = type === 'bot' ? 'bot-message' : 'user-message';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <p>${content}</p>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        };
        
        const generateAIResponse = (message) => {
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
        };
        
        // Initialize chat widget as minimized
        window.addEventListener('load', () => {
            document.getElementById('chatWidget').classList.add('minimized');
        });
        
        // Swipe gesture functionality for demo cards (mobile)
        const initSwipeGestures = () => {
            const demoGrid = document.querySelector('.demo-grid');
            const demoCards = document.querySelectorAll('.demo-card');
            
            if (!demoGrid || demoCards.length === 0) return;
            
            let startX = 0;
            let startY = 0;
            let currentCardIndex = 0;
            let isSwipeEnabled = window.innerWidth <= 768;
            
            // Re-check on resize
            window.addEventListener('resize', () => {
                isSwipeEnabled = window.innerWidth <= 768;
            });
            
            // Touch event handlers
            const handleTouchStart = (e) => {
                if (!isSwipeEnabled) return;
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
            };
            
            const handleTouchMove = (e) => {
                if (!isSwipeEnabled) return;
                e.preventDefault(); // Prevent scrolling
            };
            
            const handleTouchEnd = (e) => {
                if (!isSwipeEnabled) return;
                
                const endX = e.changedTouches[0].clientX;
                const endY = e.changedTouches[0].clientY;
                const deltaX = endX - startX;
                const deltaY = endY - startY;
                
                // Only swipe if horizontal movement is greater than vertical
                if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                    if (deltaX > 0) {
                        // Swipe right - previous card
                        navigateDemoCard('prev');
                    } else {
                        // Swipe left - next card
                        navigateDemoCard('next');
                    }
                }
            };
            
            // Add touch listeners to demo grid
            demoGrid.addEventListener('touchstart', handleTouchStart, { passive: true });
            demoGrid.addEventListener('touchmove', handleTouchMove, { passive: false });
            demoGrid.addEventListener('touchend', handleTouchEnd, { passive: true });
            
            // Demo card navigation function
            const navigateDemoCard = (direction) => {
                const totalCards = demoCards.length;
                
                if (direction === 'next') {
                    currentCardIndex = (currentCardIndex + 1) % totalCards;
                } else {
                    currentCardIndex = (currentCardIndex - 1 + totalCards) % totalCards;
                }
                
                // Hide all cards
                demoCards.forEach((card, index) => {
                    card.style.display = 'none';
                    card.classList.remove('active-demo-card');
                });
                
                // Show current card with animation
                const currentCard = demoCards[currentCardIndex];
                currentCard.style.display = 'block';
                currentCard.classList.add('active-demo-card');
                
                // Add swipe animation
                currentCard.style.transform = direction === 'next' ? 'translateX(100%)' : 'translateX(-100%)';
                currentCard.style.transition = 'transform 0.3s ease';
                
                // Animate to center
                setTimeout(() => {
                    currentCard.style.transform = 'translateX(0)';
                }, 10);
                
                // Update swipe indicators
                updateSwipeIndicators();
                
                // Haptic feedback on mobile
                if (navigator.vibrate) {
                    navigator.vibrate(50);
                }
            };
            
            // Create swipe indicators for mobile
            const createSwipeIndicators = () => {
                if (!isSwipeEnabled || demoCards.length <= 1) return;
                
                const indicatorsContainer = document.createElement('div');
                indicatorsContainer.className = 'swipe-indicators';
                indicatorsContainer.innerHTML = `
                    <div class="swipe-dots">
                        ${Array.from(demoCards).map((_, index) => 
                            `<div class="swipe-dot ${index === 0 ? 'active' : ''}" data-index="${index}"></div>`
                        ).join('')}
                    </div>
                    <div class="swipe-hint">← Swipe to explore demos →</div>
                `;
                
                demoGrid.parentNode.insertBefore(indicatorsContainer, demoGrid.nextSibling);
                
                // Add click handlers to dots
                const dots = indicatorsContainer.querySelectorAll('.swipe-dot');
                dots.forEach((dot, index) => {
                    dot.addEventListener('click', () => {
                        currentCardIndex = index;
                        navigateDemoCard('direct');
                    });
                });
            };
            
            // Update indicators
            const updateSwipeIndicators = () => {
                const dots = document.querySelectorAll('.swipe-dot');
                dots.forEach((dot, index) => {
                    dot.classList.toggle('active', index === currentCardIndex);
                });
            };
            
            // Initialize on mobile
            if (isSwipeEnabled) {
                // Hide all cards except first
                demoCards.forEach((card, index) => {
                    if (index !== 0) {
                        card.style.display = 'none';
                    } else {
                        card.classList.add('active-demo-card');
                    }
                });
                
                createSwipeIndicators();
            }
        };
        
        // Initialize swipe gestures
        window.addEventListener('load', initSwipeGestures);
        
        // Urgency Elements
        function updateSpotsRemaining() {
            const spotsElement = document.getElementById('spotsCount');
            if (spotsElement) {
                let currentSpots = parseInt(spotsElement.textContent);
                // Simulate spots filling up slowly
                if (Math.random() < 0.1 && currentSpots > 12) { // 10% chance every update, minimum 12 spots
                    currentSpots--;
                    spotsElement.textContent = currentSpots;
                    
                    // Add urgency animation when spots get low
                    if (currentSpots <= 25) {
                        spotsElement.parentElement.style.animation = 'spotsGlow 1s ease-in-out infinite';
                    }
                }
            }
        }
        
        // Countdown Timer
        function updateCountdown() {
            const days = document.getElementById('countdownDays');
            const hours = document.getElementById('countdownHours');
            const minutes = document.getElementById('countdownMinutes');
            const seconds = document.getElementById('countdownSeconds');
            
            if (!days || !hours || !minutes || !seconds) return;
            
            // Set target date (5 days from now)
            const targetDate = new Date();
            targetDate.setDate(targetDate.getDate() + 5);
            targetDate.setHours(0, 0, 0, 0);
            
            const now = new Date().getTime();
            const distance = targetDate - now;
            
            if (distance > 0) {
                const d = Math.floor(distance / (1000 * 60 * 60 * 24));
                const h = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const m = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const s = Math.floor((distance % (1000 * 60)) / 1000);
                
                days.textContent = d.toString().padStart(2, '0');
                hours.textContent = h.toString().padStart(2, '0');
                minutes.textContent = m.toString().padStart(2, '0');
                seconds.textContent = s.toString().padStart(2, '0');
            }
        }
        
        // Update urgency elements
        setInterval(updateSpotsRemaining, 15000); // Every 15 seconds
        setInterval(updateCountdown, 1000); // Every second
        updateCountdown(); // Initial call
        
        // Accessibility Enhancements
        function initializeAccessibility() {
            // Add keyboard navigation for interactive elements
            const interactiveElements = document.querySelectorAll('[tabindex], button, a, input, textarea, select');
            
            interactiveElements.forEach(element => {
                element.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        if (this.tagName !== 'INPUT' && this.tagName !== 'TEXTAREA') {
                            e.preventDefault();
                            this.click();
                        }
                    }
                });
            });
            
            // Add skip to main content link
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: var(--primary);
                color: white;
                padding: 8px;
                text-decoration: none;
                border-radius: 4px;
                z-index: 10000;
                transition: top 0.3s;
            `;
            skipLink.addEventListener('focus', () => {
                skipLink.style.top = '6px';
            });
            skipLink.addEventListener('blur', () => {
                skipLink.style.top = '-40px';
            });
            document.body.insertBefore(skipLink, document.body.firstChild);
            
            // Add main content landmark
            const heroSection = document.querySelector('.hero');
            if (heroSection) {
                heroSection.id = 'main-content';
                heroSection.setAttribute('role', 'main');
            }
            
            // Enhance button accessibility
            document.querySelectorAll('button').forEach(button => {
                if (!button.getAttribute('aria-label') && !button.textContent.trim()) {
                    button.setAttribute('aria-label', 'Interactive button');
                }
            });
            
            // Add alt text to decorative images
            document.querySelectorAll('img:not([alt])').forEach(img => {
                img.setAttribute('alt', '');
                img.setAttribute('role', 'presentation');
            });
            
            // Announce live regions for dynamic content
            const spotsElement = document.getElementById('spotsCount');
            if (spotsElement) {
                spotsElement.setAttribute('aria-live', 'polite');
                spotsElement.setAttribute('aria-label', 'Remaining spots');
            }
            
            // Add reduced motion preference
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.documentElement.style.setProperty('--animation-duration', '0.01ms');
                document.querySelectorAll('*').forEach(el => {
                    el.style.animationDuration = '0.01ms !important';
                    el.style.transitionDuration = '0.01ms !important';
                });
            }
        }
        
        // Progressive Web App features
        function initializePWA() {
            // Register service worker
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('Service Worker registered:', registration);
                    })
                    .catch(error => {
                        console.log('Service Worker registration failed:', error);
                    });
            }
            
            // Add to home screen prompt
            let deferredPrompt;
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                deferredPrompt = e;
                
                // Show install button
                const installButton = document.createElement('button');
                installButton.textContent = '📱 Install PrezI App';
                installButton.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    left: 20px;
                    background: var(--primary);
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    z-index: 1000;
                    font-weight: 600;
                `;
                installButton.addEventListener('click', () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('User accepted the install prompt');
                        }
                        deferredPrompt = null;
                        installButton.remove();
                    });
                });
                document.body.appendChild(installButton);
                
                // Hide after 10 seconds
                setTimeout(() => {
                    if (installButton) installButton.remove();
                }, 10000);
            });
        }
        
        // Sound & Haptics System
        class SoundManager {
            constructor() {
                this.soundEnabled = localStorage.getItem('prezI_soundEnabled') !== 'false';
                this.ambientEnabled = localStorage.getItem('prezI_ambientEnabled') === 'true';
                this.audioContext = null;
                this.ambientGain = null;
                this.ambientOscillator = null;
                this.soundEffects = {};
                this.init();
            }
            
            async init() {
                try {
                    // Initialize Web Audio API
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    this.ambientGain = this.audioContext.createGain();
                    this.ambientGain.connect(this.audioContext.destination);
                    this.ambientGain.gain.value = 0.1;
                    
                    // Create sound effects using oscillators
                    this.createSoundEffects();
                    
                    // Update UI
                    this.updateUI();
                    
                    // Start ambient sounds if enabled
                    if (this.ambientEnabled) {
                        this.startAmbient();
                    }
                    
                } catch (e) {
                    console.log('Web Audio API not supported:', e);
                    this.soundEnabled = false;
                }
            }
            
            createSoundEffects() {
                // Whoosh sound for page load
                this.soundEffects.whoosh = () => this.playTone(200, 150, 0.1, 'sine');
                
                // Click sound for buttons
                this.soundEffects.click = () => this.playTone(800, 100, 0.05, 'square');
                
                // Success chime for CTA
                this.soundEffects.success = () => {
                    this.playTone(523, 200, 0.1, 'sine'); // C5
                    setTimeout(() => this.playTone(659, 200, 0.1, 'sine'), 100); // E5
                    setTimeout(() => this.playTone(784, 300, 0.1, 'sine'), 200); // G5
                };
                
                // Hover sound for interactive elements
                this.soundEffects.hover = () => this.playTone(400, 50, 0.03, 'triangle');
            }
            
            playTone(frequency, duration, volume = 0.1, waveType = 'sine') {
                if (!this.soundEnabled || !this.audioContext) return;
                
                try {
                    const oscillator = this.audioContext.createOscillator();
                    const gainNode = this.audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(this.audioContext.destination);
                    
                    oscillator.type = waveType;
                    oscillator.frequency.value = frequency;
                    
                    gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
                    gainNode.gain.linearRampToValueAtTime(volume, this.audioContext.currentTime + 0.01);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);
                    
                    oscillator.start(this.audioContext.currentTime);
                    oscillator.stop(this.audioContext.currentTime + duration / 1000);
                } catch (e) {
                    console.log('Error playing tone:', e);
                }
            }
            
            startAmbient() {
                if (!this.soundEnabled || !this.audioContext || this.ambientOscillator) return;
                
                try {
                    // Create subtle ambient drone
                    this.ambientOscillator = this.audioContext.createOscillator();
                    const filter = this.audioContext.createBiquadFilter();
                    
                    filter.type = 'lowpass';
                    filter.frequency.value = 200;
                    filter.Q.value = 1;
                    
                    this.ambientOscillator.connect(filter);
                    filter.connect(this.ambientGain);
                    
                    this.ambientOscillator.type = 'sawtooth';
                    this.ambientOscillator.frequency.value = 55; // Low A
                    
                    // Add subtle frequency modulation
                    const lfo = this.audioContext.createOscillator();
                    const lfoGain = this.audioContext.createGain();
                    lfo.connect(lfoGain);
                    lfoGain.connect(this.ambientOscillator.frequency);
                    
                    lfo.frequency.value = 0.1;
                    lfoGain.gain.value = 2;
                    
                    this.ambientOscillator.start();
                    lfo.start();
                } catch (e) {
                    console.log('Error starting ambient:', e);
                }
            }
            
            stopAmbient() {
                if (this.ambientOscillator) {
                    this.ambientOscillator.stop();
                    this.ambientOscillator = null;
                }
            }
            
            toggleSound() {
                this.soundEnabled = !this.soundEnabled;
                localStorage.setItem('prezI_soundEnabled', this.soundEnabled);
                this.updateUI();
                
                if (!this.soundEnabled) {
                    this.stopAmbient();
                    this.ambientEnabled = false;
                    localStorage.setItem('prezI_ambientEnabled', false);
                }
            }
            
            toggleAmbient() {
                if (!this.soundEnabled) return;
                
                this.ambientEnabled = !this.ambientEnabled;
                localStorage.setItem('prezI_ambientEnabled', this.ambientEnabled);
                
                if (this.ambientEnabled) {
                    this.startAmbient();
                } else {
                    this.stopAmbient();
                }
                
                this.updateUI();
            }
            
            updateUI() {
                const soundToggle = document.getElementById('soundToggle');
                const ambientToggle = document.getElementById('ambientToggle');
                
                if (soundToggle) {
                    soundToggle.classList.toggle('muted', !this.soundEnabled);
                }
                
                if (ambientToggle) {
                    ambientToggle.classList.toggle('active', this.ambientEnabled);
                    ambientToggle.style.opacity = this.soundEnabled ? '1' : '0.3';
                }
            }
        }
        
        // Haptic Feedback System
        class HapticManager {
            constructor() {
                this.supported = 'vibrate' in navigator;
            }
            
            vibrate(pattern) {
                if (this.supported && Array.isArray(pattern)) {
                    navigator.vibrate(pattern);
                } else if (this.supported && typeof pattern === 'number') {
                    navigator.vibrate([pattern]);
                }
            }
            
            // Subtle vibration on button press
            buttonPress() {
                this.vibrate([10]);
            }
            
            // Feedback on swipe actions
            swipeFeedback() {
                this.vibrate([5, 20, 5]);
            }
            
            // Success vibration pattern
            success() {
                this.vibrate([50, 50, 50, 50, 100]);
            }
            
            // Gentle notification
            notification() {
                this.vibrate([20, 100, 20]);
            }
        }
        
        // Initialize sound and haptic systems
        let soundManager;
        let hapticManager;
        
        // Language Management System
        class LanguageManager {
            constructor() {
                this.currentLanguage = localStorage.getItem('prezI_language') || 'en';
                this.translations = {
                    en: {
                        // Navigation
                        'The Problem': 'The Problem',
                        'Solution': 'Solution',
                        'Features': 'Features',
                        'Live Demos': 'Live Demos',
                        'Get Early Access': 'Get Early Access',
                        
                        // Hero Section
                        'Your AI Presentation Partner': 'Your AI Presentation Partner',
                        'Transform 5 hours of slide hunting into 5 minutes of magic': 'Transform 5 hours of slide hunting into 5 minutes of magic',
                        'From chaos to clarity. From intent to professional presentation': 'From chaos to clarity. From intent to professional presentation',
                        'Join Early Access': 'Join Early Access',
                        'Watch 90-Second Demo': 'Watch 90-Second Demo',
                        'Try Interactive Demos': 'Try Interactive Demos',
                        '2,847 professionals already in line': '2,847 professionals already in line',
                        'Next spots open': 'Next spots open',
                        'Early bird pricing ends': 'Early bird pricing ends',
                        
                        // Problem Section
                        'The Presentation Nightmare Every Professional Knows': 'The Presentation Nightmare Every Professional Knows',
                        'Hunting through 500+ slides across 30 PowerPoint files': 'Hunting through 500+ slides across 30 PowerPoint files',
                        'Copy-pasting slides, losing formatting, fixing fonts': 'Copy-pasting slides, losing formatting, fixing fonts',
                        'Inconsistent branding and missing critical information': 'Inconsistent branding and missing critical information',
                        '5 hours wasted on what should take 5 minutes': '5 hours wasted on what should take 5 minutes',
                        
                        // Solution Section
                        'Your AI Presentation Assistant is Here': 'Your AI Presentation Assistant is Here',
                        'PrezI transforms how you work with presentations. No more chaos, just professional results in minutes.': 'PrezI transforms how you work with presentations. No more chaos, just professional results in minutes.',
                        
                        // Features
                        'Instant Slide Discovery': 'Instant Slide Discovery',
                        'Find any slide instantly with natural language search. "Find Q4 revenue charts" → Done.': 'Find any slide instantly with natural language search. "Find Q4 revenue charts" → Done.',
                        'AI-Powered Assembly': 'AI-Powered Assembly',
                        'PrezI creates professional presentations from your existing slides with perfect formatting.': 'PrezI creates professional presentations from your existing slides with perfect formatting.',
                        'Smart Element Recognition': 'Smart Element Recognition',
                        'Every chart, table, and text box is tagged and searchable. Find exactly what you need.': 'Every chart, table, and text box is tagged and searchable. Find exactly what you need.',
                        'Brand Consistency Magic': 'Brand Consistency Magic',
                        'Automatic formatting ensures every presentation looks professionally crafted.': 'Automatic formatting ensures every presentation looks professionally crafted.',
                        
                        // Pricing
                        'Choose Your PrezI Plan': 'Choose Your PrezI Plan',
                        'Starter': 'Starter',
                        'Professional': 'Professional',
                        'Enterprise': 'Enterprise',
                        'per month': 'per month',
                        'Custom pricing': 'Custom pricing',
                        'Perfect for individuals': 'Perfect for individuals',
                        'For growing teams': 'For growing teams',
                        'Enterprise-scale solution': 'Enterprise-scale solution',
                        
                        // Testimonials
                        'What Our Early Users Say': 'What Our Early Users Say',
                        
                        // FAQ
                        'Frequently Asked Questions': 'Frequently Asked Questions',
                        'How accurate is PrezI?': 'How accurate is PrezI?',
                        'What AI models power PrezI?': 'What AI models power PrezI?',
                        
                        // Footer
                        'Request Early Access': 'Request Early Access',
                        'Start Your AI-Powered Presentation Journey': 'Start Your AI-Powered Presentation Journey'
                    },
                    de: {
                        // Navigation
                        'The Problem': 'Das Problem',
                        'Solution': 'Lösung',
                        'Features': 'Funktionen',
                        'Live Demos': 'Live-Demos',
                        'Get Early Access': 'Frühen Zugang erhalten',
                        
                        // Hero Section
                        'Your AI Presentation Partner': 'Ihr KI-Präsentationspartner',
                        'Transform 5 hours of slide hunting into 5 minutes of magic': 'Verwandeln Sie 5 Stunden Foliensuche in 5 Minuten Magie',
                        'From chaos to clarity. From intent to professional presentation': 'Vom Chaos zur Klarheit. Von der Absicht zur professionellen Präsentation',
                        'Join Early Access': 'Frühen Zugang beantragen',
                        'Watch 90-Second Demo': '90-Sekunden Demo ansehen',
                        'Try Interactive Demos': 'Interaktive Demos ausprobieren',
                        '2,847 professionals already in line': '2.847 Fachkräfte bereits in der Warteschlange',
                        'Next spots open': 'Nächste Plätze öffnen',
                        'Early bird pricing ends': 'Frühbucherpreise enden',
                        
                        // Problem Section
                        'The Presentation Nightmare Every Professional Knows': 'Der Präsentations-Albtraum, den jeder Profi kennt',
                        'Hunting through 500+ slides across 30 PowerPoint files': 'Suche durch 500+ Folien in 30 PowerPoint-Dateien',
                        'Copy-pasting slides, losing formatting, fixing fonts': 'Folien kopieren, Formatierung verlieren, Schriftarten reparieren',
                        'Inconsistent branding and missing critical information': 'Inkonsistentes Branding und fehlende kritische Informationen',
                        '5 hours wasted on what should take 5 minutes': '5 Stunden verschwendet für das, was 5 Minuten dauern sollte',
                        
                        // Solution Section
                        'Your AI Presentation Assistant is Here': 'Ihr KI-Präsentationsassistent ist da',
                        'PrezI transforms how you work with presentations. No more chaos, just professional results in minutes.': 'PrezI verwandelt Ihre Arbeit mit Präsentationen. Kein Chaos mehr, nur professionelle Ergebnisse in Minuten.',
                        
                        // Features
                        'Instant Slide Discovery': 'Sofortige Folien-Entdeckung',
                        'Find any slide instantly with natural language search. "Find Q4 revenue charts" → Done.': 'Finden Sie jede Folie sofort mit natürlicher Sprachsuche. "Finde Q4 Umsatzdiagramme" → Erledigt.',
                        'AI-Powered Assembly': 'KI-gestützte Assemblierung',
                        'PrezI creates professional presentations from your existing slides with perfect formatting.': 'PrezI erstellt professionelle Präsentationen aus Ihren vorhandenen Folien mit perfekter Formatierung.',
                        'Smart Element Recognition': 'Intelligente Element-Erkennung',
                        'Every chart, table, and text box is tagged and searchable. Find exactly what you need.': 'Jedes Diagramm, jede Tabelle und jedes Textfeld wird markiert und durchsuchbar. Finden Sie genau das, was Sie brauchen.',
                        'Brand Consistency Magic': 'Marken-Konsistenz-Magie',
                        'Automatic formatting ensures every presentation looks professionally crafted.': 'Automatische Formatierung sorgt dafür, dass jede Präsentation professionell gestaltet aussieht.',
                        
                        // Pricing
                        'Choose Your PrezI Plan': 'Wählen Sie Ihren PrezI-Plan',
                        'Starter': 'Starter',
                        'Professional': 'Professional',
                        'Enterprise': 'Enterprise',
                        'per month': 'pro Monat',
                        'Custom pricing': 'Individuelle Preise',
                        'Perfect for individuals': 'Perfekt für Einzelpersonen',
                        'For growing teams': 'Für wachsende Teams',
                        'Enterprise-scale solution': 'Enterprise-Skalenlösung',
                        
                        // Testimonials
                        'What Our Early Users Say': 'Was unsere Early User sagen',
                        
                        // FAQ
                        'Frequently Asked Questions': 'Häufig gestellte Fragen',
                        'How accurate is PrezI?': 'Wie genau ist PrezI?',
                        'What AI models power PrezI?': 'Welche KI-Modelle treiben PrezI an?',
                        
                        // Footer
                        'Request Early Access': 'Frühen Zugang beantragen',
                        'Start Your AI-Powered Presentation Journey': 'Beginnen Sie Ihre KI-gestützte Präsentationsreise'
                    }
                };
            }
            
            getCurrentLanguage() {
                return this.currentLanguage;
            }
            
            setLanguage(language) {
                this.currentLanguage = language;
                localStorage.setItem('prezI_language', language);
                this.updatePage();
                this.updateLanguageToggle();
            }
            
            toggleLanguage() {
                const newLanguage = this.currentLanguage === 'en' ? 'de' : 'en';
                this.setLanguage(newLanguage);
            }
            
            translate(key) {
                return this.translations[this.currentLanguage][key] || key;
            }
            
            updatePage() {
                // Update all translatable elements
                const elements = document.querySelectorAll('[data-translate]');
                elements.forEach(element => {
                    const key = element.getAttribute('data-translate');
                    const translation = this.translate(key);
                    
                    if (element.tagName === 'INPUT' && element.type === 'submit') {
                        element.value = translation;
                    } else if (element.tagName === 'INPUT' && element.placeholder) {
                        element.placeholder = translation;
                    } else {
                        element.textContent = translation;
                    }
                });
                
                // Update specific elements by ID or class if needed
                this.updateSpecialElements();
            }
            
            updateSpecialElements() {
                // Update meta tags for SEO
                const title = document.querySelector('title');
                if (title) {
                    if (this.currentLanguage === 'de') {
                        title.textContent = 'PrezI - Verwandeln Sie 5 Stunden Präsentationsarbeit in 5 Minuten mit KI';
                    } else {
                        title.textContent = 'PrezI - Transform 5 Hours of Presentation Work into 5 Minutes with AI';
                    }
                }
                
                const metaDescription = document.querySelector('meta[name="description"]');
                if (metaDescription) {
                    if (this.currentLanguage === 'de') {
                        metaDescription.content = 'PrezI ist der KI-Präsentationsassistent, der Ihr PowerPoint-Chaos in professionelle Präsentationen in Minuten verwandelt. Sparen Sie 90% Ihrer Zeit mit intelligenter Folienverwaltung.';
                    } else {
                        metaDescription.content = 'PrezI is the AI-powered presentation assistant that transforms your PowerPoint chaos into professional presentations in minutes. Save 90% of your time with intelligent slide management.';
                    }
                }
            }
            
            updateLanguageToggle() {
                const languageFlag = document.getElementById('languageFlag');
                if (languageFlag) {
                    languageFlag.textContent = this.currentLanguage === 'en' ? '🇩🇪' : '🇺🇸';
                }
                
                const languageToggle = document.getElementById('languageToggle');
                if (languageToggle) {
                    if (this.currentLanguage === 'en') {
                        languageToggle.title = 'Switch to German / Zu Deutsch wechseln';
                    } else {
                        languageToggle.title = 'Switch to English / Zu Englisch wechseln';
                    }
                }
            }
        }
        
        // Initialize language manager
        const languageManager = new LanguageManager();
        
        function initializeSoundAndHaptics() {
            soundManager = new SoundManager();
            hapticManager = new HapticManager();
            
            // Set up event listeners
            const soundToggle = document.getElementById('soundToggle');
            const ambientToggle = document.getElementById('ambientToggle');
            const themeToggle = document.getElementById('themeToggle');
            
            if (soundToggle) {
                soundToggle.addEventListener('click', () => {
                    soundManager.toggleSound();
                    hapticManager.buttonPress();
                });
            }
            
            if (ambientToggle) {
                ambientToggle.addEventListener('click', () => {
                    soundManager.toggleAmbient();
                    hapticManager.buttonPress();
                });
            }
            
            if (themeToggle) {
                themeToggle.addEventListener('click', () => {
                    toggleTheme();
                    hapticManager.buttonPress();
                    if (soundManager.soundEnabled) {
                        soundManager.soundEffects.click();
                    }
                });
            }
            
            // Language toggle
            const languageToggle = document.getElementById('languageToggle');
            if (languageToggle) {
                languageToggle.addEventListener('click', () => {
                    languageManager.toggleLanguage();
                    hapticManager.buttonPress();
                    if (soundManager.soundEnabled) {
                        soundManager.soundEffects.click();
                    }
                });
            }
            
            // Initialize language on load
            languageManager.updateLanguageToggle();
            
            // Add sound effects to page elements
            addSoundEffectsToElements();
            
            // Play whoosh on page load
            setTimeout(() => {
                if (soundManager.soundEnabled) {
                    soundManager.soundEffects.whoosh();
                }
            }, 1000);
        }
        
        function addSoundEffectsToElements() {
            // Add click sounds to all buttons
            document.querySelectorAll('button, .btn, .nav-cta, .cta-btn').forEach(button => {
                button.addEventListener('click', () => {
                    if (soundManager.soundEnabled) {
                        soundManager.soundEffects.click();
                    }
                    hapticManager.buttonPress();
                });
                
                button.addEventListener('mouseenter', () => {
                    if (soundManager.soundEnabled) {
                        soundManager.soundEffects.hover();
                    }
                });
            });
            
            // Add success chime to CTA buttons
            document.querySelectorAll('.hero-cta, .cta-btn, .pricing-btn').forEach(cta => {
                cta.addEventListener('click', () => {
                    if (soundManager.soundEnabled) {
                        soundManager.soundEffects.success();
                    }
                    hapticManager.success();
                });
            });
            
            // Add swipe feedback to swipeable elements
            document.querySelectorAll('.demo-card, .slide-card').forEach(card => {
                let startX = 0;
                
                card.addEventListener('touchstart', (e) => {
                    startX = e.touches[0].clientX;
                });
                
                card.addEventListener('touchend', (e) => {
                    const endX = e.changedTouches[0].clientX;
                    const diff = Math.abs(startX - endX);
                    
                    if (diff > 50) { // Swipe detected
                        hapticManager.swipeFeedback();
                    }
                });
            });
            
            // Add notification haptic to urgency elements
            const spotsElement = document.getElementById('spotsCount');
            if (spotsElement) {
                const observer = new MutationObserver(() => {
                    hapticManager.notification();
                });
                observer.observe(spotsElement, { childList: true, characterData: true, subtree: true });
            }
        }
        
        // Theme Management
        function initializeTheme() {
            // Get saved theme or default to dark
            const savedTheme = localStorage.getItem('prezI_theme') || 'dark';
            
            // Apply theme
            if (savedTheme === 'light') {
                document.documentElement.setAttribute('data-theme', 'light');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
            
            // Also set color-scheme meta tag
            const colorSchemeMetaTag = document.querySelector('meta[name="color-scheme"]');
            if (colorSchemeMetaTag) {
                colorSchemeMetaTag.content = savedTheme;
            }
            
            // Set theme-color meta tag
            const themeColorMetaTag = document.querySelector('meta[name="theme-color"]');
            if (themeColorMetaTag) {
                themeColorMetaTag.content = savedTheme === 'light' ? '#f8fafc' : '#667eea';
            }
        }
        
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            if (newTheme === 'light') {
                document.documentElement.setAttribute('data-theme', 'light');
            } else {
                document.documentElement.removeAttribute('data-theme');
            }
            
            // Save to localStorage
            localStorage.setItem('prezI_theme', newTheme);
            
            // Update meta tags
            const colorSchemeMetaTag = document.querySelector('meta[name="color-scheme"]');
            if (colorSchemeMetaTag) {
                colorSchemeMetaTag.content = newTheme;
            }
            
            const themeColorMetaTag = document.querySelector('meta[name="theme-color"]');
            if (themeColorMetaTag) {
                themeColorMetaTag.content = newTheme === 'light' ? '#f8fafc' : '#667eea';
            }
            
            // Track theme change
            if (typeof gtag !== 'undefined') {
                gtag('event', 'theme_change', {
                    theme: newTheme,
                    interaction_type: 'toggle'
                });
            }
            
            // Add a subtle animation effect
            document.body.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        }
        
        // System theme preference detection
        function detectSystemTheme() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
                return 'light';
            }
            return 'dark';
        }
        
        // Listen for system theme changes
        function watchSystemTheme() {
            if (window.matchMedia) {
                const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
                mediaQuery.addListener((e) => {
                    // Only auto-switch if user hasn't manually set a preference
                    if (!localStorage.getItem('prezI_theme')) {
                        const systemTheme = e.matches ? 'light' : 'dark';
                        if (systemTheme === 'light') {
                            document.documentElement.setAttribute('data-theme', 'light');
                        } else {
                            document.documentElement.removeAttribute('data-theme');
                        }
                    }
                });
            }
        }
        
        // Initialize all features
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize theme first to prevent flash
            initializeTheme();
            watchSystemTheme();
            
            initializeAccessibility();
            initializePWA();
            
            // Initialize sound and haptics after user interaction
            const initSoundOnInteraction = () => {
                initializeSoundAndHaptics();
                document.removeEventListener('click', initSoundOnInteraction);
                document.removeEventListener('keydown', initSoundOnInteraction);
                document.removeEventListener('touchstart', initSoundOnInteraction);
            };
            
            document.addEventListener('click', initSoundOnInteraction);
            document.addEventListener('keydown', initSoundOnInteraction);
            document.addEventListener('touchstart', initSoundOnInteraction);
        });
