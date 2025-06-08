/**
 * PrezI Electron Main Process
 * Advanced desktop application with AI integration and real-time communication
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

const { app, BrowserWindow, Menu, dialog, shell, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const WebSocket = require('ws');

/**
 * PrezI Electron Application Class
 * Manages the desktop application lifecycle and Python backend bridge
 */
class PrezIElectronApp {
    constructor() {
        this.mainWindow = null;
        this.pythonBackend = null;
        this.backendReady = false;
        this.wsServer = null;
        this.isQuitting = false;
        
        // Application configuration
        this.config = {
            windowWidth: 1400,
            windowHeight: 900,
            minWidth: 1200,
            minHeight: 800,
            backendPort: process.env.BACKEND_PORT || 8765,
            wsPort: process.env.WS_PORT || 8766,
            isDevelopment: process.env.NODE_ENV === 'development'
        };
    }

    /**
     * Initialize the Electron application
     */
    async initialize() {
        // Wait for Electron to be ready
        await app.whenReady();
        
        console.log('🚀 Initializing PrezI Desktop Application...');
        
        // Create the main application window
        await this.createMainWindow();
        
        // Start the Python backend engine
        await this.startPythonBackend();
        
        // Setup WebSocket server for real-time communication
        await this.setupWebSocketServer();
        
        // Register IPC handlers
        this.registerIPCHandlers();
        
        // Setup application event handlers
        this.setupAppEventHandlers();
        
        console.log('✅ PrezI Desktop Application initialized successfully');
    }

    /**
     * Create the main application window
     */
    async createMainWindow() {
        this.mainWindow = new BrowserWindow({
            width: this.config.windowWidth,
            height: this.config.windowHeight,
            minWidth: this.config.minWidth,
            minHeight: this.config.minHeight,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js'),
                webSecurity: true
            },
            titleBarStyle: 'default',
            icon: path.join(__dirname, 'assets', 'icons', 'prezi-icon.png'),
            show: false, // Don't show until backend is ready
            backgroundColor: '#0a0a0a' // Dark theme background
        });

        // Load the frontend UI
        if (this.config.isDevelopment) {
            this.mainWindow.loadURL(`http://localhost:${this.config.backendPort}`);
            this.mainWindow.webContents.openDevTools();
        } else {
            this.mainWindow.loadFile(path.join(__dirname, 'frontend', 'index.html'));
        }

