/* =====================================================
   PREZI LANDING PAGE - MAIN JAVASCRIPT
   ===================================================== */

// Progressive Enhancement: Check for browser capabilities
const supportsIntersectionObserver = 'IntersectionObserver' in window;
const supportsWebAnimations = 'animate' in document.documentElement;
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Performance optimization: Throttle and debounce helpers
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// =====================================================
// INTERSECTION OBSERVER FOR ANIMATIONS
// =====================================================
let animationObserver;

function initIntersectionObserver() {
    if (!supportsIntersectionObserver || prefersReducedMotion) return;
    
    const options = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Start animations when in view
                entry.target.classList.add('in-view');
                
                // Pause animations when out of view for performance
                const animations = entry.target.getAnimations ? entry.target.getAnimations() : [];
                animations.forEach(animation => {
                    animation.play();
                });
            } else {
                // Pause animations when out of view
                const animations = entry.target.getAnimations ? entry.target.getAnimations() : [];
                animations.forEach(animation => {
                    if (animation.playState === 'running') {
                        animation.pause();
                    }
                });
            }
        });
    }, options);
    
    // Observe all animated elements
    document.querySelectorAll('.gradient-orb, .parallax-bg, .parallax-mid, .parallax-front, .floating-particle, .mesh-gradient').forEach(el => {
        animationObserver.observe(el);
    });
}

// =====================================================
// NAVIGATION ENHANCEMENTS
// =====================================================
function initNavigation() {
    const nav = document.querySelector('.nav');
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section[id]');
    const navProgress = document.createElement('div');
    navProgress.className = 'nav-progress';
    nav.appendChild(navProgress);
    
    // Active section tracking
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
                });
                
                // Update progress bar
                updateNavProgress();
            }
        });
    }, {
        rootMargin: '-50% 0px -50% 0px'
    });
    
    sections.forEach(section => {
        sectionObserver.observe(section);
    });
    
    // Smooth scroll with progress update
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: prefersReducedMotion ? 'auto' : 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Update navigation progress bar
    function updateNavProgress() {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        navProgress.style.width = scrolled + '%';
    }
    
    // Throttled scroll handler
    window.addEventListener('scroll', throttle(updateNavProgress, 100));
}

// =====================================================
// PARTICLE SYSTEM OPTIMIZATION
// =====================================================
function initParticleSystem() {
    if (prefersReducedMotion) return;
    
    const particleContainer = document.querySelector('.hero-particles');
    if (!particleContainer) return;
    
    // Determine particle count based on device
    const isMobile = window.innerWidth <= 768;
    const particleCount = isMobile ? 10 : 20;
    
    // Create particles with staggered animation delays
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'floating-particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = (Math.random() * 20) + 's';
        particle.style.animationDuration = (15 + Math.random() * 10) + 's';
        particleContainer.appendChild(particle);
    }
}

// =====================================================
// MAGNETIC CURSOR EFFECT FOR CTAS
// =====================================================
function initMagneticCursors() {
    if (prefersReducedMotion || 'ontouchstart' in window) return;
    
    const magneticElements = document.querySelectorAll('.btn-primary, .nav-cta, .pricing-btn');
    
    magneticElements.forEach(elem => {
        const magneticWrapper = document.createElement('div');
        magneticWrapper.className = 'magnetic-wrapper';
        elem.parentNode.insertBefore(magneticWrapper, elem);
        magneticWrapper.appendChild(elem);
        
        magneticWrapper.addEventListener('mousemove', (e) => {
            const rect = magneticWrapper.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            elem.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
        });
        
        magneticWrapper.addEventListener('mouseleave', () => {
            elem.style.transform = '';
        });
    });
}

