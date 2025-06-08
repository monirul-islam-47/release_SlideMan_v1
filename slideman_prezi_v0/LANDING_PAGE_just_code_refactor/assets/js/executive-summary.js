// Executive Summary JavaScript

// Smooth scroll behavior
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

// Animate stats on scroll
const animateValue = (element, start, end, duration) => {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        
        if (element.textContent.includes('€')) {
            element.textContent = '€' + Math.floor(current) + element.textContent.slice(element.textContent.indexOf(' '));
        } else if (element.textContent.includes('$')) {
            element.textContent = '$' + Math.floor(current) + element.textContent.slice(element.textContent.indexOf(' '));
        } else if (element.textContent.includes('%')) {
            element.textContent = Math.floor(current) + '%';
        } else {
            element.textContent = Math.floor(current) + '+';
        }
    }, 16);
};

// Intersection Observer for animations
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            
            // Animate numbers
            if (entry.target.classList.contains('stat-number')) {
                const text = entry.target.textContent;
                if (text.includes('$')) {
                    animateValue(entry.target, 0, 50, 1500);
                } else if (text.includes('%')) {
                    animateValue(entry.target, 0, 90, 1500);
                } else if (text.includes('K')) {
                    entry.target.textContent = '500K+';
                }
            }
            
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

// Observe elements
document.querySelectorAll('.subsection, .feature-card, .roadmap-item, .stat-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});