        // Window event handlers
        this.mainWindow.once('ready-to-show', () => {
            if (this.backendReady) {
                this.mainWindow.show();
                this.mainWindow.focus();
            }
        });

        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
            this.cleanup();
        });

        // Handle external links
        this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
            shell.openExternal(url);
            return { action: 'deny' };
        });

        console.log('📱 Main window created');
    }

    /**
     * Start the Python backend engine
     */
    async startPythonBackend() {
        return new Promise((resolve, reject) => {
            const pythonExecutable = process.env.PYTHON_EXECUTABLE || 'python';
            const backendScript = path.join(__dirname, 'backend', 'main.py');
            
            // Start Python FastAPI server
            this.pythonBackend = spawn(pythonExecutable, [
                backendScript,
                '--host', '127.0.0.1',
                '--port', this.config.backendPort.toString(),
                '--electron-mode'
            ], {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    PREZI_ELECTRON_MODE: 'true',
                    PREZI_FRONTEND_PATH: path.join(__dirname, 'frontend')
                }
            });

            // Handle backend output
            this.pythonBackend.stdout.on('data', (data) => {
                const output = data.toString();
                console.log(`[Backend] ${output}`);
                
                // Check if backend is ready
                if (output.includes('PrezI Backend Engine ready')) {
                    this.backendReady = true;
                    if (this.mainWindow) {
                        this.mainWindow.show();
                        this.mainWindow.focus();
                    }
                    resolve();
                }
            });

            this.pythonBackend.stderr.on('data', (data) => {
                console.error(`[Backend Error] ${data.toString()}`);
            });

            this.pythonBackend.on('close', (code) => {
                console.log(`Backend process exited with code ${code}`);
                if (code !== 0 && !this.isQuitting) {
                    // Backend crashed, show error to user
                    this.showBackendError();
                }
            });

            this.pythonBackend.on('error', (error) => {
                console.error('Failed to start backend:', error);
                reject(error);
            });

            // Timeout after 30 seconds
            setTimeout(() => {
                if (!this.backendReady) {
                    reject(new Error('Backend startup timeout'));
                }
            }, 30000);
        });
    }

    /**
     * Setup WebSocket server for real-time communication
     */
    async setupWebSocketServer() {
        this.wsServer = new WebSocket.Server({ port: this.config.wsPort });
        
        this.wsServer.on('connection', (ws) => {
            console.log('📡 WebSocket client connected');
            
            // Send welcome message
            ws.send(JSON.stringify({
                type: 'connection',
                data: { status: 'connected', timestamp: new Date().toISOString() }
            }));

            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message.toString());
                    this.handleWebSocketMessage(ws, data);
                } catch (error) {
                    console.error('Invalid WebSocket message:', error);
                }
            });

            ws.on('close', () => {
                console.log('📡 WebSocket client disconnected');
            });
        });

        console.log(`🔗 WebSocket server listening on port ${this.config.wsPort}`);
    }

    /**
     * Handle WebSocket messages from frontend
     */
    handleWebSocketMessage(ws, data) {
        switch (data.type) {
            case 'ping':
                ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
                break;
                
            case 'task_progress_subscribe':
                // Subscribe to task progress updates
                this.subscribeToTaskProgress(ws, data.taskId);
                break;
                
            case 'prezi_suggestion_request':
                // Request AI suggestions based on context
                this.handlePreziSuggestionRequest(ws, data);
                break;
                
            default:
                console.warn('Unknown WebSocket message type:', data.type);
        }
    }

    /**
     * Register IPC handlers for native functionality
     */
    registerIPCHandlers() {
        // File system operations
        ipcMain.handle('select-powerpoint-files', async () => {
            const result = await dialog.showOpenDialog(this.mainWindow, {
                properties: ['openFile', 'multiSelections'],
                filters: [
                    { name: 'PowerPoint Files', extensions: ['pptx', 'ppt'] },
                    { name: 'All Files', extensions: ['*'] }
                ]
            });
            
            return result.filePaths;
        });

        ipcMain.handle('select-export-location', async (event, defaultName) => {
            const result = await dialog.showSaveDialog(this.mainWindow, {
                defaultPath: defaultName,
                filters: [
                    { name: 'PowerPoint Files', extensions: ['pptx'] },
                    { name: 'PDF Files', extensions: ['pdf'] }
                ]
            });
            
            return result.filePath;
        });

        ipcMain.handle('open-file-in-system', async (event, filePath) => {
            await shell.openPath(filePath);
        });

        ipcMain.handle('show-item-in-folder', async (event, filePath) => {
            shell.showItemInFolder(filePath);
        });

        // Application control
        ipcMain.handle('app-quit', () => {
            this.cleanup();
            app.quit();
        });

        ipcMain.handle('app-minimize', () => {
            if (this.mainWindow) {
                this.mainWindow.minimize();
            }
        });

        ipcMain.handle('app-maximize', () => {
            if (this.mainWindow) {
                if (this.mainWindow.isMaximized()) {
                    this.mainWindow.unmaximize();
                } else {
                    this.mainWindow.maximize();
                }
            }
        });
    }

    /**
     * Setup application event handlers
     */
    setupAppEventHandlers() {
        app.on('window-all-closed', () => {
            // On macOS, keep app running even when all windows are closed
            if (process.platform !== 'darwin') {
                this.cleanup();
                app.quit();
            }
        });

        app.on('activate', async () => {
            // On macOS, re-create window when dock icon is clicked
            if (BrowserWindow.getAllWindows().length === 0) {
                await this.createMainWindow();
            }
        });

        app.on('before-quit', () => {
            this.isQuitting = true;
            this.cleanup();
        });
    }

    /**
     * Show backend error dialog
     */
    showBackendError() {
        if (this.mainWindow) {
            dialog.showErrorBox(
                'PrezI Backend Error',
                'The PrezI backend engine encountered an error. Please check that Python is installed and try restarting the application.'
            );
        }
    }

    /**
     * Cleanup resources before exit
     */
    cleanup() {
        console.log('🧹 Cleaning up application resources...');
        
        // Close WebSocket server
        if (this.wsServer) {
            this.wsServer.close();
            this.wsServer = null;
        }

        // Terminate Python backend
        if (this.pythonBackend && !this.pythonBackend.killed) {
            this.pythonBackend.kill('SIGTERM');
            
            // Force kill after 5 seconds if still running
            setTimeout(() => {
                if (this.pythonBackend && !this.pythonBackend.killed) {
                    this.pythonBackend.kill('SIGKILL');
                }
            }, 5000);
        }
    }

    /**
     * Subscribe to task progress updates
     */
    subscribeToTaskProgress(ws, taskId) {
        // This would connect to the backend's task progress system
        // For now, we'll simulate progress updates
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            
            ws.send(JSON.stringify({
                type: 'TASK_PROGRESS',
                data: {
                    taskId: taskId,
                    progress: progress,
                    message: `Processing step ${Math.ceil(progress / 10)}...`,
                    timestamp: new Date().toISOString()
                }
            }));

            if (progress >= 100) {
                clearInterval(interval);
                ws.send(JSON.stringify({
                    type: 'TASK_COMPLETE',
                    data: {
                        taskId: taskId,
                        success: true,
                        message: 'Task completed successfully',
                        timestamp: new Date().toISOString()
                    }
                }));
            }
        }, 500);
    }

    /**
     * Handle PrezI AI suggestion requests
     */
    handlePreziSuggestionRequest(ws, data) {
        // This would integrate with the AI service to provide contextual suggestions
        const suggestions = [
            "Try searching for 'revenue charts' to find financial slides",
            "Consider adding a title slide to start your presentation",
            "Your assembly could benefit from a conclusion slide"
        ];

        ws.send(JSON.stringify({
            type: 'PREZI_SUGGESTION',
            data: {
                context: data.context,
                suggestions: suggestions,
                timestamp: new Date().toISOString()
            }
        }));
    }
}