// =====================================================
// PREZI AVATAR INTERACTIONS
// =====================================================
function initPreziAvatar() {
    const avatar = document.querySelector('.prezi-avatar-main');
    const avatarCore = document.querySelector('.prezi-avatar-core');
    
    if (!avatar || !avatarCore) return;
    
    // Add thinking particles on hover
    avatar.addEventListener('mouseenter', () => {
        if (prefersReducedMotion) return;
        
        avatarCore.classList.add('thinking');
        
        // Create thinking particles
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.className = 'thinking-particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.setProperty('--end-x', (50 - Math.random() * 100) + 'px');
            particle.style.setProperty('--end-y', (50 - Math.random() * 100) + 'px');
            particle.style.animationDelay = (i * 0.1) + 's';
            avatar.appendChild(particle);
            
            // Remove particle after animation
            particle.addEventListener('animationend', () => {
                particle.remove();
            });
        }
    });
    
    avatar.addEventListener('mouseleave', () => {
        avatarCore.classList.remove('thinking');
    });
    
    // Excitement on CTA hover
    document.querySelectorAll('.btn-primary').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            avatar.classList.add('excited');
        });
        
        btn.addEventListener('mouseleave', () => {
            avatar.classList.remove('excited');
        });
    });
}

// =====================================================
// LAZY LOADING IMPLEMENTATION
// =====================================================
function initLazyLoading() {
    if (!supportsIntersectionObserver) return;
    
    const lazyImages = document.querySelectorAll('img[data-src]');
    const lazyVideos = document.querySelectorAll('video[data-src]');
    const lazySections = document.querySelectorAll('.lazy-section');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    }, {
        rootMargin: '50px 0px'
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
    
    // Lazy load sections
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('loaded');
                sectionObserver.unobserve(entry.target);
            }
        });
    }, {
        rootMargin: '100px 0px'
    });
    
    lazySections.forEach(section => sectionObserver.observe(section));
}

// =====================================================
// COUNTDOWN TIMER
// =====================================================
function initCountdownTimer() {
    const countdownDays = document.getElementById('countdownDays');
    const countdownHours = document.getElementById('countdownHours');
    const countdownMinutes = document.getElementById('countdownMinutes');
    const countdownSeconds = document.getElementById('countdownSeconds');
    
    if (!countdownDays) return;
    
    // Set target date (5 days from now)
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 5);
    targetDate.setHours(23, 59, 59, 999);
    
    function updateCountdown() {
        const now = new Date();
        const difference = targetDate - now;
        
        if (difference > 0) {
            const days = Math.floor(difference / (1000 * 60 * 60 * 24));
            const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((difference % (1000 * 60)) / 1000);
            
            countdownDays.textContent = days.toString().padStart(2, '0');
            countdownHours.textContent = hours.toString().padStart(2, '0');
            countdownMinutes.textContent = minutes.toString().padStart(2, '0');
            countdownSeconds.textContent = seconds.toString().padStart(2, '0');
            
            // Add urgency animation in last hour
            if (difference < 3600000) {
                document.querySelector('.countdown-timer').classList.add('urgent');
            }
        } else {
            // Timer expired
            document.querySelector('.countdown-timer').innerHTML = '<div class="countdown-expired">Early Access Has Ended</div>';
        }
    }
    
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

// =====================================================
// URGENCY BANNER UPDATES
// =====================================================
function initUrgencyBanner() {
    const spotsElement = document.getElementById('spotsCount');
    if (!spotsElement) return;
    
    let spots = 37;
    const minSpots = 12;
    
    // Decrease spots count randomly
    function updateSpots() {
        if (spots > minSpots) {
            const decrease = Math.random() < 0.3 ? 1 : 0;
            if (decrease) {
                spots--;
                spotsElement.textContent = spots;
                spotsElement.classList.add('pulse');
                setTimeout(() => spotsElement.classList.remove('pulse'), 600);
            }
        }
        
        // Schedule next update
        const nextUpdate = 15000 + Math.random() * 45000; // 15-60 seconds
        setTimeout(updateSpots, nextUpdate);
    }
    
    setTimeout(updateSpots, 10000); // Start after 10 seconds
}

// =====================================================
// SOUND MANAGER CLASS
// =====================================================
class SoundManager {
    constructor() {
        this.soundEnabled = localStorage.getItem('prezI_soundEnabled') !== 'false';
        this.ambientEnabled = localStorage.getItem('prezI_ambientEnabled') === 'true';
        
        // Create audio context on first user interaction
        this.audioContext = null;
        this.sounds = {};
        
        this.updateSoundIcon();
        this.updateAmbientIcon();
    }
    
