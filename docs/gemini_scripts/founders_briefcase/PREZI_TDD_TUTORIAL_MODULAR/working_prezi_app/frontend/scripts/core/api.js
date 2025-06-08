/**
 * PrezI API Client - HTTP interface to backend services
 * Provides a clean interface for all backend API interactions
 */

window.API = (function() {
    'use strict';

    const BASE_URL = window.location.hostname === 'localhost' 
        ? 'http://localhost:8000/api/v1'
        : '/api/v1';

    // Configure axios defaults
    axios.defaults.baseURL = BASE_URL;
    axios.defaults.timeout = 30000; // 30 seconds
    axios.defaults.headers.common['Content-Type'] = 'application/json';

    // Request interceptor for loading states
    axios.interceptors.request.use(
        config => {
            console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
            return config;
        },
        error => {
            console.error('❌ API Request Error:', error);
            return Promise.reject(error);
        }
    );

    // Response interceptor for error handling
    axios.interceptors.response.use(
        response => {
            console.log(`✅ API Response: ${response.status} ${response.config.url}`);
            return response;
        },
        error => {
            console.error('❌ API Response Error:', error);
            handleApiError(error);
            return Promise.reject(error);
        }
    );

    /**
     * Handle API errors with user-friendly messages
     */
    function handleApiError(error) {
        let message = 'An unexpected error occurred';

        if (error.response) {
            // Server responded with error status
            const status = error.response.status;
            const data = error.response.data;

            switch (status) {
                case 400:
                    message = data.detail || 'Invalid request';
                    break;
                case 401:
                    message = 'Authentication required';
                    break;
                case 403:
                    message = 'Access denied';
                    break;
                case 404:
                    message = 'Resource not found';
                    break;
                case 429:
                    message = 'Too many requests. Please wait a moment.';
                    break;
                case 500:
                    message = 'Server error. Please try again later.';
                    break;
                default:
                    message = data.detail || `Server error (${status})`;
            }
        } else if (error.request) {
            // Network error
            message = 'Network error. Please check your connection.';
        }

        // Show error notification
        if (window.Notifications) {
            window.Notifications.error(message);
        }
    }

    /**
     * Generic API request wrapper
     */
    async function request(method, endpoint, data = null, options = {}) {
        try {
            const config = {
                method,
                url: endpoint,
                ...options
            };

            if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
                config.data = data;
            } else if (data && method === 'GET') {
                config.params = data;
            }

            const response = await axios(config);
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    // ===== HEALTH & STATUS ENDPOINTS =====

    const health = {
        check: () => request('GET', '/health'),
        detailed: () => request('GET', '/health/detailed'),
        database: () => request('GET', '/health/database')
    };

    const status = {
        version: () => request('GET', '/version'),
        status: () => request('GET', '/status')
    };

    // ===== PROJECT ENDPOINTS =====

    const projects = {
        list: (params = {}) => request('GET', '/projects', params),
        
        get: (id) => request('GET', `/projects/${id}`),
        
        create: (data) => request('POST', '/projects', data),
        
        update: (id, data) => request('PUT', `/projects/${id}`, data),
        
        delete: (id, permanent = false) => 
            request('DELETE', `/projects/${id}`, { permanent }),
        
        restore: (id) => request('POST', `/projects/${id}/restore`),
        
        stats: (id) => request('GET', `/projects/${id}/stats`),
        
        activity: (id, limit = 10) => 
            request('GET', `/projects/${id}/recent-activity`, { limit })
    };

    // ===== FILE ENDPOINTS =====

    const files = {
        list: (params = {}) => request('GET', '/files', params),
        
        get: (id) => request('GET', `/files/${id}`),
        
        upload: async (projectId, file, onProgress = null) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('project_id', projectId);

            const config = {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            };

            if (onProgress) {
                config.onUploadProgress = (progressEvent) => {
                    const progress = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    );
                    onProgress(progress);
                };
            }

            return request('POST', '/files/upload', formData, config);
        },
        
        process: (id) => request('POST', `/files/${id}/process`),
        
        delete: (id) => request('DELETE', `/files/${id}`),
        
        reprocess: (id) => request('POST', `/files/${id}/reprocess`)
    };

    // ===== SLIDE ENDPOINTS =====

    const slides = {
        list: (params = {}) => request('GET', '/slides', params),
        
        get: (id) => request('GET', `/slides/${id}`),
        
        update: (id, data) => request('PUT', `/slides/${id}`, data),
        
        addKeywords: (id, keywordIds) => 
            request('POST', `/slides/${id}/keywords`, { 
                keyword_ids: keywordIds, 
                action: 'add' 
            }),
        
        removeKeywords: (id, keywordIds) => 
            request('POST', `/slides/${id}/keywords`, { 
                keyword_ids: keywordIds, 
                action: 'remove' 
            }),
        
        replaceKeywords: (id, keywordIds) => 
            request('POST', `/slides/${id}/keywords`, { 
                keyword_ids: keywordIds, 
                action: 'replace' 
            }),
        
        analyze: (id) => request('POST', `/slides/${id}/analyze`),
        
        thumbnail: (id) => `${BASE_URL}/slides/${id}/thumbnail`,
        
        fullImage: (id) => `${BASE_URL}/slides/${id}/image`
    };

    // ===== ELEMENT ENDPOINTS =====

    const elements = {
        list: (slideId) => request('GET', `/slides/${slideId}/elements`),
        
        get: (id) => request('GET', `/elements/${id}`),
        
        update: (id, data) => request('PUT', `/elements/${id}`, data),
        
        addKeywords: (id, keywordIds) => 
            request('POST', `/elements/${id}/keywords`, { 
                keyword_ids: keywordIds, 
                action: 'add' 
            }),
        
        removeKeywords: (id, keywordIds) => 
            request('POST', `/elements/${id}/keywords`, { 
                keyword_ids: keywordIds, 
                action: 'remove' 
            }),
        
        analyze: (id) => request('POST', `/elements/${id}/analyze`)
    };

    // ===== KEYWORD ENDPOINTS =====

    const keywords = {
        list: (params = {}) => request('GET', '/keywords', params),
        
        get: (id) => request('GET', `/keywords/${id}`),
        
        create: (data) => request('POST', '/keywords', data),
        
        update: (id, data) => request('PUT', `/keywords/${id}`, data),
        
        delete: (id) => request('DELETE', `/keywords/${id}`),
        
        usage: (id) => request('GET', `/keywords/${id}/usage`),
        
        merge: (sourceId, targetId) => 
            request('POST', `/keywords/${sourceId}/merge`, { target_id: targetId })
    };

    // ===== ASSEMBLY ENDPOINTS =====

    const assemblies = {
        list: (params = {}) => request('GET', '/assemblies', params),
        
        get: (id) => request('GET', `/assemblies/${id}`),
        
        create: (data) => request('POST', '/assemblies', data),
        
        update: (id, data) => request('PUT', `/assemblies/${id}`, data),
        
        delete: (id) => request('DELETE', `/assemblies/${id}`),
        
        addSlide: (id, slideId, position = null) => 
            request('POST', `/assemblies/${id}/slides`, { 
                slide_id: slideId, 
                position 
            }),
        
        removeSlide: (id, slideId) => 
            request('DELETE', `/assemblies/${id}/slides/${slideId}`),
        
        reorderSlides: (id, slideIds) => 
            request('PUT', `/assemblies/${id}/order`, { slide_ids: slideIds }),
        
        clear: (id) => request('DELETE', `/assemblies/${id}/slides`)
    };

    // ===== SEARCH ENDPOINTS =====

    const search = {
        global: (params = {}) => request('GET', '/search', params),
        
        slides: (params = {}) => request('GET', '/search/slides', params),
        
        projects: (params = {}) => request('GET', '/search/projects', params),
        
        keywords: (params = {}) => request('GET', '/search/keywords', params)
    };

    // ===== AI ENDPOINTS =====

    const ai = {
        analyze: (data) => request('POST', '/ai/analyze', data),
        
        suggestKeywords: (content, context = 'general') => 
            request('POST', '/ai/suggest-keywords', { content, context }),
        
        naturalLanguageSearch: (query, availableContent = []) => 
            request('POST', '/ai/natural-search', { 
                query, 
                available_content: availableContent 
            }),
        
        generatePlan: (intent, availableSlides = []) => 
            request('POST', '/ai/generate-plan', { 
                intent, 
                available_slides: availableSlides 
            }),
        
        chat: (message, context = {}) => 
            request('POST', '/ai/chat', { message, context }),
        
        autoTag: (contentId, contentType) => 
            request('POST', '/ai/auto-tag', { 
                content_id: contentId, 
                content_type: contentType 
            }),
        
        status: () => request('GET', '/ai/status')
    };

    // ===== EXPORT ENDPOINTS =====

    const exports = {
        assembly: async (assemblyId, options = {}) => {
            const response = await request('POST', '/export/assembly', {
                assembly_id: assemblyId,
                ...options
            });
            
            // Handle file download
            if (response.file_path) {
                downloadFile(response.file_path, response.filename);
            }
            
            return response;
        },
        
        slides: async (slideIds, options = {}) => {
            const response = await request('POST', '/export/slides', {
                slide_ids: slideIds,
                ...options
            });
            
            if (response.file_path) {
                downloadFile(response.file_path, response.filename);
            }
            
            return response;
        },
        
        status: (exportId) => request('GET', `/export/${exportId}/status`),
        
        download: (exportId) => {
            const url = `${BASE_URL}/export/${exportId}/download`;
            window.open(url, '_blank');
        }
    };

    /**
     * Download file helper
     */
    function downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // ===== UTILITY FUNCTIONS =====

    /**
     * Upload file with progress tracking
     */
    async function uploadWithProgress(endpoint, file, onProgress = null, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add additional data
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        const config = {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        };

        if (onProgress) {
            config.onUploadProgress = (progressEvent) => {
                const progress = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                );
                onProgress(progress);
            };
        }

        return request('POST', endpoint, formData, config);
    }

    /**
     * Batch request helper
     */
    async function batchRequest(requests) {
        try {
            const responses = await Promise.allSettled(requests);
            return responses.map(response => {
                if (response.status === 'fulfilled') {
                    return { success: true, data: response.value };
                } else {
                    return { success: false, error: response.reason };
                }
            });
        } catch (error) {
            throw error;
        }
    }

    /**
     * Check if API is available
     */
    async function checkConnection() {
        try {
            await health.check();
            return true;
        } catch (error) {
            return false;
        }
    }

    // Public API
    return {
        // Core request method
        request,
        
        // API modules
        health,
        status,
        projects,
        files,
        slides,
        elements,
        keywords,
        assemblies,
        search,
        ai,
        exports,
        
        // Utilities
        uploadWithProgress,
        batchRequest,
        checkConnection,
        downloadFile,
        
        // Configuration
        BASE_URL,
        setBaseURL: (url) => {
            axios.defaults.baseURL = url;
            BASE_URL = url;
        },
        
        setTimeout: (timeout) => {
            axios.defaults.timeout = timeout;
        }
    };
})();