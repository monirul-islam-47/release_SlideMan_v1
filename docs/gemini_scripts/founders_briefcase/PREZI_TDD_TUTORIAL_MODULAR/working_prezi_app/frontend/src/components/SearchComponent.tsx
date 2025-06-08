/**
 * SearchComponent for PrezI Frontend
 * Comprehensive search interface with AI-powered natural language processing
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { debounce } from 'lodash'
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Typography,
  List,
  ListItem,
  Card,
  CardContent,
  Collapse,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Button,
  Paper,
  Grid,
  Tooltip,
  CircularProgress,
  Alert,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Psychology as AIIcon,
  AutoAwesome as SuggestIcon,
  History as HistoryIcon,
  Tune as TuneIcon,
  BookmarkBorder as SaveIcon,
  Share as ShareIcon
} from '@mui/icons-material'
import { searchService } from '../services/api'
import { SearchResult, SlideData, SearchFilter, SearchSuggestion } from '../types/api'
import { SlideViewer } from './SlideViewer'
import { useSearchContext } from '../contexts/SearchContext'

interface SearchComponentProps {
  onSlideSelect?: (slideId: string) => void
  onAddToAssembly?: (slideId: string) => void
  projectId?: string
  defaultQuery?: string
  autoFocus?: boolean
  className?: string
  'data-testid'?: string
}

export const SearchComponent: React.FC<SearchComponentProps> = ({
  onSlideSelect,
  onAddToAssembly,
  projectId,
  defaultQuery = '',
  autoFocus = false,
  className,
  'data-testid': dataTestId
}) => {
  // State management
  const [query, setQuery] = useState(defaultQuery)
  const [showFilters, setShowFilters] = useState(false)
  const [crossProject, setCrossProject] = useState(false)
  const [searchType, setSearchType] = useState<'natural' | 'semantic' | 'advanced'>('natural')
  const [showSavedSearches, setShowSavedSearches] = useState(false)
  
  // Advanced filters state
  const [filters, setFilters] = useState<Partial<SearchFilter>>({
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
  })

  // Context and custom hooks
  const { 
    searchHistory, 
    addToHistory, 
    suggestions, 
    setSuggestions,
    savedSearches,
    saveSearch
  } = useSearchContext()

  // Debounced suggestions fetch
  const debouncedGetSuggestions = useCallback(
    debounce(async (partialQuery: string) => {
      if (partialQuery.length >= 2) {
        try {
          const suggestionsResult = await searchService.getSearchSuggestions(partialQuery)
          setSuggestions(suggestionsResult.suggestions || [])
        } catch (error) {
          console.error('Failed to get suggestions:', error)
          setSuggestions([])
        }
      } else {
        setSuggestions([])
      }
    }, 300),
    [setSuggestions]
  )

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: async (searchQuery: string) => {
      const searchOptions = {
        projectId: crossProject ? undefined : projectId,
        filters: {
          ...filters,
          search_scope: crossProject ? 'all_projects' : 'current_project'
        }
      }

      switch (searchType) {
        case 'semantic':
          return await searchService.semanticSearch(searchQuery, true)
        case 'advanced':
          return await searchService.advancedSearch({
            query: searchQuery,
            ...filters,
            projects: crossProject ? undefined : projectId ? [projectId] : undefined
          } as SearchFilter)
        default:
          return await searchService.naturalLanguageSearch(searchQuery, searchOptions)
      }
    },
    onSuccess: (data: SearchResult) => {
      if (data.success) {
        addToHistory(query)
      }
    },
    onError: (error) => {
      console.error('Search failed:', error)
    }
  })

  // Auto-focus effect
  useEffect(() => {
    if (autoFocus) {
      const searchInput = document.querySelector('input[placeholder*="search"]') as HTMLInputElement
      if (searchInput) {
        searchInput.focus()
      }
    }
  }, [autoFocus])

  // Handle input change with suggestions
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = event.target.value
    setQuery(newQuery)
    debouncedGetSuggestions(newQuery)
  }

  // Handle search submission
  const handleSearch = useCallback(() => {
    if (query.trim()) {
      searchMutation.mutate(query.trim())
    }
  }, [query, searchMutation])

  // Handle Enter key press
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch()
    }
  }

  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.text)
    setSuggestions([])
    searchMutation.mutate(suggestion.text)
  }

  // Handle filter changes
  const handleFilterChange = (filterKey: keyof SearchFilter, value: any) => {
    setFilters(prev => ({ ...prev, [filterKey]: value }))
  }

  // Handle clear filters
  const handleClearFilters = () => {
    setFilters({
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
      search_scope: crossProject ? 'all_projects' : 'current_project'
    })
  }

  // Handle save search
  const handleSaveSearch = () => {
    if (query.trim()) {
      saveSearch({
        query: query.trim(),
        filters,
        searchType,
        crossProject,
        name: `Search: ${query.trim().substring(0, 30)}...`,
        created_at: new Date().toISOString()
      })
    }
  }

  // Search results
  const searchResults = searchMutation.data
  const isLoading = searchMutation.isPending
  const hasError = searchMutation.isError

  // Memoized content type options
  const contentTypeOptions = useMemo(() => [
    { value: 'chart', label: 'Charts', icon: '📊' },
    { value: 'image', label: 'Images', icon: '🖼️' },
    { value: 'table', label: 'Tables', icon: '📋' },
    { value: 'text', label: 'Text', icon: '📝' },
    { value: 'title', label: 'Title Slides', icon: '🎯' },
    { value: 'conclusion', label: 'Conclusions', icon: '🏁' }
  ], [])

  return (
    <Box 
      className={className}
      data-testid={dataTestId}
      sx={{ width: '100%', maxWidth: 1200, mx: 'auto', p: 2 }}
    >
      {/* Search Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        {/* Main Search Input */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            placeholder="Search presentations, slides, and content..."
            value={query}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            autoFocus={autoFocus}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="primary" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {isLoading && <CircularProgress size={20} />}
                    {query && (
                      <Tooltip title="Clear search">
                        <IconButton 
                          onClick={() => setQuery('')} 
                          size="small"
                          disabled={isLoading}
                        >
                          <ClearIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {query && !isLoading && (
                      <Tooltip title="Save search">
                        <IconButton onClick={handleSaveSearch} size="small">
                          <SaveIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </InputAdornment>
              )
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                fontSize: '1.1rem'
              }
            }}
          />
          
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={!query.trim() || isLoading}
            startIcon={<SearchIcon />}
            size="large"
            sx={{ 
              minWidth: 120,
              borderRadius: 2,
              py: 1.5
            }}
          >
            Search
          </Button>
        </Box>

        {/* Search Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Search Type</InputLabel>
            <Select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as any)}
              label="Search Type"
            >
              <MenuItem value="natural">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AIIcon fontSize="small" color="primary" />
                  Natural Language
                </Box>
              </MenuItem>
              <MenuItem value="semantic">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SuggestIcon fontSize="small" color="secondary" />
                  Semantic
                </Box>
              </MenuItem>
              <MenuItem value="advanced">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TuneIcon fontSize="small" />
                  Advanced
                </Box>
              </MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={crossProject}
                onChange={(e) => setCrossProject(e.target.checked)}
                color="primary"
              />
            }
            label="Search All Projects"
          />

          <Button
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
            variant={showFilters ? 'contained' : 'outlined'}
            size="small"
          >
            Filters
          </Button>

          <Button
            startIcon={<HistoryIcon />}
            onClick={() => setShowSavedSearches(true)}
            variant="outlined"
            size="small"
          >
            Saved
          </Button>
        </Box>

        {/* Advanced Filters */}
        <Collapse in={showFilters}>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Advanced Filters
            </Typography>
            
            <Grid container spacing={2}>
              {/* Content Types */}
              <Grid item xs={12} sm={6} md={4}>
                <FormControl fullWidth size="small">
                  <Autocomplete
                    multiple
                    options={contentTypeOptions}
                    getOptionLabel={(option) => option.label}
                    value={contentTypeOptions.filter(opt => 
                      filters.content_types?.includes(opt.value)
                    )}
                    onChange={(_, value) => 
                      handleFilterChange('content_types', value.map(v => v.value))
                    }
                    renderInput={(params) => (
                      <TextField {...params} label="Content Types" />
                    )}
                    renderOption={(props, option) => (
                      <li {...props}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <span>{option.icon}</span>
                          {option.label}
                        </Box>
                      </li>
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => (
                        <Chip
                          {...getTagProps({ index })}
                          key={option.value}
                          label={`${option.icon} ${option.label}`}
                          size="small"
                        />
                      ))
                    }
                  />
                </FormControl>
              </Grid>

              {/* AI Confidence Range */}
              <Grid item xs={12} sm={6} md={4}>
                <Typography gutterBottom sx={{ fontSize: '0.875rem' }}>
                  AI Confidence Range
                </Typography>
                <Slider
                  value={[filters.ai_confidence_min || 0, filters.ai_confidence_max || 1]}
                  onChange={(_, value) => {
                    const [min, max] = value as number[]
                    handleFilterChange('ai_confidence_min', min)
                    handleFilterChange('ai_confidence_max', max)
                  }}
                  min={0}
                  max={1}
                  step={0.1}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 0.5, label: '50%' },
                    { value: 1, label: '100%' }
                  ]}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
                />
              </Grid>

              {/* Sort Options */}
              <Grid item xs={12} sm={6} md={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Sort By</InputLabel>
                  <Select
                    value={filters.sort_by || 'relevance'}
                    onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                    label="Sort By"
                  >
                    <MenuItem value="relevance">Relevance</MenuItem>
                    <MenuItem value="date">Date</MenuItem>
                    <MenuItem value="title">Title</MenuItem>
                    <MenuItem value="ai_confidence">AI Confidence</MenuItem>
                    <MenuItem value="project">Project</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Clear Filters */}
              <Grid item xs={12} sm={6} md={2}>
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center' }}>
                  <Button
                    onClick={handleClearFilters}
                    size="small"
                    variant="outlined"
                    fullWidth
                  >
                    Clear Filters
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Collapse>
      </Paper>

      {/* Search Suggestions */}
      {suggestions.length > 0 && query.length >= 2 && !searchResults && (
        <Paper elevation={1} sx={{ mb: 2, maxHeight: 200, overflow: 'auto' }}>
          <List dense>
            {suggestions.map((suggestion, index) => (
              <ListItem
                key={index}
                button
                onClick={() => handleSuggestionSelect(suggestion)}
                sx={{ borderBottom: '1px solid', borderColor: 'divider' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  <SuggestIcon fontSize="small" color="primary" />
                  <Typography variant="body2" sx={{ flexGrow: 1 }}>
                    {suggestion.text}
                  </Typography>
                  <Chip 
                    label={suggestion.type} 
                    size="small" 
                    variant="outlined"
                    color="primary"
                  />
                  <Typography variant="caption" color="text.secondary">
                    {Math.round(suggestion.confidence * 100)}%
                  </Typography>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Error Display */}
      {hasError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Search failed. Please try again or adjust your search terms.
        </Alert>
      )}

      {/* Search Results */}
      {searchResults && (
        <Paper elevation={1} sx={{ p: 2 }}>
          {/* Results Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              {searchResults.success ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {searchResults.search_strategy === 'ai_natural_language' && (
                    <Chip 
                      icon={<AIIcon />} 
                      label="AI Powered" 
                      color="primary" 
                      size="small"
                    />
                  )}
                  Found {searchResults.total_results} result{searchResults.total_results !== 1 ? 's' : ''}
                </Box>
              ) : (
                'Search failed'
              )}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {searchResults.search_time_ms && (
                <Typography variant="caption" color="text.secondary">
                  {searchResults.search_time_ms}ms
                </Typography>
              )}
              
              {searchResults.success && searchResults.results.length > 0 && (
                <Button
                  startIcon={<ShareIcon />}
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    const url = new URL(window.location.href)
                    url.searchParams.set('q', query)
                    navigator.clipboard.writeText(url.toString())
                  }}
                >
                  Share Results
                </Button>
              )}
            </Box>
          </Box>

          {/* AI Query Interpretation */}
          {searchResults.query_interpretation && (
            <Card sx={{ mb: 2, bgcolor: 'primary.50', borderLeft: 4, borderColor: 'primary.main' }}>
              <CardContent sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AIIcon fontSize="small" />
                  AI Understanding:
                </Typography>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  {searchResults.query_interpretation.topics?.length > 0 && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Topics:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {searchResults.query_interpretation.topics.map((topic, index) => (
                          <Chip 
                            key={index} 
                            label={topic} 
                            size="small" 
                            color="primary"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {searchResults.query_interpretation.keywords?.length > 0 && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Keywords:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {searchResults.query_interpretation.keywords.map((keyword, index) => (
                          <Chip 
                            key={index} 
                            label={keyword} 
                            size="small" 
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {searchResults.query_interpretation.content_types?.length > 0 && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Content Types:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {searchResults.query_interpretation.content_types.map((type, index) => (
                          <Chip 
                            key={index} 
                            label={type} 
                            size="small" 
                            color="secondary"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Results List */}
          {searchResults.success && searchResults.results.length > 0 ? (
            <Grid container spacing={2}>
              {searchResults.results.map((slide) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={slide.id}>
                  <SlideViewer
                    slide={slide}
                    onSlideSelect={onSlideSelect}
                    onAddToAssembly={onAddToAssembly}
                    showAIAnalysis={searchType === 'natural'}
                    compact={true}
                    data-testid={`search-result-${slide.id}`}
                  />
                </Grid>
              ))}
            </Grid>
          ) : searchResults.success ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No slides found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Try different keywords, adjust your filters, or search across all projects.
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  onClick={() => setCrossProject(true)}
                  disabled={crossProject}
                >
                  Search All Projects
                </Button>
                <Button
                  variant="outlined"
                  onClick={handleClearFilters}
                >
                  Clear Filters
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setSearchType('semantic')}
                  disabled={searchType === 'semantic'}
                >
                  Try Semantic Search
                </Button>
              </Box>
            </Box>
          ) : (
            <Alert severity="error" sx={{ textAlign: 'center' }}>
              Search failed. Please check your connection and try again.
            </Alert>
          )}
        </Paper>
      )}

      {/* Recent Searches */}
      {!searchResults && searchHistory.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon fontSize="small" />
            Recent Searches
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {searchHistory.slice(0, 10).map((historyQuery, index) => (
              <Chip
                key={index}
                label={historyQuery}
                onClick={() => {
                  setQuery(historyQuery)
                  searchMutation.mutate(historyQuery)
                }}
                variant="outlined"
                size="small"
                clickable
                sx={{ '&:hover': { bgcolor: 'primary.50' } }}
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Saved Searches Dialog */}
      <Dialog 
        open={showSavedSearches} 
        onClose={() => setShowSavedSearches(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Saved Searches</DialogTitle>
        <DialogContent>
          {savedSearches.length > 0 ? (
            <List>
              {savedSearches.map((savedSearch, index) => (
                <ListItem
                  key={index}
                  button
                  onClick={() => {
                    setQuery(savedSearch.query)
                    setFilters(savedSearch.filters)
                    setSearchType(savedSearch.searchType)
                    setCrossProject(savedSearch.crossProject)
                    setShowSavedSearches(false)
                    searchMutation.mutate(savedSearch.query)
                  }}
                >
                  <Box sx={{ width: '100%' }}>
                    <Typography variant="subtitle2">
                      {savedSearch.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {savedSearch.query}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(savedSearch.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
              No saved searches yet.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSavedSearches(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}