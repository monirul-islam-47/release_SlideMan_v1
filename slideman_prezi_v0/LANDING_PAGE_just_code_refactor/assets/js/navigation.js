// PrezI Navigation Component JavaScript

function togglePreziNav() {
    const nav = document.getElementById('preziNav');
    nav.classList.toggle('active');
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const nav = document.getElementById('preziNav');
    if (!nav.contains(event.target) && nav.classList.contains('active')) {
        nav.classList.remove('active');
    }
});

// Load navigation component into page
function loadNavigationComponent() {
    // Determine the correct path based on current location
    const isInPagesDir = window.location.pathname.includes('/pages/');
    const navPath = isInPagesDir ? '../assets/components/navigation.html' : './assets/components/navigation.html';
    
    fetch(navPath)
        .then(response => response.text())
        .then(html => {
            const navContainer = document.createElement('div');
            navContainer.innerHTML = html;
            
            // Update navigation links for pages subdirectory
            if (isInPagesDir) {
                const links = navContainer.querySelectorAll('a[href]');
                links.forEach(link => {
                    const href = link.getAttribute('href');
                    if (href.startsWith('pages/')) {
                        // Remove 'pages/' prefix when we're already in pages directory
                        link.setAttribute('href', href.replace('pages/', ''));
                    } else if (!href.startsWith('http') && !href.startsWith('../') && !href.includes('.md')) {
                        // Add '../' prefix for relative links to parent directory
                        link.setAttribute('href', '../' + href);
                    }
                });
            }
            
            document.body.appendChild(navContainer);
        })
        .catch(error => {
            console.error('Error loading navigation component:', error);
        });
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only load if navigation doesn't already exist
    if (!document.getElementById('preziNav')) {
        loadNavigationComponent();
    }
});