/**
 * Create application menu
 */
function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'New Project',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'new-project');
                    }
                },
                {
                    label: 'Open Project',
                    accelerator: 'CmdOrCtrl+O',
                    click: async () => {
                        const result = await dialog.showOpenDialog(mainWindow, {
                            properties: ['openFile'],
                            filters: [
                                { name: 'PowerPoint Files', extensions: ['pptx', 'ppt'] },
                                { name: 'All Files', extensions: ['*'] }
                            ]
                        });
                        
                        if (!result.canceled && result.filePaths.length > 0) {
                            mainWindow.webContents.send('menu-action', 'open-file', result.filePaths[0]);
                        }
                    }
                },
                { type: 'separator' },
                {
                    label: 'Export Assembly',
                    accelerator: 'CmdOrCtrl+E',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'export-assembly');
                    }
                },
                { type: 'separator' },
                {
                    role: 'quit'
                }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' },
                { role: 'selectall' }
            ]
        },
        {
            label: 'View',
            submenu: [
                {
                    label: 'Projects',
                    accelerator: 'CmdOrCtrl+1',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'switch-view', 'projects');
                    }
                },
                {
                    label: 'Slides',
                    accelerator: 'CmdOrCtrl+2',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'switch-view', 'slides');
                    }
                },
                {
                    label: 'Assembly',
                    accelerator: 'CmdOrCtrl+3',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'switch-view', 'assembly');
                    }
                },
                {
                    label: 'Keywords',
                    accelerator: 'CmdOrCtrl+4',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'switch-view', 'keywords');
                    }
                },
                { type: 'separator' },
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'AI',
            submenu: [
                {
                    label: 'Chat with PrezI',
                    accelerator: 'CmdOrCtrl+Shift+C',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'toggle-chat');
                    }
                },
                {
                    label: 'AI Search',
                    accelerator: 'CmdOrCtrl+Shift+F',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'ai-search');
                    }
                },
                {
                    label: 'Auto-tag Slides',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'auto-tag');
                    }
                }
            ]
        },
        {
            label: 'Window',
            submenu: [
                { role: 'minimize' },
                { role: 'close' }
            ]
        },
        {
            role: 'help',
            submenu: [
                {
                    label: 'About PrezI',
                    click: () => {
                        dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'About PrezI',
                            message: 'PrezI - AI-Powered Slide Management',
                            detail: 'Version 1.0.0\\n\\nYour intelligent presentation assistant for organizing, searching, and assembling PowerPoint slides with AI-powered features.',
                            buttons: ['OK']
                        });
                    }
                },
                {
                    label: 'Documentation',
                    click: () => {
                        shell.openExternal('https://github.com/prezi/working-prezi-app/docs');
                    }
                },
                {
                    label: 'Report Issue',
                    click: () => {
                        shell.openExternal('https://github.com/prezi/working-prezi-app/issues');
                    }
                }
            ]
        }
    ];

    // macOS specific menu adjustments
    if (process.platform === 'darwin') {
        template.unshift({
            label: app.getName(),
            submenu: [
                { role: 'about' },
                { type: 'separator' },
                {
                    label: 'Preferences',
                    accelerator: 'Cmd+,',
                    click: () => {
                        mainWindow.webContents.send('menu-action', 'open-preferences');
                    }
                },
                { type: 'separator' },
                { role: 'services' },
                { type: 'separator' },
                { role: 'hide' },
                { role: 'hideothers' },
                { role: 'unhide' },
                { type: 'separator' },
                { role: 'quit' }
            ]
        });

        // Window menu for macOS
        template[5] = {
            label: 'Window',
            submenu: [
                { role: 'close' },
                { role: 'minimize' },
                { role: 'zoom' },
                { type: 'separator' },
                { role: 'front' }
            ]
        };
    }

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

