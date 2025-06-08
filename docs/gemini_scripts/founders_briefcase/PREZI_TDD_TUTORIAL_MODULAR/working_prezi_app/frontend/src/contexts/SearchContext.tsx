/**
 * SearchContext for PrezI Frontend
 * Comprehensive search state management with history and preferences
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { SearchFilter, SearchSuggestion } from '../types/api'

interface SavedSearch {
  id: string
  name: string
  query: string
  filters: Partial<SearchFilter>
  searchType: 'natural' | 'semantic' | 'advanced'
  crossProject: boolean
  created_at: string
  last_used?: string
  use_count: number
}

interface SearchPreferences {
  defaultSearchType: 'natural' | 'semantic' | 'advanced'
  defaultCrossProject: boolean
  autoSuggestions: boolean
  saveHistory: boolean
  maxHistoryItems: number
  maxSuggestions: number
}

interface SearchContextType {
  // Search state
  query: string
  setQuery: (query: string) => void
  
  // Search history
  searchHistory: string[]
  addToHistory: (query: string) => void
  removeFromHistory: (query: string) => void
  clearHistory: () => void
  
  // Search suggestions
  suggestions: SearchSuggestion[]
  setSuggestions: (suggestions: SearchSuggestion[]) => void
  clearSuggestions: () => void
  
  // Saved searches
  savedSearches: SavedSearch[]
  saveSearch: (search: Omit<SavedSearch, 'id' | 'use_count'>) => void
  deleteSavedSearch: (id: string) => void
  updateSavedSearch: (id: string, updates: Partial<SavedSearch>) => void
  useSavedSearch: (id: string) => SavedSearch | null
  
  // Search filters
  filters: Partial<SearchFilter>
  setFilters: (filters: Partial<SearchFilter>) => void
  resetFilters: () => void
  
  // Search preferences
  preferences: SearchPreferences
  updatePreferences: (updates: Partial<SearchPreferences>) => void
  
  // Search analytics
  searchStats: {
    totalSearches: number
    avgSearchTime: number
    mostUsedTerms: string[]
    recentActivity: Array<{
      query: string
      timestamp: string
      results: number
    }>
  }
  recordSearch: (query: string, results: number, searchTime: number) => void
  
  // UI state
  showFilters: boolean
  setShowFilters: (show: boolean) => void
  searchType: 'natural' | 'semantic' | 'advanced'
  setSearchType: (type: 'natural' | 'semantic' | 'advanced') => void
  crossProject: boolean
  setCrossProject: (cross: boolean) => void
}

const SearchContext = createContext<SearchContextType | undefined>(undefined)

// Default values
const DEFAULT_PREFERENCES: SearchPreferences = {
  defaultSearchType: 'natural',
  defaultCrossProject: false,
  autoSuggestions: true,
  saveHistory: true,
  maxHistoryItems: 50,
  maxSuggestions: 10
}

const DEFAULT_FILTERS: Partial<SearchFilter> = {
  content_types: [],
  keywords: [],
  ai_confidence_min: 0,
  ai_confidence_max: 1,
  date_range: { start: '', end: '' },
  sort_by: 'relevance',
  sort_order: 'desc',
  limit: 50,
  offset: 0,
  include_ai_analysis: true,
  search_scope: 'current_project'
}

// Storage keys
const STORAGE_KEYS = {
  SEARCH_HISTORY: 'prezi_search_history',
  SAVED_SEARCHES: 'prezi_saved_searches',
  SEARCH_PREFERENCES: 'prezi_search_preferences',
  SEARCH_FILTERS: 'prezi_search_filters',
  SEARCH_STATS: 'prezi_search_stats'
}

export const SearchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Core search state
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [showFilters, setShowFilters] = useState(false)
  
  // Search history
  const [searchHistory, setSearchHistory] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SEARCH_HISTORY)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  
  // Saved searches
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SAVED_SEARCHES)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  
  // Search preferences
  const [preferences, setPreferences] = useState<SearchPreferences>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SEARCH_PREFERENCES)
      return saved ? { ...DEFAULT_PREFERENCES, ...JSON.parse(saved) } : DEFAULT_PREFERENCES
    } catch {
      return DEFAULT_PREFERENCES
    }
  })
  
  // Search filters
  const [filters, setFiltersState] = useState<Partial<SearchFilter>>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SEARCH_FILTERS)
      return saved ? { ...DEFAULT_FILTERS, ...JSON.parse(saved) } : DEFAULT_FILTERS
    } catch {
      return DEFAULT_FILTERS
    }
  })
  
  // UI state derived from preferences
  const [searchType, setSearchType] = useState<'natural' | 'semantic' | 'advanced'>(
    preferences.defaultSearchType
  )
  const [crossProject, setCrossProject] = useState(preferences.defaultCrossProject)
  
  // Search analytics
  const [searchStats, setSearchStats] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SEARCH_STATS)
      return saved ? JSON.parse(saved) : {
        totalSearches: 0,
        avgSearchTime: 0,
        mostUsedTerms: [],
        recentActivity: []
      }
    } catch {
      return {
        totalSearches: 0,
        avgSearchTime: 0,
        mostUsedTerms: [],
        recentActivity: []
      }
    }
  })

  // Persist search history to localStorage
  useEffect(() => {
    if (preferences.saveHistory) {
      localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(searchHistory))
    }
  }, [searchHistory, preferences.saveHistory])

  // Persist saved searches to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(savedSearches))
  }, [savedSearches])

  // Persist preferences to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SEARCH_PREFERENCES, JSON.stringify(preferences))
  }, [preferences])

  // Persist filters to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SEARCH_FILTERS, JSON.stringify(filters))
  }, [filters])

  // Persist search stats to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SEARCH_STATS, JSON.stringify(searchStats))
  }, [searchStats])

  // Search history management
  const addToHistory = useCallback((searchQuery: string) => {
    if (!preferences.saveHistory || !searchQuery.trim()) return
    
    setSearchHistory(prev => {
      const trimmedQuery = searchQuery.trim()
      const newHistory = [
        trimmedQuery,
        ...prev.filter(q => q !== trimmedQuery)
      ].slice(0, preferences.maxHistoryItems)
      
      return newHistory
    })
  }, [preferences.saveHistory, preferences.maxHistoryItems])

  const removeFromHistory = useCallback((searchQuery: string) => {
    setSearchHistory(prev => prev.filter(q => q !== searchQuery))
  }, [])

  const clearHistory = useCallback(() => {
    setSearchHistory([])
    localStorage.removeItem(STORAGE_KEYS.SEARCH_HISTORY)
  }, [])

  // Suggestions management
  const clearSuggestions = useCallback(() => {
    setSuggestions([])
  }, [])

  // Saved searches management
  const saveSearch = useCallback((search: Omit<SavedSearch, 'id' | 'use_count'>) => {
    const newSavedSearch: SavedSearch = {
      ...search,
      id: `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      use_count: 0
    }
    
    setSavedSearches(prev => {
      // Check for duplicates based on query and filters
      const exists = prev.some(s => 
        s.query === search.query && 
        JSON.stringify(s.filters) === JSON.stringify(search.filters)
      )
      
      if (exists) {
        return prev
      }
      
      return [newSavedSearch, ...prev].slice(0, 20) // Keep max 20 saved searches
    })
  }, [])

  const deleteSavedSearch = useCallback((id: string) => {
    setSavedSearches(prev => prev.filter(s => s.id !== id))
  }, [])

  const updateSavedSearch = useCallback((id: string, updates: Partial<SavedSearch>) => {
    setSavedSearches(prev => prev.map(s => 
      s.id === id ? { ...s, ...updates } : s
    ))
  }, [])

  const useSavedSearch = useCallback((id: string) => {
    const search = savedSearches.find(s => s.id === id)
    if (search) {
      // Update usage count and last used
      updateSavedSearch(id, { 
        use_count: search.use_count + 1, 
        last_used: new Date().toISOString() 
      })
      return search
    }
    return null
  }, [savedSearches, updateSavedSearch])

  // Filters management
  const setFilters = useCallback((newFilters: Partial<SearchFilter>) => {
    setFiltersState(prev => ({ ...prev, ...newFilters }))
  }, [])

  const resetFilters = useCallback(() => {
    setFiltersState(DEFAULT_FILTERS)
  }, [])

  // Preferences management
  const updatePreferences = useCallback((updates: Partial<SearchPreferences>) => {
    setPreferences(prev => ({ ...prev, ...updates }))
  }, [])

  // Search analytics
  const recordSearch = useCallback((searchQuery: string, results: number, searchTime: number) => {
    setSearchStats(prev => {
      const newActivity = {
        query: searchQuery,
        timestamp: new Date().toISOString(),
        results
      }
      
      // Update most used terms
      const terms = searchQuery.toLowerCase().split(' ').filter(term => term.length > 2)
      const termCounts = [...prev.mostUsedTerms]
      
      terms.forEach(term => {
        const existingIndex = termCounts.findIndex(t => t.startsWith(term + ':'))
        if (existingIndex >= 0) {
          const count = parseInt(termCounts[existingIndex].split(':')[1]) + 1
          termCounts[existingIndex] = `${term}:${count}`
        } else {
          termCounts.push(`${term}:1`)
        }
      })
      
      // Sort and keep top 20 terms
      const sortedTerms = termCounts
        .sort((a, b) => parseInt(b.split(':')[1]) - parseInt(a.split(':')[1]))
        .slice(0, 20)
      
      // Calculate new average search time
      const totalSearches = prev.totalSearches + 1
      const newAvgSearchTime = ((prev.avgSearchTime * prev.totalSearches) + searchTime) / totalSearches
      
      return {
        totalSearches,
        avgSearchTime: newAvgSearchTime,
        mostUsedTerms: sortedTerms,
        recentActivity: [newActivity, ...prev.recentActivity].slice(0, 50)
      }
    })
  }, [])

  // Context value
  const value: SearchContextType = {
    // Search state
    query,
    setQuery,
    
    // Search history
    searchHistory,
    addToHistory,
    removeFromHistory,
    clearHistory,
    
    // Search suggestions
    suggestions,
    setSuggestions,
    clearSuggestions,
    
    // Saved searches
    savedSearches,
    saveSearch,
    deleteSavedSearch,
    updateSavedSearch,
    useSavedSearch,
    
    // Search filters
    filters,
    setFilters,
    resetFilters,
    
    // Search preferences
    preferences,
    updatePreferences,
    
    // Search analytics
    searchStats,
    recordSearch,
    
    // UI state
    showFilters,
    setShowFilters,
    searchType,
    setSearchType,
    crossProject,
    setCrossProject
  }

  return (
    <SearchContext.Provider value={value}>
      {children}
    </SearchContext.Provider>
  )
}

export const useSearchContext = () => {
  const context = useContext(SearchContext)
  if (context === undefined) {
    throw new Error('useSearchContext must be used within a SearchProvider')
  }
  return context
}

// Custom hooks for specific search functionality
export const useSearchHistory = () => {
  const { searchHistory, addToHistory, removeFromHistory, clearHistory } = useSearchContext()
  return { searchHistory, addToHistory, removeFromHistory, clearHistory }
}

export const useSearchSuggestions = () => {
  const { suggestions, setSuggestions, clearSuggestions, preferences } = useSearchContext()
  
  const canShowSuggestions = preferences.autoSuggestions
  const maxSuggestions = preferences.maxSuggestions
  
  return { 
    suggestions: canShowSuggestions ? suggestions.slice(0, maxSuggestions) : [],
    setSuggestions,
    clearSuggestions,
    canShowSuggestions,
    maxSuggestions
  }
}

export const useSavedSearches = () => {
  const { 
    savedSearches, 
    saveSearch, 
    deleteSavedSearch, 
    updateSavedSearch, 
    useSavedSearch 
  } = useSearchContext()
  
  // Sort saved searches by usage and recency
  const sortedSavedSearches = savedSearches.sort((a, b) => {
    // Prioritize by usage count, then by last used, then by created date
    if (a.use_count !== b.use_count) {
      return b.use_count - a.use_count
    }
    
    if (a.last_used && b.last_used) {
      return new Date(b.last_used).getTime() - new Date(a.last_used).getTime()
    }
    
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
  
  return {
    savedSearches: sortedSavedSearches,
    saveSearch,
    deleteSavedSearch,
    updateSavedSearch,
    useSavedSearch
  }
}

export const useSearchAnalytics = () => {
  const { searchStats, recordSearch } = useSearchContext()
  
  // Parse most used terms for display
  const mostUsedTerms = searchStats.mostUsedTerms.map(termCount => {
    const [term, count] = termCount.split(':')
    return { term, count: parseInt(count) }
  })
  
  return {
    ...searchStats,
    mostUsedTerms,
    recordSearch
  }
}