/**
 * SlideViewer Component for PrezI Frontend
 * Comprehensive slide display component with AI analysis and interactive features
 * Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  CardContent,
  CardMedia,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogContent,
  LinearProgress,
  Collapse,
  Rating,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Skeleton
} from '@mui/material'
import {
  Fullscreen as FullscreenIcon,
  Add as AddIcon,
  Psychology as AIIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Close as CloseIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  MoreVert as MoreIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  Visibility as ViewIcon,
  Info as InfoIcon
} from '@mui/icons-material'
import { SlideData } from '../types/api'
import { apiUtils } from '../services/api'

interface SlideViewerProps {
  slide: SlideData
  onSlideSelect?: (slideId: string) => void
  onAddToAssembly?: (slideId: string) => void
  onBookmark?: (slideId: string, bookmarked: boolean) => void
  showAIAnalysis?: boolean
  compact?: boolean
  interactive?: boolean
  bookmarked?: boolean
  className?: string
  'data-testid'?: string
}

export const SlideViewer: React.FC<SlideViewerProps> = ({
  slide,
  onSlideSelect,
  onAddToAssembly,
  onBookmark,
  showAIAnalysis = false,
  compact = false,
  interactive = true,
  bookmarked = false,
  className,
  'data-testid': dataTestId
}) => {
  // State management
  const [fullscreen, setFullscreen] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  // Event handlers
  const handleSlideClick = useCallback(() => {
    if (onSlideSelect && interactive) {
      onSlideSelect(slide.id)
    }
  }, [onSlideSelect, slide.id, interactive])

  const handleAddToAssembly = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    if (onAddToAssembly) {
      onAddToAssembly(slide.id)
    }
  }, [onAddToAssembly, slide.id])

  const handleBookmark = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    if (onBookmark) {
      onBookmark(slide.id, !bookmarked)
    }
  }, [onBookmark, slide.id, bookmarked])

  const handleFullscreen = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setFullscreen(true)
  }, [])

  const handleMenuOpen = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    setAnchorEl(e.currentTarget)
  }, [])

  const handleMenuClose = useCallback(() => {
    setAnchorEl(null)
  }, [])

  const handleShare = useCallback(() => {
    const url = `${window.location.origin}/slides/${slide.id}`
    navigator.clipboard.writeText(url)
    handleMenuClose()
  }, [slide.id])

  const handleDownload = useCallback(() => {
    if (slide.full_image_path) {
      const link = document.createElement('a')
      link.href = apiUtils.getFullImageUrl(slide.full_image_path)
      link.download = `${slide.title}.png`
      link.click()
    }
    handleMenuClose()
  }, [slide.full_image_path, slide.title])

  // Utility functions
  const getSlideTypeColor = (type: string) => {
    const typeColors: Record<string, 'primary' | 'secondary' | 'info' | 'warning' | 'error' | 'success'> = {
      chart: 'primary',
      image: 'secondary',
      table: 'info',
      text: 'default' as any,
      title: 'warning',
      conclusion: 'success'
    }
    return typeColors[type.toLowerCase()] || 'default'
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success'
    if (score >= 0.6) return 'warning'
    return 'error'
  }

  const formatRelevanceScore = (score: number) => {
    return Math.round(score * 100)
  }

  // Image URL handling
  const thumbnailUrl = slide.thumbnail_path 
    ? apiUtils.getThumbnailUrl(slide.thumbnail_path)
    : '/placeholder-slide.png'

  const fullImageUrl = slide.full_image_path
    ? apiUtils.getFullImageUrl(slide.full_image_path)
    : thumbnailUrl

  return (
    <>
      <Card
        className={className}
        data-testid={dataTestId || `slide-viewer-${slide.id}`}
        sx={{
          height: compact ? 280 : 360,
          display: 'flex',
          flexDirection: 'column',
          cursor: interactive ? 'pointer' : 'default',
          transition: 'transform 0.2s, box-shadow 0.2s',
          position: 'relative',
          '&:hover': interactive ? {
            transform: 'translateY(-2px)',
            boxShadow: 4,
            '& .slide-overlay': {
              opacity: 1
            }
          } : {}
        }}
        onClick={handleSlideClick}
      >
        {/* Slide Thumbnail Container */}
        <Box sx={{ position: 'relative', height: compact ? 140 : 180, bgcolor: 'grey.100' }}>
          {/* Loading skeleton */}
          {!imageLoaded && !imageError && (
            <Skeleton 
              variant="rectangular" 
              width="100%" 
              height="100%" 
              animation="wave"
            />
          )}

          {/* Slide Image */}
          <CardMedia
            component="img"
            image={thumbnailUrl}
            alt={slide.title}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            sx={{
              height: '100%',
              objectFit: 'cover',
              display: imageLoaded && !imageError ? 'block' : 'none'
            }}
          />

          {/* Error state */}
          {imageError && (
            <Box
              sx={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: 'grey.200',
                color: 'text.secondary'
              }}
            >
              <Typography variant="body2">Image not available</Typography>
            </Box>
          )}
          
          {/* Overlay Actions */}
          {interactive && (
            <Box
              className="slide-overlay"
              sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                display: 'flex',
                gap: 1,
                opacity: 0,
                transition: 'opacity 0.2s'
              }}
            >
              <Tooltip title="View fullscreen">
                <IconButton
                  size="small"
                  onClick={handleFullscreen}
                  sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: 'white' } }}
                >
                  <FullscreenIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              
              {onAddToAssembly && (
                <Tooltip title="Add to assembly">
                  <IconButton
                    size="small"
                    onClick={handleAddToAssembly}
                    sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: 'white' } }}
                  >
                    <AddIcon fontSize="small" color="primary" />
                  </IconButton>
                </Tooltip>
              )}

              <Tooltip title="More options">
                <IconButton
                  size="small"
                  onClick={handleMenuOpen}
                  sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: 'white' } }}
                >
                  <MoreIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}

          {/* Relevance Score Badge */}
          {slide.relevance_score > 0 && (
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                left: 8,
                bgcolor: 'rgba(0,0,0,0.7)',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.75rem',
                fontWeight: 600
              }}
            >
              {formatRelevanceScore(slide.relevance_score)}% match
            </Box>
          )}

          {/* Bookmark indicator */}
          {bookmarked && (
            <Box
              sx={{
                position: 'absolute',
                bottom: 8,
                right: 8
              }}
            >
              <BookmarkIcon color="warning" fontSize="small" />
            </Box>
          )}
        </Box>

        {/* Slide Content */}
        <CardContent sx={{ flexGrow: 1, p: compact ? 1.5 : 2, pb: compact ? 1.5 : 2 }}>
          {/* Header: Title and Type */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Typography
              variant={compact ? "subtitle2" : "h6"}
              sx={{
                fontWeight: 600,
                lineHeight: 1.2,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                flex: 1,
                mr: 1
              }}
            >
              {slide.title}
            </Typography>
            
            <Chip
              label={slide.slide_type}
              size="small"
              color={getSlideTypeColor(slide.slide_type)}
              variant="outlined"
              sx={{ flexShrink: 0 }}
            />
          </Box>

          {/* Content Preview */}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: compact ? 2 : 3,
              WebkitBoxOrient: 'vertical',
              mb: 1,
              lineHeight: 1.4
            }}
          >
            {slide.content_preview}
          </Typography>

          {/* Project Info */}
          <Typography 
            variant="caption" 
            color="text.secondary" 
            sx={{ display: 'block', mb: 1 }}
          >
            Project: {slide.project_name}
          </Typography>

          {/* Keywords */}
          {slide.keywords.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: showAIAnalysis ? 1 : 0 }}>
              {slide.keywords.slice(0, compact ? 3 : 5).map((keyword, index) => (
                <Chip
                  key={index}
                  label={keyword}
                  size="small"
                  variant="outlined"
                  sx={{ 
                    fontSize: '0.7rem', 
                    height: 20,
                    '&:hover': { bgcolor: 'primary.50' }
                  }}
                />
              ))}
              {slide.keywords.length > (compact ? 3 : 5) && (
                <Chip
                  label={`+${slide.keywords.length - (compact ? 3 : 5)}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
            </Box>
          )}

          {/* AI Analysis Section */}
          {showAIAnalysis && slide.ai_analysis && (
            <Box sx={{ mt: 1 }}>
              <Button
                size="small"
                startIcon={<AIIcon />}
                endIcon={showAnalysis ? <CollapseIcon /> : <ExpandIcon />}
                onClick={(e) => {
                  e.stopPropagation()
                  setShowAnalysis(!showAnalysis)
                }}
                sx={{ 
                  fontSize: '0.75rem',
                  p: 0.5,
                  minHeight: 'auto'
                }}
              >
                AI Analysis ({Math.round(slide.ai_analysis.ai_confidence_score * 100)}%)
              </Button>
              
              <Collapse in={showAnalysis}>
                <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  {/* Topic */}
                  <Typography variant="caption" color="text.secondary" display="block">
                    Topic: <strong>{slide.ai_analysis.ai_topic}</strong>
                  </Typography>
                  
                  {/* Summary */}
                  <Typography variant="caption" display="block" sx={{ mt: 0.5, mb: 1 }}>
                    {slide.ai_analysis.ai_summary}
                  </Typography>
                  
                  {/* Key Insights */}
                  {slide.ai_analysis.key_insights && slide.ai_analysis.key_insights.length > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Key Insights:
                      </Typography>
                      {slide.ai_analysis.key_insights.slice(0, compact ? 2 : 3).map((insight, index) => (
                        <Typography 
                          key={index} 
                          variant="caption" 
                          display="block" 
                          sx={{ ml: 1, fontSize: '0.7rem' }}
                        >
                          • {insight}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  
                  {/* Confidence Bar */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Confidence:
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={slide.ai_analysis.ai_confidence_score * 100}
                      color={getConfidenceColor(slide.ai_analysis.ai_confidence_score)}
                      sx={{ flex: 1, height: 4, borderRadius: 2 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {Math.round(slide.ai_analysis.ai_confidence_score * 100)}%
                    </Typography>
                  </Box>
                </Box>
              </Collapse>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={(e) => e.stopPropagation()}
      >
        <MenuItem onClick={handleShare}>
          <ListItemIcon>
            <ShareIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Share slide</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleDownload}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download image</ListItemText>
        </MenuItem>
        
        {onBookmark && (
          <MenuItem onClick={handleBookmark}>
            <ListItemIcon>
              {bookmarked ? <BookmarkIcon fontSize="small" /> : <BookmarkBorderIcon fontSize="small" />}
            </ListItemIcon>
            <ListItemText>{bookmarked ? 'Remove bookmark' : 'Bookmark slide'}</ListItemText>
          </MenuItem>
        )}
        
        <MenuItem onClick={() => window.open(`/slides/${slide.id}`, '_blank')}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View details</ListItemText>
        </MenuItem>
      </Menu>

      {/* Fullscreen Dialog */}
      <Dialog
        open={fullscreen}
        onClose={() => setFullscreen(false)}
        maxWidth={false}
        fullWidth
        PaperProps={{
          sx: {
            height: '90vh',
            maxHeight: '90vh',
            m: 2
          }
        }}
      >
        <DialogContent sx={{ p: 0, position: 'relative', height: '100%' }} data-testid="fullscreen-viewer">
          {/* Fullscreen Controls */}
          <Box
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              zIndex: 1,
              display: 'flex',
              gap: 1,
              bgcolor: 'rgba(0,0,0,0.7)',
              borderRadius: 1,
              p: 1
            }}
          >
            <Tooltip title="Zoom in">
              <IconButton
                size="small"
                onClick={() => setZoom(prev => Math.min(prev + 0.25, 3))}
                sx={{ color: 'white' }}
                aria-label="zoom in"
              >
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Zoom out">
              <IconButton
                size="small"
                onClick={() => setZoom(prev => Math.max(prev - 0.25, 0.5))}
                sx={{ color: 'white' }}
                aria-label="zoom out"
              >
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Reset zoom">
              <IconButton
                size="small"
                onClick={() => setZoom(1)}
                sx={{ color: 'white' }}
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Close">
              <IconButton
                size="small"
                onClick={() => setFullscreen(false)}
                sx={{ color: 'white' }}
              >
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Zoom indicator */}
          {zoom !== 1 && (
            <Box
              sx={{
                position: 'absolute',
                top: 16,
                left: 16,
                zIndex: 1,
                bgcolor: 'rgba(0,0,0,0.7)',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.875rem'
              }}
            >
              {Math.round(zoom * 100)}%
            </Box>
          )}

          {/* Fullscreen Image Container */}
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'black',
              overflow: 'hidden'
            }}
          >
            <img
              src={fullImageUrl}
              alt={slide.title}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                transform: `scale(${zoom})`,
                transition: 'transform 0.2s ease-in-out'
              }}
            />
          </Box>

          {/* Fullscreen Info Overlay */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              bgcolor: 'rgba(0,0,0,0.8)',
              color: 'white',
              p: 2
            }}
          >
            <Typography variant="h6" gutterBottom>
              {slide.title}
            </Typography>
            
            <Typography variant="body2" sx={{ mb: 1 }}>
              {slide.content_preview}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
              <Typography variant="caption">
                Project: {slide.project_name}
              </Typography>
              
              <Typography variant="caption">
                Type: {slide.slide_type}
              </Typography>
              
              {slide.relevance_score > 0 && (
                <Typography variant="caption">
                  Relevance: {formatRelevanceScore(slide.relevance_score)}%
                </Typography>
              )}
            </Box>
            
            {slide.keywords.length > 0 && (
              <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {slide.keywords.map((keyword, index) => (
                  <Chip
                    key={index}
                    label={keyword}
                    size="small"
                    sx={{ 
                      bgcolor: 'rgba(255,255,255,0.2)', 
                      color: 'white',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
                    }}
                  />
                ))}
              </Box>
            )}
          </Box>
        </DialogContent>
      </Dialog>
    </>
  )
}