/**
 * Setup IPC handlers
 */
function setupIPC() {
    // Handle file operations
    ipcMain.handle('select-file', async () => {
        const result = await dialog.showOpenDialog(mainWindow, {
            properties: ['openFile'],
            filters: [
                { name: 'PowerPoint Files', extensions: ['pptx', 'ppt'] },
                { name: 'All Files', extensions: ['*'] }
            ]
        });
        
        return result.canceled ? null : result.filePaths[0];
    });

    // Handle save operations
    ipcMain.handle('save-file', async (event, defaultName, filters) => {
        const result = await dialog.showSaveDialog(mainWindow, {
            defaultPath: defaultName,
            filters: filters || [
                { name: 'PowerPoint Files', extensions: ['pptx'] },
                { name: 'PDF Files', extensions: ['pdf'] }
            ]
        });
        
        return result.canceled ? null : result.filePath;
    });

    // Handle directory selection
    ipcMain.handle('select-directory', async () => {
        const result = await dialog.showOpenDialog(mainWindow, {
            properties: ['openDirectory']
        });
        
        return result.canceled ? null : result.filePaths[0];
    });

    // Handle notifications
    ipcMain.handle('show-notification', (event, title, body) => {
        const { Notification } = require('electron');
        
        if (Notification.isSupported()) {
            new Notification({
                title,
                body,
                icon: path.join(__dirname, 'frontend/assets/icons/icon.png')
            }).show();
        }
    });

    // Handle system info
    ipcMain.handle('get-system-info', () => {
        const os = require('os');
        return {
            platform: process.platform,
            version: process.getSystemVersion(),
            arch: process.arch,
            memory: os.totalmem(),
            cpus: os.cpus().length
        };
    });
}

/**
 * Application event handlers
 */

// Create and initialize the application
const preziApp = new PrezIElectronApp();

// Initialize when Electron is ready
app.whenReady().then(() => {
    preziApp.initialize().catch((error) => {
        console.error('Failed to initialize PrezI application:', error);
        
        // Show error dialog
        dialog.showErrorBox(
            'Startup Error',
            `Failed to start PrezI: ${error.message}\n\nPlease check the logs and try again.`
        );
        
        app.quit();
    });
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
    contents.on('new-window', (event, url) => {
        event.preventDefault();
        shell.openExternal(url);
    });
});

// Handle certificate errors
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
    if (url.startsWith('https://localhost') || url.startsWith('https://127.0.0.1')) {
        // Allow localhost certificates in development
        event.preventDefault();
        callback(true);
    } else {
        callback(false);
    }
});

// Export for testing
module.exports = { PrezIElectronApp };