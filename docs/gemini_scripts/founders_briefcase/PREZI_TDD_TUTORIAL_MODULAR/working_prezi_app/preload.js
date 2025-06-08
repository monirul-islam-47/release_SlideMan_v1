/**
 * Preload Script for PrezI Electron Application
 * Secure bridge between renderer and main process
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Secure API bridge for PrezI frontend
 * Exposes only necessary native functionality to the renderer process
 */
contextBridge.exposeInMainWorld('electronAPI', {
    // File system operations
    selectPowerPointFiles: () => ipcRenderer.invoke('select-powerpoint-files'),
    selectExportLocation: (defaultName) => ipcRenderer.invoke('select-export-location', defaultName),
    openFileInSystem: (filePath) => ipcRenderer.invoke('open-file-in-system', filePath),
    showItemInFolder: (filePath) => ipcRenderer.invoke('show-item-in-folder', filePath),

    // Application control
    quit: () => ipcRenderer.invoke('app-quit'),
    minimize: () => ipcRenderer.invoke('app-minimize'),
    maximize: () => ipcRenderer.invoke('app-maximize'),

    // System information
    platform: process.platform,
    version: process.versions.electron,
    
    // Menu actions (receive from main process)
    onMenuAction: (callback) => ipcRenderer.on('menu-action', callback),
    removeMenuActionListener: (callback) => ipcRenderer.removeListener('menu-action', callback)
});

/**
 * WebSocket API for real-time communication
 */
contextBridge.exposeInMainWorld('wsAPI', {
    connect: (url) => {
        return new WebSocket(url);
    },
    
    createConnection: () => {
        const ws = new WebSocket('ws://localhost:8766');
        return ws;
    }
});

/**
 * PrezI specific APIs for enhanced functionality
 */
contextBridge.exposeInMainWorld('preziAPI', {
    // Task progress tracking
    subscribeToTaskProgress: (taskId) => {
        const ws = new WebSocket('ws://localhost:8766');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'task_progress_subscribe',
                taskId: taskId
            }));
        };
        
        return ws;
    },
    
    // AI suggestion requests
    requestSuggestions: (context) => {
        const ws = new WebSocket('ws://localhost:8766');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'prezi_suggestion_request',
                context: context
            }));
        };
        
        return ws;
    },
    
    // Ping/pong for connection health
    ping: () => {
        const ws = new WebSocket('ws://localhost:8766');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'ping'
            }));
        };
        
        return ws;
    }
});

/**
 * Development and debugging utilities
 */
if (process.env.NODE_ENV === 'development') {
    contextBridge.exposeInMainWorld('devAPI', {
        // Debug logging
        log: (...args) => console.log('[Preload]', ...args),
        
        // Performance monitoring
        performance: {
            now: () => performance.now(),
            mark: (name) => performance.mark(name),
            measure: (name, start, end) => performance.measure(name, start, end)
        },
        
        // Environment info
        env: {
            NODE_ENV: process.env.NODE_ENV,
            platform: process.platform,
            versions: process.versions
        }
    });
}

console.log('🔗 Preload script loaded successfully');

/**
 * Security hardening
 */

// Prevent access to Node.js APIs
delete window.require;
delete window.exports;
delete window.module;

// Disable eval and similar functions
window.eval = () => {
    throw new Error('eval() is disabled for security reasons');
};

// Override console methods in production
if (process.env.NODE_ENV === 'production') {
    const allowedLevels = ['error', 'warn'];
    
    Object.keys(console).forEach(method => {
        if (!allowedLevels.includes(method)) {
            console[method] = () => {};
        }
    });
}

/**
 * Error handling and reporting
 */
window.addEventListener('error', (event) => {
    console.error('Renderer error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});

/**
 * Application lifecycle hooks
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 DOM content loaded, PrezI frontend ready');
    
    // Add performance monitoring for development
    if (process.env.NODE_ENV === 'development') {
        const loadTime = performance.now();
        console.log(`⚡ Preload script execution time: ${loadTime.toFixed(2)}ms`);
    }
});