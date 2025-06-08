/**
 * PrezI Application - Main Application Controller
 * Handles application initialization, routing, and global state management
 */

window.PreziApp = (function() {
    'use strict';

    // Application state
    let state = {
        initialized: false,
        currentView: 'projects',
        user: null,
        settings: {
            theme: 'light',
            defaultExportFormat: 'pptx',
            enableAutoTagging: true,
            openaiApiKey: ''
        },
        projects: [],
        slides: [],
        keywords: [],
        assembly: [],
        loading: false
    };

    // DOM elements cache
    let elements = {};

    /**
     * Initialize the application
     */
    function init() {
        console.log('🚀 Initializing PrezI Application...');
        
        try {
            // Cache DOM elements
            cacheElements();
            
            // Load user settings
            loadSettings();
            
            // Apply theme
            applyTheme();
            
            // Set up event listeners
            setupEventListeners();
            
            // Initialize components
            initializeComponents();
            
            // Check if first time user
            checkFirstTimeUser();
            
            // Load initial data
            loadInitialData();
            
            state.initialized = true;
            console.log('✅ PrezI Application initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize application:', error);
            showError('Failed to initialize application. Please refresh the page.');
        }
    }

    /**
     * Cache frequently used DOM elements
     */
    function cacheElements() {
        elements = {
            // Main containers
            app: document.getElementById('app'),
            welcomeScreen: document.getElementById('welcomeScreen'),
            mainApp: document.getElementById('mainApp'),
            
            // Header elements
            globalSearch: document.getElementById('globalSearch'),
            searchResults: document.getElementById('searchResults'),
            aiSearchBtn: document.getElementById('aiSearchBtn'),
            
            // Navigation
            navItems: document.querySelectorAll('.nav-item'),
            
            // Views
            views: document.querySelectorAll('.view'),
            projectsView: document.getElementById('projectsView'),
            slidesView: document.getElementById('slidesView'),
            assemblyView: document.getElementById('assemblyView'),
            keywordsView: document.getElementById('keywordsView'),
            
            // Buttons
            createProjectBtn: document.getElementById('createProjectBtn'),
            settingsBtn: document.getElementById('settingsBtn'),
            helpBtn: document.getElementById('helpBtn'),
            chatToggleBtn: document.getElementById('chatToggleBtn'),
            
            // Modals
            modalOverlay: document.getElementById('modalOverlay'),
            createProjectModal: document.getElementById('createProjectModal'),
            settingsModal: document.getElementById('settingsModal'),
            
            // Chat
            preziChat: document.getElementById('preziChat'),
            chatMessages: document.getElementById('chatMessages'),
            chatInput: document.getElementById('chatInput'),
            sendChatBtn: document.getElementById('sendChatBtn'),
            
            // Loading
            loadingOverlay: document.getElementById('loadingOverlay'),
            loadingMessage: document.getElementById('loadingMessage'),
            
            // Content containers
            projectsGrid: document.getElementById('projectsGrid'),
            slidesGrid: document.getElementById('slidesGrid'),
            keywordsGrid: document.getElementById('keywordsGrid'),
            assemblySlides: document.getElementById('assemblySlides')
        };
    }

    /**
     * Set up global event listeners
     */
    function setupEventListeners() {
        // Navigation
        elements.navItems.forEach(item => {
            item.addEventListener('click', handleNavigation);
        });

        // Search
        elements.globalSearch.addEventListener('input', debounce(handleSearch, 300));
        elements.aiSearchBtn.addEventListener('click', handleAISearch);

        // Buttons
        elements.createProjectBtn.addEventListener('click', () => openModal('createProjectModal'));
        elements.settingsBtn.addEventListener('click', () => openModal('settingsModal'));
        elements.helpBtn.addEventListener('click', showHelp);
        elements.chatToggleBtn.addEventListener('click', toggleChat);

        // Chat
        elements.sendChatBtn.addEventListener('click', sendChatMessage);
        elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });

        // Modal handling
        setupModalHandlers();

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeyboardShortcuts);

        // Window events
        window.addEventListener('beforeunload', saveUserData);
        window.addEventListener('resize', handleResize);
    }

    /**
     * Handle navigation between views
     */
    function handleNavigation(event) {
        const targetView = event.currentTarget.dataset.view;
        if (targetView && targetView !== state.currentView) {
            switchView(targetView);
        }
    }

    /**
     * Switch to a different view
     */
    function switchView(viewName) {
        console.log(`🔄 Switching to view: ${viewName}`);
        
        // Update navigation state
        elements.navItems.forEach(item => {
            if (item.dataset.view === viewName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Update view visibility
        elements.views.forEach(view => {
            if (view.id === `${viewName}View`) {
                view.classList.add('active');
            } else {
                view.classList.remove('active');
            }
        });

        // Update state
        state.currentView = viewName;

        // Load view-specific data
        loadViewData(viewName);

        // Trigger view change event
        window.dispatchEvent(new CustomEvent('viewChanged', { 
            detail: { view: viewName } 
        }));
    }

    /**
     * Load data for specific view
     */
    async function loadViewData(viewName) {
        try {
            switch (viewName) {
                case 'projects':
                    await window.ProjectsView.loadProjects();
                    break;
                case 'slides':
                    await window.SlidesView.loadSlides();
                    break;
                case 'assembly':
                    await window.AssemblyView.loadAssembly();
                    break;
                case 'keywords':
                    await window.KeywordsView.loadKeywords();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load data for ${viewName}:`, error);
            showError(`Failed to load ${viewName} data`);
        }
    }

    /**
     * Handle global search
     */
    async function handleSearch(event) {
        const query = event.target.value.trim();
        
        if (query.length < 2) {
            hideSearchResults();
            return;
        }

        try {
            showLoading('Searching...');
            const results = await window.API.search({
                query: query,
                limit: 10
            });
            
            displaySearchResults(results);
        } catch (error) {
            console.error('Search failed:', error);
            showError('Search failed');
        } finally {
            hideLoading();
        }
    }

    /**
     * Handle AI-powered search
     */
    async function handleAISearch() {
        const query = elements.globalSearch.value.trim();
        
        if (!query) {
            showError('Please enter a search query');
            return;
        }

        try {
            showLoading('AI is analyzing your query...');
            const results = await window.AIService.naturalLanguageSearch(query);
            displaySearchResults(results, true);
        } catch (error) {
            console.error('AI search failed:', error);
            showError('AI search failed');
        } finally {
            hideLoading();
        }
    }

    /**
     * Display search results
     */
    function displaySearchResults(results, isAI = false) {
        const container = elements.searchResults;
        
        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="search-no-results">
                    <i class="fas fa-search"></i>
                    <p>No results found</p>
                </div>
            `;
        } else {
            container.innerHTML = results.map(result => `
                <div class="search-result" data-id="${result.id}" data-type="${result.type}">
                    <div class="search-result-icon">
                        <i class="fas fa-${getResultIcon(result.type)}"></i>
                    </div>
                    <div class="search-result-content">
                        <h4>${result.title || result.name}</h4>
                        <p>${result.summary || result.description || ''}</p>
                        ${isAI ? `<small class="ai-confidence">AI Confidence: ${Math.round(result.confidence * 100)}%</small>` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        container.classList.remove('hidden');
        
        // Add click handlers for results
        container.querySelectorAll('.search-result').forEach(result => {
            result.addEventListener('click', () => {
                openSearchResult(result.dataset.id, result.dataset.type);
                hideSearchResults();
            });
        });
    }

    /**
     * Hide search results
     */
    function hideSearchResults() {
        elements.searchResults.classList.add('hidden');
    }

    /**
     * Get icon for search result type
     */
    function getResultIcon(type) {
        const icons = {
            project: 'folder',
            file: 'file-powerpoint',
            slide: 'image',
            keyword: 'tag'
        };
        return icons[type] || 'file';
    }

    /**
     * Open search result
     */
    function openSearchResult(id, type) {
        switch (type) {
            case 'project':
                switchView('projects');
                // Highlight project
                break;
            case 'slide':
                switchView('slides');
                // Highlight slide
                break;
            case 'keyword':
                switchView('keywords');
                // Highlight keyword
                break;
        }
    }

    /**
     * Initialize components
     */
    function initializeComponents() {
        // Initialize view components
        if (window.ProjectsView) window.ProjectsView.init();
        if (window.SlidesView) window.SlidesView.init();
        if (window.AssemblyView) window.AssemblyView.init();
        if (window.KeywordsView) window.KeywordsView.init();
        
        // Initialize services
        if (window.AIService) window.AIService.init();
        if (window.FileService) window.FileService.init();
        if (window.ExportService) window.ExportService.init();
    }

    /**
     * Check if first time user
     */
    function checkFirstTimeUser() {
        const hasVisited = localStorage.getItem('prezi_has_visited');
        if (!hasVisited) {
            showWelcomeScreen();
            localStorage.setItem('prezi_has_visited', 'true');
        }
    }

    /**
     * Show welcome screen
     */
    function showWelcomeScreen() {
        elements.welcomeScreen.classList.remove('hidden');
        elements.mainApp.classList.add('hidden');
        
        // Welcome screen event handlers
        document.getElementById('startTourBtn').addEventListener('click', startTour);
        document.getElementById('skipTourBtn').addEventListener('click', skipTour);
    }

    /**
     * Start guided tour
     */
    function startTour() {
        hideWelcomeScreen();
        // TODO: Implement guided tour
        showNotification('Welcome to PrezI! Tour coming soon.', 'info');
    }

    /**
     * Skip tour
     */
    function skipTour() {
        hideWelcomeScreen();
    }

    /**
     * Hide welcome screen
     */
    function hideWelcomeScreen() {
        elements.welcomeScreen.classList.add('hidden');
        elements.mainApp.classList.remove('hidden');
    }

    /**
     * Load initial application data
     */
    async function loadInitialData() {
        try {
            showLoading('Loading application data...');
            
            // Load projects (default view)
            await loadViewData('projects');
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            showError('Failed to load application data');
        } finally {
            hideLoading();
        }
    }

    /**
     * Load user settings
     */
    function loadSettings() {
        const saved = localStorage.getItem('prezi_settings');
        if (saved) {
            try {
                state.settings = { ...state.settings, ...JSON.parse(saved) };
            } catch (error) {
                console.error('Failed to load settings:', error);
            }
        }
    }

    /**
     * Save user settings
     */
    function saveSettings() {
        localStorage.setItem('prezi_settings', JSON.stringify(state.settings));
    }

    /**
     * Apply theme
     */
    function applyTheme() {
        const theme = state.settings.theme;
        document.documentElement.setAttribute('data-theme', theme);
    }

    /**
     * Show loading overlay
     */
    function showLoading(message = 'Loading...') {
        state.loading = true;
        elements.loadingMessage.textContent = message;
        elements.loadingOverlay.classList.remove('hidden');
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        state.loading = false;
        elements.loadingOverlay.classList.add('hidden');
    }

    /**
     * Show error notification
     */
    function showError(message) {
        if (window.Notifications) {
            window.Notifications.error(message);
        } else {
            alert(message);
        }
    }

    /**
     * Show success notification
     */
    function showSuccess(message) {
        if (window.Notifications) {
            window.Notifications.success(message);
        } else {
            console.log('Success:', message);
        }
    }

    /**
     * Show info notification
     */
    function showNotification(message, type = 'info') {
        if (window.Notifications) {
            window.Notifications[type](message);
        } else {
            console.log(`${type.toUpperCase()}:`, message);
        }
    }

    /**
     * Modal handling
     */
    function setupModalHandlers() {
        // Close modal when clicking overlay
        elements.modalOverlay.addEventListener('click', closeAllModals);
        
        // Close modal buttons
        document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
            btn.addEventListener('click', closeAllModals);
        });
        
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeAllModals();
        });
    }

    /**
     * Open modal
     */
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            elements.modalOverlay.classList.remove('hidden');
            modal.classList.remove('hidden');
            
            // Focus first input
            const firstInput = modal.querySelector('input, textarea, select');
            if (firstInput) firstInput.focus();
        }
    }

    /**
     * Close all modals
     */
    function closeAllModals() {
        elements.modalOverlay.classList.add('hidden');
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    /**
     * Toggle chat
     */
    function toggleChat() {
        if (elements.preziChat.classList.contains('hidden')) {
            elements.preziChat.classList.remove('hidden');
            elements.chatInput.focus();
        } else {
            elements.preziChat.classList.add('hidden');
        }
    }

    /**
     * Send chat message
     */
    async function sendChatMessage() {
        const message = elements.chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addChatMessage(message, 'user');
        elements.chatInput.value = '';
        
        try {
            // Send to AI service
            const response = await window.AIService.chatWithPrezI(message);
            addChatMessage(response, 'assistant');
        } catch (error) {
            console.error('Chat failed:', error);
            addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    }

    /**
     * Add message to chat
     */
    function addChatMessage(content, sender) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}`;
        messageEl.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">${content}</div>
        `;
        
        elements.chatMessages.appendChild(messageEl);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    /**
     * Show help
     */
    function showHelp() {
        showNotification('Help documentation coming soon!', 'info');
    }

    /**
     * Handle keyboard shortcuts
     */
    function handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K for search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            elements.globalSearch.focus();
        }
        
        // Ctrl/Cmd + 1-4 for navigation
        if (event.ctrlKey || event.metaKey) {
            const num = parseInt(event.key);
            if (num >= 1 && num <= 4) {
                event.preventDefault();
                const views = ['projects', 'slides', 'assembly', 'keywords'];
                switchView(views[num - 1]);
            }
        }
    }

    /**
     * Handle window resize
     */
    function handleResize() {
        // Update layout if needed
        window.dispatchEvent(new CustomEvent('layoutChange'));
    }

    /**
     * Save user data before unload
     */
    function saveUserData() {
        saveSettings();
    }

    /**
     * Debounce function
     */
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

    // Public API
    return {
        init,
        switchView,
        showLoading,
        hideLoading,
        showError,
        showSuccess,
        showNotification,
        openModal,
        closeAllModals,
        getState: () => ({ ...state }),
        updateSettings: (newSettings) => {
            state.settings = { ...state.settings, ...newSettings };
            saveSettings();
            applyTheme();
        }
    };
})();