    async initAudioContext() {
        if (this.audioContext) return;
        
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create simple sound effects using Web Audio API
        this.soundEffects = {
            click: () => this.playTone(800, 0.05),
            hover: () => this.playTone(600, 0.02),
            success: () => this.playChime(),
            notification: () => this.playNotification(),
            error: () => this.playError(),
            whoosh: () => this.playWhoosh()
        };
    }
    
    playTone(frequency, duration) {
        if (!this.soundEnabled || !this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.value = frequency;
        gainNode.gain.value = 0.1;
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + duration);
    }
    
    playChime() {
        if (!this.soundEnabled || !this.audioContext) return;
        
        const frequencies = [523.25, 659.25, 783.99]; // C, E, G
        frequencies.forEach((freq, index) => {
            setTimeout(() => this.playTone(freq, 0.2), index * 100);
        });
    }
    
    playNotification() {
        if (!this.soundEnabled || !this.audioContext) return;
        
        this.playTone(880, 0.1);
        setTimeout(() => this.playTone(1100, 0.1), 100);
    }
    
    playError() {
        if (!this.soundEnabled || !this.audioContext) return;
        
        this.playTone(200, 0.2);
    }
    
    playWhoosh() {
        if (!this.soundEnabled || !this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        const filter = this.audioContext.createBiquadFilter();
        
        oscillator.type = 'noise';
        filter.type = 'highpass';
        filter.frequency.value = 1000;
        
        oscillator.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        gainNode.gain.value = 0.3;
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
        
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + 0.3);
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        localStorage.setItem('prezI_soundEnabled', this.soundEnabled);
        this.updateSoundIcon();
    }
    
    toggleAmbient() {
        this.ambientEnabled = !this.ambientEnabled;
        localStorage.setItem('prezI_ambientEnabled', this.ambientEnabled);
        this.updateAmbientIcon();
        
        if (this.ambientEnabled) {
            this.startAmbientSound();
        } else {
            this.stopAmbientSound();
        }
    }
    
    updateSoundIcon() {
        const soundToggle = document.getElementById('soundToggle');
        if (soundToggle) {
            soundToggle.textContent = this.soundEnabled ? '🔊' : '🔇';
            soundToggle.title = this.soundEnabled ? 'Mute sounds' : 'Enable sounds';
        }
    }
    
    updateAmbientIcon() {
        const ambientToggle = document.getElementById('ambientToggle');
        if (ambientToggle) {
            ambientToggle.textContent = this.ambientEnabled ? '🎵' : '🔇';
            ambientToggle.title = this.ambientEnabled ? 'Disable ambient sound' : 'Enable ambient sound';
        }
    }
    
    startAmbientSound() {
        // Implement ambient sound if needed
    }
    
    stopAmbientSound() {
        // Stop ambient sound if implemented
    }
}

// =====================================================
// HAPTIC FEEDBACK MANAGER
// =====================================================
class HapticManager {
    constructor() {
        this.supportsVibration = 'vibrate' in navigator;
    }
    
    vibrate(pattern) {
        if (this.supportsVibration && !prefersReducedMotion) {
            navigator.vibrate(pattern);
        }
    }
    
    buttonPress() {
        this.vibrate(10);
    }
    
    success() {
        this.vibrate([50, 100, 50]);
    }
    
    error() {
        this.vibrate([100, 50, 100]);
    }
    
    notification() {
        this.vibrate([200, 100, 200]);
    }
    
    swipeFeedback() {
        this.vibrate(5);
    }
}

// =====================================================
// THEME MANAGEMENT
// =====================================================
function initializeTheme() {
    const savedTheme = localStorage.getItem('prezI_theme') || 'dark';
    
    if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    
    updateMetaTags(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    if (newTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else {
        document.documentElement.removeAttribute('data-theme');
    }
    
    localStorage.setItem('prezI_theme', newTheme);
    updateMetaTags(newTheme);
    
    // Track theme change
    if (typeof gtag !== 'undefined') {
        gtag('event', 'theme_change', {
            theme: newTheme,
            interaction_type: 'toggle'
        });
    }
}

function updateMetaTags(theme) {
    const colorSchemeMetaTag = document.querySelector('meta[name="color-scheme"]');
    if (colorSchemeMetaTag) {
        colorSchemeMetaTag.content = theme;
    }
    
    const themeColorMetaTag = document.querySelector('meta[name="theme-color"]');
    if (themeColorMetaTag) {
        themeColorMetaTag.content = theme === 'light' ? '#f8fafc' : '#667eea';
    }
}

// =====================================================
// PROGRESSIVE WEB APP
// =====================================================
function initializePWA() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {
            // Service worker registration failed, app still works
        });
    }
}

