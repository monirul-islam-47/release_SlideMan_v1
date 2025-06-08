        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // Parallax effect for hero background
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const heroBg = document.querySelector('.hero-bg');
            if (heroBg) {
                heroBg.style.transform = `translateY(${scrolled * 0.5}px)`;
            }
        });
        
        // Animate elements on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        // Observe all sections and cards
        document.querySelectorAll('.section, .problem-card, .roi-stat, .demo-card, .feature-row').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        });
        
        // Enhanced animate ROI numbers on scroll
        const animateNumber = (element, target, suffix = '', decimals = 0) => {
            const duration = 2000;
            const start = 0;
            const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easedProgress = easeOutQuart(progress);
                const current = start + (target - start) * easedProgress;
                
                // Add random jitter for realistic counting
                const jitter = progress < 0.95 ? Math.random() * 2 - 1 : 0;
                const displayValue = decimals > 0 
                    ? (current + jitter).toFixed(decimals) 
                    : Math.floor(current + jitter);
                
                element.textContent = displayValue + suffix;
                
                // Add scale effect during counting
                const scale = 1 + (1 - progress) * 0.05;
                element.style.transform = `scale(${scale})`;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.transform = 'scale(1)';
                    element.textContent = (decimals > 0 ? target.toFixed(decimals) : target) + suffix;
                }
            };
            
            requestAnimationFrame(animate);
        };
        
        const roiObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const numberEl = entry.target.querySelector('.roi-number');
                    const text = numberEl.textContent;
                    
                    if (text.includes('%')) {
                        animateNumber(numberEl, parseInt(text), '%');
                    } else if (text.includes('s')) {
                        animateNumber(numberEl, 0.3, 's', 1);
                    } else {
                        animateNumber(numberEl, parseInt(text));
                    }
                    
                    roiObserver.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.roi-stat').forEach(stat => {
            roiObserver.observe(stat);
        });
        
        // Dynamic avatar particles
        setInterval(() => {
            const particles = document.querySelectorAll('.particle');
            particles.forEach(particle => {
                if (Math.random() > 0.7) {
                    particle.style.left = (40 + Math.random() * 20) + '%';
                    particle.style.top = (40 + Math.random() * 20) + '%';
                }
            });
        }, 3000);
        
        // Mouse-following avatar
        const avatarCore = document.querySelector('.prezi-avatar-core');
        const avatar = document.querySelector('.prezi-hero-avatar');
        
        if (avatarCore && avatar) {
            let scrollRotation = 0;
            let mouseRotationX = 0;
            let mouseRotationY = 0;
            
            // React to scroll position
            window.addEventListener('scroll', () => {
                const scrollPercent = window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight);
                scrollRotation = scrollPercent * 20; // Look down up to 20 degrees
                
                avatarCore.style.transform = `translate(-50%, -50%) rotateX(${scrollRotation + mouseRotationX}deg) rotateY(${mouseRotationY}deg)`;
            });
            
            // Follow mouse
            document.addEventListener('mousemove', (e) => {
                const rect = avatar.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angleX = (e.clientX - centerX) / window.innerWidth;
                const angleY = (e.clientY - centerY) / window.innerHeight;
                
                const maxRotation = 15;
                mouseRotationX = -angleY * maxRotation;
                mouseRotationY = angleX * maxRotation;
                
                avatarCore.style.transform = `translate(-50%, -50%) rotateX(${scrollRotation + mouseRotationX}deg) rotateY(${mouseRotationY}deg)`;
            });
        }
        
        // Generate floating particles
        const heroParticles = document.querySelector('.hero-particles');
        if (heroParticles) {
            for (let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.className = 'floating-particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 20 + 's';
                particle.style.animationDuration = (15 + Math.random() * 10) + 's';
                heroParticles.appendChild(particle);
            }
        }
        
        // CTA button particle burst on hover
        const avatarMain = document.querySelector('.prezi-avatar-main');
        const avatarCore = document.querySelector('.prezi-avatar-core');
        
        document.querySelectorAll('.btn-primary').forEach(btn => {
            btn.addEventListener('mouseenter', (e) => {
                // Trigger excitement bounce on PrezI avatar
                if (avatarMain) {
                    avatarMain.classList.add('excited');
                    setTimeout(() => avatarMain.classList.remove('excited'), 800);
                }
                
                const rect = btn.getBoundingClientRect();
                for (let i = 0; i < 5; i++) {
                    const particle = document.createElement('div');
                    particle.style.position = 'fixed';
                    particle.style.width = '4px';
                    particle.style.height = '4px';
                    particle.style.background = 'rgba(102, 126, 234, 0.8)';
                    particle.style.borderRadius = '50%';
                    particle.style.left = rect.left + rect.width / 2 + 'px';
                    particle.style.top = rect.top + rect.height / 2 + 'px';
                    particle.style.pointerEvents = 'none';
                    particle.style.zIndex = '9999';
                    document.body.appendChild(particle);
                    
                    const angle = (Math.PI * 2 * i) / 5;
                    const velocity = 100 + Math.random() * 50;
                    
                    particle.animate([
                        { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                        { 
                            transform: `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity}px) scale(0)`,
                            opacity: 0
                        }
                    ], {
                        duration: 800,
                        easing: 'ease-out'
                    }).onfinish = () => particle.remove();
                }
            });
        });
        
        // Thinking spiral when scrolling to solution section
        const solutionSection = document.querySelector('.solution-section');
        const thinkingObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && avatarCore) {
                    avatarCore.classList.add('thinking');
                    
                    // Create spiral particles
                    const avatarRect = avatar.getBoundingClientRect();
                    const centerX = avatarRect.left + avatarRect.width / 2;
                    const centerY = avatarRect.top + avatarRect.height / 2;
                    
                    for (let i = 0; i < 6; i++) {
                        setTimeout(() => {
                            const particle = document.createElement('div');
                            particle.className = 'thinking-particle';
                            particle.style.position = 'fixed';
                            particle.style.zIndex = '999';
                            
                            // Start position in a circle around avatar
                            const angle = (Math.PI * 2 * i) / 6;
                            const radius = 100;
                            const startX = centerX + Math.cos(angle) * radius;
                            const startY = centerY + Math.sin(angle) * radius;
                            
                            particle.style.left = startX + 'px';
                            particle.style.top = startY + 'px';
                            
                            // Calculate end position (center of avatar)
                            const endX = centerX - startX;
                            const endY = centerY - startY;
                            
                            particle.style.setProperty('--end-x', endX + 'px');
                            particle.style.setProperty('--end-y', endY + 'px');
                            
                            document.body.appendChild(particle);
                            
                            // Remove particle after animation
                            setTimeout(() => particle.remove(), 2000);
                        }, i * 100);
                    }
                    
                    setTimeout(() => avatarCore.classList.remove('thinking'), 2000);
                }
            });
        }, { threshold: 0.3 });
        
        if (solutionSection) {
            thinkingObserver.observe(solutionSection);
        }
        
        // Success celebration when reaching CTA section
        const ctaSection = document.querySelector('.cta-section');
        const celebrationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && avatarMain) {
                    avatarMain.classList.add('celebrating');
                    
                    // Create celebration particles
                    const avatarRect = avatarMain.getBoundingClientRect();
                    for (let i = 0; i < 8; i++) {
                        const particle = document.createElement('div');
                        particle.style.position = 'fixed';
                        particle.style.width = '6px';
                        particle.style.height = '6px';
                        particle.style.background = `hsl(${Math.random() * 60 + 240}, 70%, 60%)`;
                        particle.style.borderRadius = '50%';
                        particle.style.left = avatarRect.left + avatarRect.width / 2 + 'px';
                        particle.style.top = avatarRect.top + avatarRect.height / 2 + 'px';
                        particle.style.pointerEvents = 'none';
                        particle.style.zIndex = '9999';
                        document.body.appendChild(particle);
                        
                        const angle = (Math.PI * 2 * i) / 8;
                        const velocity = 150 + Math.random() * 100;
                        const rotation = Math.random() * 720 - 360;
                        
                        particle.animate([
                            { transform: 'translate(0, 0) scale(1) rotate(0deg)', opacity: 1 },
                            { 
                                transform: `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity - 50}px) scale(0) rotate(${rotation}deg)`,
                                opacity: 0
                            }
                        ], {
                            duration: 1200,
                            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
                        }).onfinish = () => particle.remove();
                    }
                    
                    setTimeout(() => avatarMain.classList.remove('celebrating'), 1500);
                }
            });
        }, { threshold: 0.5 });
        
        if (ctaSection) {
            celebrationObserver.observe(ctaSection);
        }
        
        // 3D tilt effect for feature cards
        document.querySelectorAll('.feature-visual').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / centerY * -10;
                const rotateY = (x - centerX) / centerX * 10;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
            });
        });
        
        // Enhanced demo card hover with preview animation
        document.querySelectorAll('.demo-card').forEach(card => {
            const thumbnail = card.querySelector('.demo-thumbnail');
            
            // 3D tilt effect
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / centerY * -5;
                const rotateY = (x - centerX) / centerX * 5;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
            });
            
            // Add preview animation placeholder
            if (thumbnail && !thumbnail.querySelector('.demo-preview')) {
                const preview = document.createElement('div');
                preview.className = 'demo-preview';
                preview.innerHTML = `
                    <div class="preview-screen">
                        <div class="preview-content">
                            <div class="preview-slide"></div>
                            <div class="preview-slide"></div>
                            <div class="preview-slide"></div>
                        </div>
                    </div>
                `;
                thumbnail.appendChild(preview);
            }
        });
        
        // Generate ambient floating dots for sections
        document.querySelectorAll('.ambient-dots').forEach(container => {
            for (let i = 0; i < 15; i++) {
                const dot = document.createElement('div');
                dot.className = 'floating-dot';
                dot.style.left = Math.random() * 100 + '%';
                dot.style.animationDelay = Math.random() * 20 + 's';
                dot.style.animationDuration = (15 + Math.random() * 10) + 's';
                
                // Vary the movement pattern
                if (Math.random() > 0.5) {
                    dot.style.animation = `float-dot ${15 + Math.random() * 10}s infinite linear`;
                } else {
                    dot.style.animation = `float-dot ${15 + Math.random() * 10}s infinite linear reverse`;
                }
                
                container.appendChild(dot);
            }
        });
        
        // Animate view counter
        const viewCountObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const viewCount = entry.target.querySelector('.view-count');
                    if (viewCount && viewCount.dataset.target) {
                        const target = parseInt(viewCount.dataset.target);
                        animateViewCount(viewCount, target);
                        viewCountObserver.unobserve(entry.target);
                    }
                }
            });
        }, { threshold: 0.5 });
        
        const viewCounter = document.querySelector('.view-counter');
        if (viewCounter) {
            viewCountObserver.observe(viewCounter);
        }
        
        // Enhanced view count animation with formatting
        const animateViewCount = (element, target) => {
            const duration = 2500;
            const start = 0;
            const easeOutExpo = (t) => t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const easedProgress = easeOutExpo(progress);
                const current = Math.floor(start + (target - start) * easedProgress);
                
                // Format with commas
                element.textContent = current.toLocaleString();
                
                // Add slight scale effect
                const scale = 1 + (1 - progress) * 0.1;
                element.style.transform = `scale(${scale})`;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.transform = 'scale(1)';
                    element.textContent = target.toLocaleString();
                    // Add a subtle glow when complete
                    element.style.textShadow = '0 0 10px rgba(102, 126, 234, 0.5)';
                    setTimeout(() => {
                        element.style.textShadow = '';
                    }, 500);
                }
            };
            
            requestAnimationFrame(animate);
        };
        
        // Feature Connection Lines
        const initFeatureConnections = () => {
            const featureRows = document.querySelectorAll('.feature-row[data-feature]');
            const connections = document.querySelector('.feature-connections svg');
            
            if (!featureRows.length || !connections) return;
            
            const updateConnectionPaths = () => {
                const containerRect = connections.getBoundingClientRect();
                
                featureRows.forEach((row, index) => {
                    if (index === featureRows.length - 1) return; // Skip last row
                    
                    const currentVisual = row.querySelector('.feature-visual');
                    const nextRow = featureRows[index + 1];
                    const nextVisual = nextRow.querySelector('.feature-visual');
                    
                    if (!currentVisual || !nextVisual) return;
                    
                    const currentRect = currentVisual.getBoundingClientRect();
                    const nextRect = nextVisual.getBoundingClientRect();
                    
                    // Calculate relative positions
                    const startX = currentRect.left + currentRect.width / 2 - containerRect.left;
                    const startY = currentRect.top + currentRect.height / 2 - containerRect.top;
                    const endX = nextRect.left + nextRect.width / 2 - containerRect.left;
                    const endY = nextRect.top + nextRect.height / 2 - containerRect.top;
                    
                    // Create curved path
                    const controlX = (startX + endX) / 2;
                    const controlY = startY - 60;
                    const pathData = `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;
                    
                    // Update connection paths
                    const connectionId = `connection-${index + 1}-${index + 2}`;
                    const connection = document.getElementById(connectionId);
                    const pathId = `path-${index + 1}-${index + 2}`;
                    
                    if (connection) {
                        const path = connection.querySelector('.connection-path');
                        const hiddenPath = document.getElementById(pathId);
                        
                        if (path) path.setAttribute('d', pathData);
                        if (hiddenPath) hiddenPath.setAttribute('d', pathData);
                    }
                });
            };
            
            // Initial path update
            updateConnectionPaths();
            
            // Update on window resize
            window.addEventListener('resize', updateConnectionPaths);
            
            // Add hover effects
            featureRows.forEach((row, index) => {
                row.addEventListener('mouseenter', () => {
                    // Show connection from this feature to next
                    if (index < featureRows.length - 1) {
                        const connectionId = `connection-${index + 1}-${index + 2}`;
                        const connection = document.getElementById(connectionId);
                        if (connection) {
                            connection.classList.add('active');
                        }
                    }
                    
                    // Show connection from previous feature to this
                    if (index > 0) {
                        const connectionId = `connection-${index}-${index + 1}`;
                        const connection = document.getElementById(connectionId);
                        if (connection) {
                            connection.classList.add('active');
                        }
                    }
                });
                
                row.addEventListener('mouseleave', () => {
                    // Hide all connections after a delay
                    setTimeout(() => {
                        const allConnections = document.querySelectorAll('.connection-line');
                        let shouldKeepVisible = false;
                        
                        // Check if any feature is still hovered
                        featureRows.forEach(checkRow => {
                            if (checkRow.matches(':hover')) {
                                shouldKeepVisible = true;
                            }
                        });
                        
                        if (!shouldKeepVisible) {
                            allConnections.forEach(conn => {
                                conn.classList.remove('active');
                            });
                        }
                    }, 100);
                });
            });
        };
        
        // Initialize feature connections when page loads
        window.addEventListener('load', initFeatureConnections);
        
        // Video Progress Bar Animation
        const initVideoProgress = () => {
            const playButton = document.querySelector('.video-play-button');
            const progressBar = document.querySelector('.video-progress-fill');
            
            if (!playButton || !progressBar) return;
            
            let progressInterval;
            
            const animateProgress = () => {
                const targetProgress = parseInt(progressBar.dataset.progress) || 42;
                let currentProgress = 0;
                
                progressInterval = setInterval(() => {
                    currentProgress += 1;
                    progressBar.style.width = `${currentProgress}%`;
                    
                    if (currentProgress >= targetProgress) {
                        clearInterval(progressInterval);
                    }
                }, 50);
            };
            
            const resetProgress = () => {
                if (progressInterval) {
                    clearInterval(progressInterval);
                }
                progressBar.style.width = '0%';
            };
            
            // Animate progress on hover
            playButton.addEventListener('mouseenter', animateProgress);
            playButton.addEventListener('mouseleave', resetProgress);
            
            // Also animate when clicking play button
            playButton.addEventListener('click', (e) => {
                e.preventDefault();
                progressBar.style.width = '100%';
                progressBar.style.transition = 'width 90s linear';
                
                // Reset after animation
                setTimeout(() => {
                    progressBar.style.transition = 'width 0.3s ease';
                    resetProgress();
                }, 92000);
            });
        };
        
        // Initialize video progress
        window.addEventListener('load', initVideoProgress);
        
        // Request Access Form Handler
        const initRequestForm = () => {
            const form = document.getElementById('requestAccessForm');
            const successDiv = document.getElementById('formSuccess');
            
            if (!form || !successDiv) return;
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const submitBtn = form.querySelector('.form-submit');
                const originalText = submitBtn.textContent;
                
                // Show loading state
                submitBtn.disabled = true;
                submitBtn.textContent = '🔄 Submitting...';
                
                // Simulate form submission (replace with actual API call)
                try {
                    await new Promise(resolve => setTimeout(resolve, 1500));
                    
                    // Hide form and show success
                    form.style.display = 'none';
                    successDiv.classList.add('show');
                    
                    // Trigger PrezI celebration
                    const avatarMain = document.querySelector('.prezi-avatar-main');
                    if (avatarMain) {
                        avatarMain.classList.add('celebrating');
                        setTimeout(() => avatarMain.classList.remove('celebrating'), 1500);
                    }
                    
                    // Create success particles
                    createSuccessParticles();
                    
                } catch (error) {
                    // Reset button on error
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                    
                    // Trigger avatar error shake
                    if (typeof window.triggerAvatarError === 'function') {
                        window.triggerAvatarError('Oops! Something went wrong. Please try again.');
                    }
                    
                    // Show friendly error message instead of alert
                    const errorDiv = document.createElement('div');
                    errorDiv.style.cssText = `
                        background: var(--accent-red);
                        color: white;
                        padding: 12px 20px;
                        border-radius: 8px;
                        margin-top: 16px;
                        text-align: center;
                        font-weight: 600;
                        opacity: 0;
                        transition: opacity 0.3s ease;
                    `;
                    errorDiv.textContent = 'Something went wrong. Please check your connection and try again.';
                    
                    form.appendChild(errorDiv);
                    setTimeout(() => errorDiv.style.opacity = '1', 100);
                    setTimeout(() => {
                        errorDiv.style.opacity = '0';
                        setTimeout(() => errorDiv.remove(), 300);
                    }, 4000);
                }
            });
        };
        
        const createSuccessParticles = () => {
            const formContainer = document.querySelector('.request-form-container');
            if (!formContainer) return;
            
            const rect = formContainer.getBoundingClientRect();
            for (let i = 0; i < 12; i++) {
                const particle = document.createElement('div');
                particle.style.position = 'fixed';
                particle.style.width = '8px';
                particle.style.height = '8px';
                particle.style.background = `hsl(${120 + Math.random() * 60}, 70%, 60%)`;
                particle.style.borderRadius = '50%';
                particle.style.left = rect.left + rect.width / 2 + 'px';
                particle.style.top = rect.top + rect.height / 2 + 'px';
                particle.style.pointerEvents = 'none';
                particle.style.zIndex = '9999';
                document.body.appendChild(particle);
                
                const angle = (Math.PI * 2 * i) / 12;
                const velocity = 120 + Math.random() * 80;
                const rotation = Math.random() * 720 - 360;
                
                particle.animate([
                    { transform: 'translate(0, 0) scale(1) rotate(0deg)', opacity: 1 },
                    { 
                        transform: `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity - 100}px) scale(0) rotate(${rotation}deg)`,
                        opacity: 0
                    }
                ], {
                    duration: 1500,
                    easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
                }).onfinish = () => particle.remove();
            }
        };
        
        // Initialize form
        window.addEventListener('load', initRequestForm);
        
        // Live Performance Badge Updates
        const initLivePerformance = () => {
            const latencyElement = document.getElementById('liveLatency');
            if (!latencyElement) return;
            
            const baseLatency = 0.28;
            const updateLatency = () => {
                // Generate realistic variations between 0.24s and 0.32s
                const variation = (Math.random() - 0.5) * 0.08;
                const newLatency = Math.max(0.24, Math.min(0.32, baseLatency + variation));
                latencyElement.textContent = newLatency.toFixed(2) + 's';
                
                // Slight color change based on performance
                if (newLatency <= 0.26) {
                    latencyElement.style.color = 'var(--accent-green)';
                } else if (newLatency <= 0.30) {
                    latencyElement.style.color = '#22d3ee'; // cyan for good
                } else {
                    latencyElement.style.color = '#fbbf24'; // amber for slower
                }
            };
            
            // Update every 3-7 seconds for realistic behavior
            const scheduleUpdate = () => {
                const delay = 3000 + Math.random() * 4000;
                setTimeout(() => {
                    updateLatency();
                    scheduleUpdate();
                }, delay);
            };
            
            scheduleUpdate();
        };
        
        // Initialize live performance updates
        window.addEventListener('load', initLivePerformance);
        
        // Onboarding Video Player
        const initOnboardingVideo = () => {
            const playBtn = document.getElementById('onboardingPlayBtn');
            const progressBar = document.getElementById('onboardingProgress');
            const frameItems = document.querySelectorAll('.frame-item');
            
            if (!playBtn || !progressBar) return;
            
            playBtn.addEventListener('click', () => {
                // Simulate video playback with frame progression
                progressBar.style.width = '100%';
                progressBar.style.transition = 'width 60s linear';
                
                // Cycle through frames
                let currentFrame = 0;
                const cycleFrames = () => {
                    frameItems.forEach(item => item.classList.remove('active'));
                    frameItems[currentFrame].classList.add('active');
                    currentFrame = (currentFrame + 1) % frameItems.length;
                };
                
                const frameInterval = setInterval(cycleFrames, 12000); // 12 seconds per frame
                
                // Reset after 60 seconds
                setTimeout(() => {
                    clearInterval(frameInterval);
                    progressBar.style.transition = 'width 0.3s ease';
                    progressBar.style.width = '0%';
                    frameItems.forEach(item => item.classList.remove('active'));
                    frameItems[0].classList.add('active');
                }, 60000);
            });
            
            // Frame click interaction
            frameItems.forEach((item, index) => {
                item.addEventListener('click', () => {
                    frameItems.forEach(f => f.classList.remove('active'));
                    item.classList.add('active');
                    
                    // Update progress to match frame
                    progressBar.style.width = ((index + 1) / frameItems.length * 100) + '%';
                });
            });
        };
        
        // Initialize onboarding video
        window.addEventListener('load', initOnboardingVideo);
        
        // Live Sandbox Functionality
        const initSandbox = () => {
            const uploadArea = document.getElementById('sandboxUpload');
            const analysisArea = document.getElementById('analysisArea');
            const fileInput = document.getElementById('sandboxFileInput');
            const progressBar = document.getElementById('analysisProgress');
            const progressText = document.getElementById('progressText');
            
            if (!uploadArea || !analysisArea) return;
            
            // File drop handling
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = 'var(--accent-blue)';
                uploadArea.style.background = 'rgba(59, 130, 246, 0.05)';
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.style.borderColor = '#3a3a3a';
                uploadArea.style.background = '';
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#3a3a3a';
                uploadArea.style.background = '';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    processFile(files[0]);
                }
            });
            
            // File input change
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    processFile(e.target.files[0]);
                }
            });
        };
        
        // Sample file loading
        window.loadSampleFile = (type) => {
            const fileData = {
                revenue: { name: 'Q4 Revenue.pptx', slides: 12, type: 'Financial' },
                strategy: { name: 'Growth Strategy.pptx', slides: 15, type: 'Strategic' },
                product: { name: 'Product Roadmap.pptx', slides: 8, type: 'Product' }
            };
            
            const file = fileData[type];
            if (file) {
                simulateFileProcessing(file);
            }
        };
        
        const processFile = (file) => {
            if (!file.name.match(/\.(pptx|ppt)$/)) {
                alert('Please upload a PowerPoint file (.pptx or .ppt)');
                return;
            }
            
            const fileData = {
                name: file.name,
                slides: Math.floor(Math.random() * 10) + 8,
                type: 'Uploaded'
            };
            
            simulateFileProcessing(fileData);
        };
        
        const simulateFileProcessing = (fileData) => {
            const uploadArea = document.getElementById('sandboxUpload');
            const analysisArea = document.getElementById('analysisArea');
            const progressBar = document.getElementById('analysisProgress');
            const progressText = document.getElementById('progressText');
            
            // Hide upload, show analysis
            uploadArea.style.display = 'none';
            analysisArea.style.display = 'block';
            
            const steps = [
                'Extracting slide content...',
                'Identifying element types...',
                'Analyzing text and images...',
                'Applying AI recognition...',
                'Generating smart tags...',
                'Creating insights...',
                'Analysis complete!'
            ];
            
            let currentStep = 0;
            const stepInterval = setInterval(() => {
                const progress = ((currentStep + 1) / steps.length) * 100;
                progressBar.style.width = progress + '%';
                progressText.textContent = steps[currentStep];
                
                currentStep++;
                if (currentStep >= steps.length) {
                    clearInterval(stepInterval);
                    showAnalysisResults(fileData);
                }
            }, 800);
        };
        
        const showAnalysisResults = (fileData) => {
            // Update slide info
            const slideInfo = document.querySelector('.slide-info h4');
            if (slideInfo) {
                slideInfo.textContent = `Slide 1 of ${fileData.slides}`;
            }
            
            // Show element overlays with animation
            const overlays = document.querySelectorAll('.element-overlay');
            overlays.forEach((overlay, index) => {
                setTimeout(() => {
                    overlay.style.opacity = '1';
                    overlay.style.animation = 'elementPulse 0.5s ease';
                }, index * 300);
            });
            
            // Animate element items
            const elementItems = document.querySelectorAll('.element-item');
            elementItems.forEach((item, index) => {
                setTimeout(() => {
                    item.style.transform = 'translateX(0)';
                    item.style.opacity = '1';
                }, 2000 + index * 200);
            });
            
            // Show AI insights
            const insights = document.querySelectorAll('.insight-item');
            insights.forEach((insight, index) => {
                setTimeout(() => {
                    insight.style.transform = 'translateX(0)';
                    insight.style.opacity = '1';
                }, 3000 + index * 300);
            });
        };
        
        // Navigate to next slide
        window.nextSlide = () => {
            const slideInfo = document.querySelector('.slide-info h4');
            if (slideInfo) {
                const match = slideInfo.textContent.match(/Slide (\d+) of (\d+)/);
                if (match) {
                    const current = parseInt(match[1]);
                    const total = parseInt(match[2]);
                    const next = current < total ? current + 1 : 1;
                    slideInfo.textContent = `Slide ${next} of ${total}`;
                    
                    // Reset and re-animate overlays
                    const overlays = document.querySelectorAll('.element-overlay');
                    overlays.forEach(overlay => {
                        overlay.style.opacity = '0';
                        setTimeout(() => {
                            overlay.style.opacity = '1';
                            overlay.style.animation = 'elementPulse 0.5s ease';
                        }, 200);
                    });
                }
            }
        };
        
        // Reset sandbox
        window.resetSandbox = () => {
            const uploadArea = document.getElementById('sandboxUpload');
            const analysisArea = document.getElementById('analysisArea');
            
            uploadArea.style.display = 'block';
            analysisArea.style.display = 'none';
            
            // Reset progress
            document.getElementById('analysisProgress').style.width = '0%';
            document.getElementById('progressText').textContent = 'Initializing...';
            
            // Reset overlays
            const overlays = document.querySelectorAll('.element-overlay');
            overlays.forEach(overlay => {
                overlay.style.opacity = '0';
            });
        };
        
        // Initialize sandbox
        window.addEventListener('load', initSandbox);
