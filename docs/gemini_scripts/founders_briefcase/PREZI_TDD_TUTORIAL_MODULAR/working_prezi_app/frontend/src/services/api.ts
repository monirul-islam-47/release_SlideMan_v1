/**
 * API Service Layer for PrezI Frontend
 * Comprehensive service layer that interfaces with all backend services
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import {
  SearchResult,
  SearchFilter,
  SearchSuggestion,
  AssemblyData,
  SlideData,
  TemplateData,
  ProjectData,
  AIAnalysisResult,
  AssemblyOptimizationResult,
  ExportResult,
  CollaborationSession,
  CollaborationUpdate,
  ApiError
} from '../types/api'

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'
const API_TIMEOUT = 30000

// Create axios instance with default config
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  })

  // Request interceptor for authentication
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      // Add request ID for tracking
      config.headers['X-Request-ID'] = generateRequestId()
      
      return config
    },
    (error) => {
      console.error('Request interceptor error:', error)
      return Promise.reject(error)
    }
  )

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => {
      // Log successful requests in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
      }
      return response
    },
    (error: AxiosError) => {
      // Enhanced error handling
      const apiError: ApiError = {
        message: 'An unexpected error occurred',
        status: error.response?.status || 0
      }

      if (error.response?.data) {
        const errorData = error.response.data as any
        apiError.message = errorData.message || errorData.error || apiError.message
        apiError.code = errorData.code
        apiError.details = errorData.details
      } else if (error.request) {
        apiError.message = 'Network error - please check your connection'
      } else {
        apiError.message = error.message || apiError.message
      }

      // Handle specific error cases
      if (error.response?.status === 401) {
        apiError.message = 'Authentication required'
        // Clear invalid token
        localStorage.removeItem('auth_token')
        // Redirect to login if needed
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      } else if (error.response?.status === 403) {
        apiError.message = 'Access denied'
      } else if (error.response?.status === 404) {
        apiError.message = 'Resource not found'
      } else if (error.response?.status >= 500) {
        apiError.message = 'Server error - please try again later'
      }

      console.error('API Error:', apiError)
      return Promise.reject(apiError)
    }
  )

  return client
}

// Create API client instance
const apiClient = createApiClient()

// Utility functions
const generateRequestId = (): string => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

const handleApiError = (error: any): never => {
  if (error.response?.data) {
    throw error.response.data
  }
  throw error
}

// Search Service
export const searchService = {
  /**
   * Perform natural language search with AI interpretation
   */
  async naturalLanguageSearch(
    query: string, 
    options: {
      projectId?: string
      filters?: Partial<SearchFilter>
    } = {}
  ): Promise<SearchResult> {
    try {
      const response = await apiClient.post('/api/search/natural-language', {
        query,
        project_id: options.projectId,
        filters: options.filters || {}
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Get search suggestions for autocomplete
   */
  async getSearchSuggestions(
    partialQuery: string, 
    limit: number = 10
  ): Promise<{ suggestions: SearchSuggestion[]; total_suggestions: number; query: string }> {
    try {
      const response = await apiClient.get('/api/search/suggestions', {
        params: { 
          query: partialQuery, 
          limit 
        }
      })
      return response.data
    } catch (error) {
      console.warn('Search suggestions failed:', error)
      return { suggestions: [], total_suggestions: 0, query: partialQuery }
    }
  },

  /**
   * Perform cross-project search
   */
  async crossProjectSearch(searchFilter: SearchFilter): Promise<SearchResult> {
    try {
      const response = await apiClient.post('/api/search/cross-project', searchFilter)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Perform semantic search using AI embeddings
   */
  async semanticSearch(
    query: string, 
    useAIEmbeddings: boolean = true
  ): Promise<SearchResult> {
    try {
      const response = await apiClient.post('/api/search/semantic', {
        query,
        use_ai_embeddings: useAIEmbeddings
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Perform advanced search with comprehensive filters
   */
  async advancedSearch(searchFilter: SearchFilter): Promise<SearchResult> {
    try {
      const response = await apiClient.post('/api/search/advanced', searchFilter)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Search with analytics tracking
   */
  async searchWithAnalytics(
    query: string, 
    userId: string, 
    options: any = {}
  ): Promise<SearchResult> {
    try {
      const response = await apiClient.post('/api/search/analytics', {
        query,
        user_id: userId,
        ...options
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  }
}

// Assembly Service
export const assemblyService = {
  /**
   * Create AI-automated presentation from user intent
   */
  async createAIAutomatedAssembly(
    intent: string, 
    projectId: string, 
    preferences?: any
  ): Promise<{
    success: boolean
    assembly_plan: AssemblyData
    recommendations: string[]
    estimated_duration: number
    optimization?: any
    error?: string
  }> {
    try {
      const response = await apiClient.post('/api/assembly/ai-automated', {
        intent,
        project_id: projectId,
        user_preferences: preferences || {}
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Create manual presentation assembly
   */
  async createManualAssembly(
    name: string, 
    slides: Array<{ slide_id: string; title?: string }>, 
    projectId: string,
    optimizeOrder: boolean = true
  ): Promise<{
    success: boolean
    assembly: AssemblyData
    optimization?: any
    transitions?: any[]
    error?: string
  }> {
    try {
      const response = await apiClient.post('/api/assembly/manual', {
        name,
        slides,
        project_id: projectId,
        optimize_order: optimizeOrder
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Optimize existing assembly with AI suggestions
   */
  async optimizeAssembly(
    assemblyId: string, 
    goals: string[]
  ): Promise<AssemblyOptimizationResult> {
    try {
      const response = await apiClient.post(`/api/assembly/${assemblyId}/optimize`, {
        optimization_goals: goals
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Generate smart slide transition suggestions
   */
  async suggestSmartTransitions(
    slides: Array<{ slide_id: string; title: string; slide_type: string }>
  ): Promise<{
    success: boolean
    transitions: any[]
    overall_flow: string
    timing_optimization: boolean
    error?: string
  }> {
    try {
      const response = await apiClient.post('/api/assembly/transitions', { slides })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Export assembly to various formats
   */
  async exportAssembly(
    assemblyId: string, 
    format: 'pptx' | 'pdf' | 'html', 
    options?: any
  ): Promise<ExportResult> {
    try {
      const response = await apiClient.post(`/api/assembly/${assemblyId}/export`, {
        format,
        options: options || {}
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Get available presentation templates
   */
  async getAvailableTemplates(): Promise<TemplateData[]> {
    try {
      const response = await apiClient.get('/api/assembly/templates')
      return response.data
    } catch (error) {
      console.warn('Failed to get templates:', error)
      return []
    }
  },

  /**
   * Apply template to assembly
   */
  async applyTemplate(
    assemblyId: string, 
    templateId: string
  ): Promise<{
    success: boolean
    template_applied: string
    template_name: string
    slides_updated: number
    layout_mappings: Record<string, string>
    color_scheme: string
    font_family: string
    error?: string
  }> {
    try {
      const response = await apiClient.post(`/api/assembly/${assemblyId}/template`, {
        template_id: templateId
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Get assemblies by project
   */
  async getAssembliesByProject(projectId: string): Promise<AssemblyData[]> {
    try {
      const response = await apiClient.get(`/api/assembly/project/${projectId}`)
      return response.data
    } catch (error) {
      console.warn('Failed to get assemblies:', error)
      return []
    }
  },

  /**
   * Delete assembly
   */
  async deleteAssembly(assemblyId: string): Promise<{ success: boolean; deleted_id: string; error?: string }> {
    try {
      const response = await apiClient.delete(`/api/assembly/${assemblyId}`)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Duplicate assembly
   */
  async duplicateAssembly(
    assemblyId: string, 
    newName: string
  ): Promise<{ success: boolean; new_assembly: AssemblyData; error?: string }> {
    try {
      const response = await apiClient.post(`/api/assembly/${assemblyId}/duplicate`, {
        new_name: newName
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Create collaboration session
   */
  async createCollaborationSession(
    assemblyId: string, 
    ownerId: string, 
    participants: string[]
  ): Promise<CollaborationSession> {
    try {
      const response = await apiClient.post('/api/assembly/collaboration/session', {
        assembly_id: assemblyId,
        owner_id: ownerId,
        participants
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Handle collaboration update
   */
  async handleCollaborationUpdate(
    sessionId: string, 
    userId: string, 
    action: string, 
    data: any
  ): Promise<CollaborationUpdate> {
    try {
      const response = await apiClient.post('/api/assembly/collaboration/update', {
        session_id: sessionId,
        user_id: userId,
        action,
        data
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  }
}

// Slide Service
export const slideService = {
  /**
   * Get detailed slide information
   */
  async getSlideDetails(slideId: string): Promise<SlideData> {
    try {
      const response = await apiClient.get(`/api/slides/${slideId}`)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Analyze slide content with AI
   */
  async analyzeSlideContent(slideId: string): Promise<AIAnalysisResult> {
    try {
      const response = await apiClient.post(`/api/slides/${slideId}/analyze`)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Suggest keywords for content
   */
  async suggestKeywords(
    content: string, 
    context: string = 'general'
  ): Promise<Array<{
    keyword: string
    confidence: number
    category: string
    exists: boolean
    usage_count: number
  }>> {
    try {
      const response = await apiClient.post('/api/ai/suggest-keywords', {
        content,
        context
      })
      return response.data
    } catch (error) {
      console.warn('Keyword suggestion failed:', error)
      return []
    }
  }
}

// Project Service
export const projectService = {
  /**
   * Get all projects
   */
  async getProjects(): Promise<ProjectData[]> {
    try {
      const response = await apiClient.get('/api/projects')
      return response.data
    } catch (error) {
      console.warn('Failed to get projects:', error)
      return []
    }
  },

  /**
   * Get project details
   */
  async getProjectDetails(projectId: string): Promise<ProjectData> {
    try {
      const response = await apiClient.get(`/api/projects/${projectId}`)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Create new project
   */
  async createProject(
    name: string, 
    description?: string
  ): Promise<{ success: boolean; project: ProjectData; error?: string }> {
    try {
      const response = await apiClient.post('/api/projects', {
        name,
        description
      })
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Update project
   */
  async updateProject(
    projectId: string, 
    updates: { name?: string; description?: string }
  ): Promise<{ success: boolean; project: ProjectData; error?: string }> {
    try {
      const response = await apiClient.put(`/api/projects/${projectId}`, updates)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Delete project
   */
  async deleteProject(projectId: string): Promise<{ success: boolean; deleted_id: string; error?: string }> {
    try {
      const response = await apiClient.delete(`/api/projects/${projectId}`)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  }
}

// AI Service
export const aiService = {
  /**
   * Provide contextual assistance
   */
  async getContextualAssistance(context: any): Promise<{
    suggestion: string
    action_type: string | null
    priority: string
    helpful_tips: string[]
  }> {
    try {
      const response = await apiClient.post('/api/ai/contextual-assistance', { context })
      return response.data
    } catch (error) {
      console.warn('Contextual assistance failed:', error)
      return {
        suggestion: '',
        action_type: null,
        priority: 'low',
        helpful_tips: []
      }
    }
  },

  /**
   * Check if AI service is available
   */
  async checkAvailability(): Promise<{ available: boolean; features: string[] }> {
    try {
      const response = await apiClient.get('/api/ai/status')
      return response.data
    } catch (error) {
      console.warn('AI availability check failed:', error)
      return { available: false, features: [] }
    }
  }
}

// File Upload Service
export const fileService = {
  /**
   * Upload PowerPoint file for processing
   */
  async uploadFile(
    file: File, 
    projectId: string,
    onProgress?: (progress: number) => void
  ): Promise<{
    success: boolean
    file_id: string
    processing_started: boolean
    estimated_completion: string
    error?: string
  }> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', projectId)

      const response = await apiClient.post('/api/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        }
      })

      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  },

  /**
   * Get file processing status
   */
  async getProcessingStatus(fileId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed'
    progress: number
    slides_processed: number
    total_slides: number
    error?: string
  }> {
    try {
      const response = await apiClient.get(`/api/files/${fileId}/status`)
      return response.data
    } catch (error) {
      return handleApiError(error)
    }
  }
}

// Export the main API client for custom requests
export { apiClient }

// Export utility functions
export const apiUtils = {
  generateRequestId,
  handleApiError,
  
  /**
   * Create a download URL for file exports
   */
  getDownloadUrl(filePath: string): string {
    return `${API_BASE_URL}/api/files/download?path=${encodeURIComponent(filePath)}`
  },
  
  /**
   * Create a thumbnail URL for slides
   */
  getThumbnailUrl(thumbnailPath: string): string {
    if (thumbnailPath.startsWith('http')) {
      return thumbnailPath
    }
    return `${API_BASE_URL}/api/slides/thumbnail?path=${encodeURIComponent(thumbnailPath)}`
  },
  
  /**
   * Create a full image URL for slides
   */
  getFullImageUrl(imagePath: string): string {
    if (imagePath.startsWith('http')) {
      return imagePath
    }
    return `${API_BASE_URL}/api/slides/image?path=${encodeURIComponent(imagePath)}`
  }
}

// Default export with all services
export default {
  search: searchService,
  assembly: assemblyService,
  slide: slideService,
  project: projectService,
  ai: aiService,
  file: fileService,
  utils: apiUtils,
  client: apiClient
}