// =====================================================
// ACCESSIBILITY FEATURES
// =====================================================
function initializeAccessibility() {
    // Skip to content link
    const skipLink = document.querySelector('.skip-to-content');
    if (skipLink) {
        skipLink.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector('#main-content');
            if (target) {
                target.focus();
                target.scrollIntoView();
            }
        });
    }
    
    // Keyboard navigation enhancements
    document.addEventListener('keydown', (e) => {
        // Escape key closes modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.open');
            openModals.forEach(modal => modal.classList.remove('open'));
        }
    });
}

// =====================================================
// FORM VALIDATION WITH PROGRESS ANIMATIONS
// =====================================================
function initFormValidation() {
    const form = document.getElementById('earlyAccessForm');
    if (!form) return;
    
    const emailInput = document.getElementById('emailInput');
    const companyInput = document.getElementById('companyInput');
    
    // Email validation
    emailInput.addEventListener('input', debounce(() => {
        const field = emailInput.closest('.form-field');
        const isValid = validateEmail(emailInput.value);
        
        if (emailInput.value.length > 0) {
            field.classList.add('validating');
            
            setTimeout(() => {
                field.classList.remove('validating');
                if (isValid) {
                    field.classList.add('valid');
                    field.classList.remove('invalid');
                } else {
                    field.classList.add('invalid');
                    field.classList.remove('valid');
                }
            }, 1000);
        } else {
            field.classList.remove('valid', 'invalid', 'validating');
        }
    }, 500));
    
    // Company input (optional) validation
    companyInput.addEventListener('input', () => {
        const field = companyInput.closest('.form-field');
        if (companyInput.value.length > 0) {
            field.classList.add('valid');
        } else {
            field.classList.remove('valid');
        }
    });
    
    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        // Disable form
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Success state
        submitBtn.textContent = '✓ Success!';
        submitBtn.style.background = 'var(--accent-green)';
        
        // Play success sound
        if (soundManager && soundManager.soundEnabled) {
            soundManager.soundEffects.success();
        }
        
        // Haptic feedback
        if (hapticManager) {
            hapticManager.success();
        }
        
        // Show success message
        setTimeout(() => {
            form.innerHTML = `
                <div class="form-success-message">
                    <div class="success-icon">🎉</div>
                    <h3>Welcome to PrezI Early Access!</h3>
                    <p>Check your email for next steps.</p>
                </div>
            `;
        }, 1500);
    });
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// =====================================================
// MAIN INITIALIZATION
// =====================================================
let soundManager;
let hapticManager;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme first to prevent flash
    initializeTheme();
    
    // Progressive enhancement checks
    if (supportsIntersectionObserver) {
        initIntersectionObserver();
        initLazyLoading();
    }
    
    // Initialize core features
    initNavigation();
    initParticleSystem();
    initMagneticCursors();
    initPreziAvatar();
    initCountdownTimer();
    initUrgencyBanner();
    initFormValidation();
    initializeAccessibility();
    initializePWA();
    
    // Initialize sound and haptics after user interaction
    const initInteractiveFeatures = () => {
        soundManager = new SoundManager();
        hapticManager = new HapticManager();
        soundManager.initAudioContext();
        
        // Remove listeners after initialization
        document.removeEventListener('click', initInteractiveFeatures);
        document.removeEventListener('keydown', initInteractiveFeatures);
        document.removeEventListener('touchstart', initInteractiveFeatures);
    };
    
    document.addEventListener('click', initInteractiveFeatures);
    document.addEventListener('keydown', initInteractiveFeatures);
    document.addEventListener('touchstart', initInteractiveFeatures);
    
    // Remove loading screen
    const loadingScreen = document.querySelector('.loading-skeleton');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => loadingScreen.remove(), 500);
        }, 1000);
    }
});

// Export for use in other modules if needed
window.PreziLanding = {
    soundManager,
    hapticManager,
    toggleTheme,
    initMagneticCursors
};