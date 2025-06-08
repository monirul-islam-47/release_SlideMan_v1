/**
 * API Type Definitions for PrezI Frontend
 * Comprehensive TypeScript interfaces for all API interactions
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

export interface SlideData {
  id: string
  title: string
  content_preview: string
  slide_type: string
  project_id: string
  project_name: string
  keywords: string[]
  thumbnail_path?: string
  full_image_path?: string
  relevance_score: number
  ai_analysis?: {
    ai_topic: string
    ai_summary: string
    ai_confidence_score: number
    key_insights: string[]
    analyzed_at?: string
  }
  semantic_score?: number
  match_highlights?: string[]
  created_at?: string
  updated_at?: string
  notes?: string
  elements?: ElementData[]
}

export interface ElementData {
  id: string
  element_type: string
  content?: string
  position_x: number
  position_y: number
  width: number
  height: number
  ai_analysis?: any
}

export interface SearchResult {
  success: boolean
  query: string
  query_interpretation?: {
    search_intent: string
    topics: string[]
    keywords: string[]
    content_types: string[]
    confidence: number
    filters?: any
  }
  results: SlideData[]
  total_results: number
  search_time_ms?: number
  search_strategy: string
  error?: string
}

export interface SearchFilter {
  query: string
  content_types?: string[]
  keywords?: string[]
  projects?: string[]
  ai_confidence_min?: number
  ai_confidence_max?: number
  date_range?: {
    start: string
    end: string
  }
  sort_by: string
  sort_order: string
  limit: number
  offset: number
  include_ai_analysis: boolean
  search_scope: string
}

export interface SearchSuggestion {
  text: string
  type: 'topic' | 'keyword' | 'content_combination' | 'slide_title' | 'ai_suggestion'
  confidence: number
  result_count: number
}

export interface AssemblyData {
  id: string
  name: string
  description: string
  project_id: string
  slides: SlideAssembly[]
  ai_plan?: {
    intent: string
    target_audience: string
    estimated_duration: number
    success_metrics: string[]
    [key: string]: any
  }
  export_settings?: {
    format?: string
    template?: string
    include_notes?: boolean
    slide_numbering?: boolean
    [key: string]: any
  }
  template_id?: string
  collaboration_session?: string
  ai_generated: boolean
  created_at?: string
  updated_at?: string
  created_by?: string
}

export interface SlideAssembly {
  slide_id: string
  position: number
  title: string
  notes?: string
  transitions?: {
    type: string
    duration: number
    [key: string]: any
  }
  ai_suggested: boolean
  rationale?: string
  custom_layout?: string
  speaker_notes?: string
}

export interface TemplateData {
  id: string
  name: string
  description: string
  preview_url: string
  slide_layouts: string[]
  color_scheme: string
  font_family: string
}

export interface ProjectData {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  slide_count: number
  file_count: number
  keyword_count: number
  last_accessed?: string
}

export interface FileData {
  id: string
  name: string
  file_path: string
  project_id: string
  slide_count: number
  created_at: string
  processed: boolean
  processing_status?: string
}

export interface KeywordData {
  id: string
  name: string
  description?: string
  usage_count: number
  created_at: string
  is_ai_suggested?: boolean
  ai_confidence?: number
  semantic_group?: string
}

export interface AIAnalysisResult {
  success: boolean
  analysis?: {
    topic: string
    summary: string
    key_insights: string[]
    confidence_score: number
    slide_type: string
  }
  suggested_keywords?: Array<{
    keyword: string
    confidence: number
    category: string
  }>
  element_analysis?: Array<{
    element_type: string
    description: string
    data_insights: string[]
    importance: 'high' | 'medium' | 'low'
  }>
  error?: string
  fallback_analysis?: any
}

export interface AssemblyOptimizationResult {
  success: boolean
  optimization?: {
    optimized_order: Array<{
      slide_id: string
      position: number
      rationale?: string
    }>
    improvements: string[]
    flow_score: number
    rationale: string
  }
  missing_content?: Array<{
    content_type: string
    suggested_title: string
    rationale: string
    position: number
    priority: 'high' | 'medium' | 'low'
  }>
  enhancement_suggestions?: string[]
  assembly_updated?: boolean
  error?: string
}

export interface ExportResult {
  success: boolean
  file_path?: string
  format?: string
  slide_count?: number
  page_count?: number
  export_time_ms?: number
  file_size_mb?: number
  interactive?: boolean
  responsive?: boolean
  quality?: string
  error?: string
}

export interface CollaborationSession {
  session_id: string
  assembly_id: string
  owner_id: string
  participants: string[]
  permissions: Record<string, 'edit' | 'view'>
  version: number
  created_at: string
  last_activity: string
  status: 'active' | 'ended'
}

export interface CollaborationUpdate {
  success: boolean
  version?: number
  changes?: Array<{
    type: string
    user: string
    details: any
    timestamp?: string
  }>
  conflicts?: any[]
  sync_required?: boolean
  error?: string
}

export interface ApiError {
  message: string
  code?: string
  status?: number
  details?: any
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

// API Response wrappers
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: ApiError
  meta?: {
    timestamp: string
    request_id?: string
    version?: string
  }
}

// Query parameters for various endpoints
export interface SearchParams {
  query: string
  project_id?: string
  search_type?: 'natural' | 'semantic' | 'advanced'
  cross_project?: boolean
  filters?: Partial<SearchFilter>
}

export interface AssemblyParams {
  intent?: string
  project_id: string
  user_preferences?: {
    duration?: number
    style?: string
    include_notes?: boolean
    [key: string]: any
  }
}

export interface ExportParams {
  format: 'pptx' | 'pdf' | 'html'
  options?: {
    template?: string
    include_notes?: boolean
    slide_numbering?: boolean
    quality?: 'low' | 'standard' | 'high'
    interactive?: boolean
    responsive?: boolean
    [key: string]: any
  }
}

// User interface state types
export interface UIState {
  loading: boolean
  error?: string | null
  success?: string | null
}

export interface SearchUIState extends UIState {
  query: string
  filters: Partial<SearchFilter>
  suggestions: SearchSuggestion[]
  showFilters: boolean
  searchType: 'natural' | 'semantic' | 'advanced'
  crossProject: boolean
}

export interface AssemblyUIState extends UIState {
  currentAssembly?: AssemblyData | null
  showTemplates: boolean
  showExportDialog: boolean
  showPreview: boolean
  exportFormat: 'pptx' | 'pdf' | 'html'
  optimizing: boolean
}

// Event handlers and callbacks
export type SlideSelectHandler = (slideId: string) => void
export type AssemblyUpdateHandler = (assembly: AssemblyData) => void
export type SearchHandler = (query: string, filters?: Partial<SearchFilter>) => void
export type ExportHandler = (assemblyId: string, format: string, options?: any) => void

// Component prop types
export interface BaseComponentProps {
  className?: string
  style?: React.CSSProperties
  'data-testid'?: string
}

export interface SlideViewerProps extends BaseComponentProps {
  slide: SlideData
  onSlideSelect?: SlideSelectHandler
  onAddToAssembly?: (slideId: string) => void
  showAIAnalysis?: boolean
  compact?: boolean
}

export interface SearchComponentProps extends BaseComponentProps {
  onSlideSelect?: SlideSelectHandler
  onAddToAssembly?: (slideId: string) => void
  projectId?: string
  defaultQuery?: string
  autoFocus?: boolean
}

export interface AssemblyBuilderProps extends BaseComponentProps {
  assembly: AssemblyData
  onAssemblyUpdate?: AssemblyUpdateHandler
  readonly?: boolean
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// API endpoint types
export type Endpoint = 
  | '/api/search/natural-language'
  | '/api/search/semantic'
  | '/api/search/advanced'
  | '/api/search/cross-project'
  | '/api/search/suggestions'
  | '/api/assembly/ai-automated'
  | '/api/assembly/manual'
  | '/api/assembly/{id}/optimize'
  | '/api/assembly/{id}/export'
  | '/api/assembly/templates'
  | '/api/slides/{id}'
  | '/api/slides/{id}/analyze'
  | '/api/projects'
  | '/api/projects/{id}'