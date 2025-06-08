"""
Search & Discovery Service for PrezI
Implements comprehensive search capabilities with AI-powered natural language processing
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, text

from backend.services.ai_service import AIService
from backend.database.models import SlideModel, KeywordModel, ProjectModel, FileModel
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class SearchFilter:
    """Search filter configuration"""
    query: str
    content_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    ai_confidence_min: Optional[float] = None
    ai_confidence_max: Optional[float] = None
    date_range: Optional[Dict[str, str]] = None
    sort_by: str = "relevance"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0
    include_ai_analysis: bool = True
    search_scope: str = "current_project"  # current_project | all_projects | specific_projects
    
    def __post_init__(self):
        """Validate filter parameters"""
        if not self.query.strip():
            raise ValueError("Search query cannot be empty")
        
        if self.ai_confidence_min is not None and (self.ai_confidence_min < 0 or self.ai_confidence_min > 1):
            raise ValueError("AI confidence minimum must be between 0 and 1")
        
        if self.ai_confidence_max is not None and (self.ai_confidence_max < 0 or self.ai_confidence_max > 1):
            raise ValueError("AI confidence maximum must be between 0 and 1")
        
        if self.sort_by not in ["relevance", "date", "title", "ai_confidence", "project"]:
            raise ValueError(f"Invalid sort_by value: {self.sort_by}")
        
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError(f"Invalid sort_order value: {self.sort_order}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary"""
        return asdict(self)

@dataclass
class SearchResult:
    """Search result item"""
    slide_id: str
    title: str
    content_preview: str
    slide_type: str
    project_id: str
    project_name: str
    keywords: List[str]
    thumbnail_path: Optional[str]
    relevance_score: float
    ai_analysis: Optional[Dict[str, Any]] = None
    semantic_score: Optional[float] = None
    match_highlights: Optional[List[str]] = None
    created_at: Optional[datetime] = None

class SearchService:
    """
    Comprehensive search and discovery service
    Implements AI-powered search with natural language processing
    """
    
    def __init__(self, db_session: Session, ai_service: AIService):
        self.db = db_session
        self.ai_service = ai_service
        self.settings = get_settings()
        
        # Initialize specialized search components
        self.semantic_engine = SemanticSearchEngine(self.db)
        self.cross_project_searcher = CrossProjectSearcher(self.db)
        self.analytics_tracker = SearchAnalyticsTracker(self.db)
        
        logger.info("Search service initialized successfully")
    
    async def natural_language_search(self, query: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process natural language search queries using AI
        Implements: AI-Driven Search & Discovery from spec
        """
        try:
            start_time = datetime.now()
            
            # Process query using AI service
            ai_result = await self.ai_service.process_natural_language_search(query, project_id)
            
            if not ai_result or not ai_result.get("success"):
                # Fallback to keyword search
                return await self._fallback_keyword_search(query, project_id)
            
            # Build search based on AI interpretation
            search_filter = self._build_filter_from_ai_result(ai_result, query, project_id)
            results = await self._execute_database_search(search_filter, ai_result["query_interpretation"])
            
            # Calculate search time
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "query": query,
                "query_interpretation": ai_result["query_interpretation"],
                "results": results["slides"],
                "total_results": results["total_count"],
                "search_time_ms": search_time,
                "search_strategy": "ai_natural_language"
            }
            
        except Exception as e:
            logger.error(f"Natural language search failed: {e}")
            return await self._fallback_keyword_search(query, project_id)
    
    async def cross_project_search(self, search_filter: SearchFilter) -> Dict[str, Any]:
        """
        Search across multiple projects globally
        Implements: Global cross-project search capability from spec
        """
        try:
            if search_filter.search_scope == "all_projects":
                # Get all accessible projects
                projects = await self._get_accessible_projects()
            elif search_filter.search_scope == "specific_projects":
                projects = search_filter.projects or []
            else:
                # Single project search
                projects = [search_filter.projects[0]] if search_filter.projects else []
            
            # Execute cross-project search
            cross_project_results = await self.cross_project_searcher.search_across_projects(
                search_filter, projects
            )
            
            return {
                "success": True,
                "results": cross_project_results["results"],
                "total_results": cross_project_results["total_results"],
                "projects_searched": cross_project_results["projects_searched"],
                "search_summary": cross_project_results["search_summary"],
                "search_strategy": "cross_project"
            }
            
        except Exception as e:
            logger.error(f"Cross-project search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def semantic_search(self, query: str, use_ai_embeddings: bool = True) -> Dict[str, Any]:
        """
        Perform semantic search using AI embeddings and similarity
        Implements: Semantic search beyond keyword matching from spec
        """
        try:
            semantic_results = await self.semantic_engine.semantic_search(
                query=query,
                use_ai_embeddings=use_ai_embeddings
            )
            
            return {
                "success": True,
                "query": query,
                "results": semantic_results["results"],
                "total_results": semantic_results["total_results"],
                "semantic_summary": semantic_results["semantic_summary"],
                "search_strategy": "semantic"
            }
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def advanced_search(self, search_filter: SearchFilter) -> Dict[str, Any]:
        """
        Execute advanced search with comprehensive filtering
        """
        try:
            # Apply advanced filters
            filtered_results = await self._apply_advanced_filters(search_filter)
            
            return {
                "success": True,
                "results": filtered_results["results"],
                "total_results": filtered_results["total_results"],
                "filters_applied": filtered_results["filters_applied"],
                "search_strategy": "advanced_filtered"
            }
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Generate search suggestions and autocomplete
        Implements: Smart suggestions from spec
        """
        try:
            suggestions = await self._generate_search_suggestions(partial_query, limit)
            
            return {
                "suggestions": suggestions,
                "total_suggestions": len(suggestions),
                "query": partial_query
            }
            
        except Exception as e:
            logger.error(f"Search suggestions failed: {e}")
            return {"suggestions": [], "total_suggestions": 0, "query": partial_query}
    
    async def search_with_analytics(self, query: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Perform search with analytics tracking
        Implements: Search analytics from spec
        """
        try:
            # Execute search
            search_result = await self.natural_language_search(query, **kwargs)
            
            # Track analytics
            analytics = await self.analytics_tracker.track_search(
                query=query,
                user_id=user_id,
                results_found=search_result.get("total_results", 0),
                search_time_ms=search_result.get("search_time_ms", 0),
                search_strategy=search_result.get("search_strategy", "unknown")
            )
            
            return {
                **search_result,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Search with analytics failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_database_search(self, search_filter: SearchFilter, ai_interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database search based on AI interpretation"""
        
        # Build base query
        query = self.db.query(SlideModel).join(FileModel).join(ProjectModel)
        
        # Apply AI-interpreted filters
        if "topics" in ai_interpretation:
            topic_conditions = []
            for topic in ai_interpretation["topics"]:
                if SlideModel.ai_analysis:  # Check if ai_analysis column exists
                    topic_conditions.append(SlideModel.ai_analysis['ai_topic'].contains(topic))
            if topic_conditions:
                query = query.filter(or_(*topic_conditions))
        
        if "keywords" in ai_interpretation:
            keyword_conditions = []
            for keyword in ai_interpretation["keywords"]:
                keyword_conditions.append(SlideModel.keywords.any(KeywordModel.name.ilike(f"%{keyword}%")))
            if keyword_conditions:
                query = query.filter(or_(*keyword_conditions))
        
        if "content_types" in ai_interpretation:
            query = query.filter(SlideModel.slide_type.in_(ai_interpretation["content_types"]))
        
        # Apply project filter if specified
        if search_filter.projects:
            query = query.filter(ProjectModel.id.in_(search_filter.projects))
        
        # Apply confidence filter
        if search_filter.ai_confidence_min and hasattr(SlideModel, 'ai_analysis'):
            query = query.filter(SlideModel.ai_analysis['ai_confidence_score'] >= search_filter.ai_confidence_min)
        
        # Apply sorting
        if search_filter.sort_by == "relevance":
            # Sort by AI confidence and keyword matches
            if hasattr(SlideModel, 'ai_analysis'):
                query = query.order_by(desc(SlideModel.ai_analysis['ai_confidence_score']))
            else:
                query = query.order_by(desc(SlideModel.title))
        elif search_filter.sort_by == "date":
            sort_col = FileModel.created_at
            query = query.order_by(desc(sort_col) if search_filter.sort_order == "desc" else asc(sort_col))
        elif search_filter.sort_by == "title":
            sort_col = SlideModel.title
            query = query.order_by(desc(sort_col) if search_filter.sort_order == "desc" else asc(sort_col))
        
        # Apply pagination
        total_count = query.count()
        slides = query.offset(search_filter.offset).limit(search_filter.limit).all()
        
        # Convert to search results
        search_results = []
        for slide in slides:
            result = SearchResult(
                slide_id=slide.id,
                title=slide.title or "Untitled Slide",
                content_preview=self._create_content_preview(slide),
                slide_type=slide.slide_type or "unknown",
                project_id=slide.file.project_id,
                project_name=slide.file.project.name,
                keywords=[kw.name for kw in slide.keywords],
                thumbnail_path=slide.thumbnail_path,
                relevance_score=self._calculate_relevance_score(slide, ai_interpretation),
                ai_analysis=slide.ai_analysis if search_filter.include_ai_analysis and hasattr(slide, 'ai_analysis') else None,
                created_at=slide.file.created_at
            )
            search_results.append(asdict(result))
        
        return {
            "slides": search_results,
            "total_count": total_count
        }
    
    def _build_filter_from_ai_result(self, ai_result: Dict[str, Any], query: str, project_id: Optional[str]) -> SearchFilter:
        """Build search filter from AI interpretation"""
        interpretation = ai_result["query_interpretation"]
        
        return SearchFilter(
            query=query,
            content_types=interpretation.get("content_types"),
            keywords=interpretation.get("keywords"),
            projects=[project_id] if project_id else None,
            sort_by="relevance",
            include_ai_analysis=True
        )
    
    async def _fallback_keyword_search(self, query: str, project_id: Optional[str]) -> Dict[str, Any]:
        """Fallback to simple keyword search when AI processing fails"""
        try:
            # Simple keyword-based search
            search_query = self.db.query(SlideModel).join(FileModel)
            
            # Text search in title and notes
            search_terms = query.lower().split()
            text_conditions = []
            for term in search_terms:
                text_conditions.extend([
                    SlideModel.title.ilike(f"%{term}%"),
                    SlideModel.notes.ilike(f"%{term}%")
                ])
            
            if text_conditions:
                search_query = search_query.filter(or_(*text_conditions))
            
            # Apply project filter
            if project_id:
                search_query = search_query.filter(FileModel.project_id == project_id)
            
            slides = search_query.limit(50).all()
            
            results = []
            for slide in slides:
                result = SearchResult(
                    slide_id=slide.id,
                    title=slide.title or "Untitled Slide",
                    content_preview=self._create_content_preview(slide),
                    slide_type=slide.slide_type or "unknown",
                    project_id=slide.file.project_id,
                    project_name=slide.file.project.name,
                    keywords=[kw.name for kw in slide.keywords],
                    thumbnail_path=slide.thumbnail_path,
                    relevance_score=0.5,  # Default score for keyword search
                    created_at=slide.file.created_at
                )
                results.append(asdict(result))
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_strategy": "keyword_fallback"
            }
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {"success": False, "error": str(e), "results": [], "total_results": 0}
    
    def _create_content_preview(self, slide: SlideModel) -> str:
        """Create content preview for search results"""
        preview_parts = []
        
        if slide.notes:
            preview_parts.append(slide.notes[:150])
        
        # Add element content if available
        for element in slide.elements[:3]:  # First 3 elements
            if element.content:
                preview_parts.append(element.content[:50])
        
        preview = " | ".join(preview_parts)
        return preview[:200] + "..." if len(preview) > 200 else preview
    
    def _calculate_relevance_score(self, slide: SlideModel, ai_interpretation: Dict[str, Any]) -> float:
        """Calculate relevance score for search result"""
        score = 0.0
        
        # AI confidence score (40% weight)
        if hasattr(slide, 'ai_analysis') and slide.ai_analysis and slide.ai_analysis.get('ai_confidence_score'):
            score += slide.ai_analysis['ai_confidence_score'] * 0.4
        else:
            score += 0.2  # Default if no AI analysis
        
        # Topic match (30% weight)
        if hasattr(slide, 'ai_analysis') and slide.ai_analysis and slide.ai_analysis.get('ai_topic'):
            slide_topic = slide.ai_analysis['ai_topic'].lower()
            for topic in ai_interpretation.get("topics", []):
                if topic.lower() in slide_topic:
                    score += 0.3
                    break
        
        # Keyword match (30% weight)
        slide_keywords = [kw.name.lower() for kw in slide.keywords]
        matching_keywords = len(set(slide_keywords) & set([k.lower() for k in ai_interpretation.get("keywords", [])]))
        max_keywords = max(len(ai_interpretation.get("keywords", [])), 1)
        score += (matching_keywords / max_keywords) * 0.3
        
        return min(score, 1.0)
    
    async def _get_accessible_projects(self) -> List[str]:
        """Get list of accessible project IDs"""
        projects = self.db.query(ProjectModel).all()
        return [project.id for project in projects]
    
    async def _apply_advanced_filters(self, search_filter: SearchFilter) -> Dict[str, Any]:
        """Apply advanced filtering logic"""
        try:
            # Build advanced query
            query = self.db.query(SlideModel).join(FileModel).join(ProjectModel)
            
            # Apply content type filters
            if search_filter.content_types:
                query = query.filter(SlideModel.slide_type.in_(search_filter.content_types))
            
            # Apply keyword filters
            if search_filter.keywords:
                keyword_conditions = []
                for keyword in search_filter.keywords:
                    keyword_conditions.append(
                        SlideModel.keywords.any(KeywordModel.name.ilike(f"%{keyword}%"))
                    )
                if keyword_conditions:
                    query = query.filter(and_(*keyword_conditions))
            
            # Apply project filters
            if search_filter.projects:
                query = query.filter(ProjectModel.id.in_(search_filter.projects))
            
            # Apply AI confidence filters
            if search_filter.ai_confidence_min and hasattr(SlideModel, 'ai_analysis'):
                query = query.filter(SlideModel.ai_analysis['ai_confidence_score'] >= search_filter.ai_confidence_min)
            
            if search_filter.ai_confidence_max and hasattr(SlideModel, 'ai_analysis'):
                query = query.filter(SlideModel.ai_analysis['ai_confidence_score'] <= search_filter.ai_confidence_max)
            
            # Apply date range filters
            if search_filter.date_range:
                if search_filter.date_range.get('start'):
                    start_date = datetime.fromisoformat(search_filter.date_range['start'])
                    query = query.filter(FileModel.created_at >= start_date)
                if search_filter.date_range.get('end'):
                    end_date = datetime.fromisoformat(search_filter.date_range['end'])
                    query = query.filter(FileModel.created_at <= end_date)
            
            # Apply text search
            if search_filter.query:
                text_conditions = [
                    SlideModel.title.ilike(f"%{search_filter.query}%"),
                    SlideModel.notes.ilike(f"%{search_filter.query}%")
                ]
                query = query.filter(or_(*text_conditions))
            
            # Apply sorting
            if search_filter.sort_by == "relevance":
                if hasattr(SlideModel, 'ai_analysis'):
                    query = query.order_by(desc(SlideModel.ai_analysis['ai_confidence_score']))
                else:
                    query = query.order_by(desc(SlideModel.title))
            elif search_filter.sort_by == "date":
                sort_col = FileModel.created_at
                query = query.order_by(desc(sort_col) if search_filter.sort_order == "desc" else asc(sort_col))
            elif search_filter.sort_by == "title":
                sort_col = SlideModel.title
                query = query.order_by(desc(sort_col) if search_filter.sort_order == "desc" else asc(sort_col))
            elif search_filter.sort_by == "ai_confidence" and hasattr(SlideModel, 'ai_analysis'):
                query = query.order_by(
                    desc(SlideModel.ai_analysis['ai_confidence_score']) 
                    if search_filter.sort_order == "desc" 
                    else asc(SlideModel.ai_analysis['ai_confidence_score'])
                )
            
            # Apply pagination
            total_count = query.count()
            slides = query.offset(search_filter.offset).limit(search_filter.limit).all()
            
            # Convert to search results
            results = []
            for slide in slides:
                result = SearchResult(
                    slide_id=slide.id,
                    title=slide.title or "Untitled Slide",
                    content_preview=self._create_content_preview(slide),
                    slide_type=slide.slide_type or "unknown",
                    project_id=slide.file.project_id,
                    project_name=slide.file.project.name,
                    keywords=[kw.name for kw in slide.keywords],
                    thumbnail_path=slide.thumbnail_path,
                    relevance_score=0.8,  # High score for filtered results
                    ai_analysis=slide.ai_analysis if search_filter.include_ai_analysis and hasattr(slide, 'ai_analysis') else None,
                    created_at=slide.file.created_at
                )
                results.append(asdict(result))
            
            return {
                "results": results,
                "total_results": total_count,
                "filters_applied": search_filter.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Advanced filtering failed: {e}")
            return {
                "results": [],
                "total_results": 0,
                "filters_applied": search_filter.to_dict()
            }
    
    async def _generate_search_suggestions(self, partial_query: str, limit: int) -> List[Dict[str, Any]]:
        """Generate search suggestions based on partial query"""
        suggestions = []
        
        try:
            # Get popular keywords
            keywords = self.db.query(KeywordModel).filter(
                KeywordModel.name.ilike(f"%{partial_query}%")
            ).order_by(desc(KeywordModel.usage_count)).limit(limit//2).all()
            
            for keyword in keywords:
                suggestions.append({
                    "text": keyword.name,
                    "type": "keyword",
                    "confidence": 0.8,
                    "result_count": keyword.usage_count
                })
            
            # Get title suggestions
            slides = self.db.query(SlideModel).filter(
                SlideModel.title.ilike(f"%{partial_query}%")
            ).limit(limit//3).all()
            
            for slide in slides:
                if slide.title:
                    suggestions.append({
                        "text": slide.title,
                        "type": "slide_title",
                        "confidence": 0.7,
                        "result_count": 1
                    })
            
            # Add AI suggestions if available
            if self.ai_service.is_available():
                try:
                    ai_suggestions = await self.ai_service.suggest_keywords_for_content(
                        partial_query, "search"
                    )
                    for suggestion in ai_suggestions[:limit//3]:
                        suggestions.append({
                            "text": suggestion["keyword"],
                            "type": "ai_suggestion",
                            "confidence": suggestion["confidence"],
                            "result_count": 0  # Would need to be calculated
                        })
                except Exception as e:
                    logger.warning(f"AI suggestions failed: {e}")
            
        except Exception as e:
            logger.error(f"Search suggestions generation failed: {e}")
        
        return suggestions[:limit]

class SemanticSearchEngine:
    """Semantic search engine using AI embeddings"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def semantic_search(self, query: str, use_ai_embeddings: bool = True) -> Dict[str, Any]:
        """Perform semantic search"""
        try:
            # For now, implement basic semantic search using text similarity
            # In a full implementation, this would use actual embeddings
            slides = self.db.query(SlideModel).join(FileModel).all()
            
            semantic_results = []
            for slide in slides:
                similarity_score = await self._calculate_text_similarity(query, slide)
                if similarity_score > 0.3:  # Threshold for relevance
                    semantic_results.append({
                        "slide_id": slide.id,
                        "title": slide.title or "Untitled Slide",
                        "semantic_score": similarity_score,
                        "slide_type": slide.slide_type or "unknown",
                        "project_id": slide.file.project_id
                    })
            
            # Sort by semantic score
            semantic_results.sort(key=lambda x: x["semantic_score"], reverse=True)
            
            return {
                "results": semantic_results[:20],  # Top 20 results
                "total_results": len(semantic_results),
                "semantic_summary": {
                    "query_embedding": [],  # Would contain actual embeddings
                    "average_score": sum(r["semantic_score"] for r in semantic_results) / max(len(semantic_results), 1),
                    "search_strategy": "text_similarity"
                }
            }
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {
                "results": [],
                "total_results": 0,
                "semantic_summary": {
                    "query_embedding": [],
                    "average_score": 0.0,
                    "search_strategy": "semantic_error"
                }
            }
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts"""
        return await self._calculate_semantic_similarity(text1, text2)
    
    async def _calculate_text_similarity(self, query: str, slide: SlideModel) -> float:
        """Calculate basic text similarity"""
        slide_text = f"{slide.title or ''} {slide.notes or ''}".lower()
        query_words = set(query.lower().split())
        slide_words = set(slide_text.split())
        
        if not query_words or not slide_words:
            return 0.0
        
        # Simple Jaccard similarity
        intersection = len(query_words & slide_words)
        union = len(query_words | slide_words)
        
        return intersection / union if union > 0 else 0.0
    
    async def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity - basic implementation"""
        # In a full implementation, this would use embeddings from OpenAI or similar
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

class CrossProjectSearcher:
    """Cross-project search functionality"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def search_across_projects(self, search_filter: SearchFilter, projects: List[str]) -> Dict[str, Any]:
        """Search across multiple projects"""
        try:
            # Build query for cross-project search
            query = self.db.query(SlideModel).join(FileModel).join(ProjectModel)
            
            # Filter by projects
            if projects:
                query = query.filter(ProjectModel.id.in_(projects))
            
            # Apply search filter
            if search_filter.query:
                text_conditions = [
                    SlideModel.title.ilike(f"%{search_filter.query}%"),
                    SlideModel.notes.ilike(f"%{search_filter.query}%")
                ]
                query = query.filter(or_(*text_conditions))
            
            # Apply content type filter
            if search_filter.content_types:
                query = query.filter(SlideModel.slide_type.in_(search_filter.content_types))
            
            # Apply keyword filter
            if search_filter.keywords:
                keyword_conditions = []
                for keyword in search_filter.keywords:
                    keyword_conditions.append(
                        SlideModel.keywords.any(KeywordModel.name.ilike(f"%{keyword}%"))
                    )
                if keyword_conditions:
                    query = query.filter(or_(*keyword_conditions))
            
            # Get results
            slides = query.limit(search_filter.limit).all()
            
            # Group results by project
            project_summary = {}
            type_summary = {}
            results = []
            
            for slide in slides:
                project_id = slide.file.project_id
                slide_type = slide.slide_type or "unknown"
                
                # Update summaries
                project_summary[project_id] = project_summary.get(project_id, 0) + 1
                type_summary[slide_type] = type_summary.get(slide_type, 0) + 1
                
                # Add to results
                results.append({
                    "slide_id": slide.id,
                    "title": slide.title or "Untitled Slide",
                    "slide_type": slide_type,
                    "project_id": project_id,
                    "project_name": slide.file.project.name,
                    "thumbnail_path": slide.thumbnail_path
                })
            
            return {
                "results": results,
                "total_results": len(results),
                "projects_searched": projects,
                "search_summary": {
                    "by_project": project_summary,
                    "by_type": type_summary
                }
            }
            
        except Exception as e:
            logger.error(f"Cross-project search failed: {e}")
            return {
                "results": [],
                "total_results": 0,
                "projects_searched": projects,
                "search_summary": {"by_project": {}, "by_type": {}}
            }
    
    async def global_search(self, query: str) -> Dict[str, Any]:
        """Global search across all accessible projects"""
        accessible_projects = await self._get_accessible_projects()
        search_filter = SearchFilter(query=query, search_scope="all_projects")
        return await self.search_across_projects(search_filter, accessible_projects)
    
    async def _get_accessible_projects(self) -> List[str]:
        """Get accessible projects"""
        try:
            projects = self.db.query(ProjectModel).all()
            return [project.id for project in projects]
        except Exception as e:
            logger.error(f"Failed to get accessible projects: {e}")
            return []

class SearchAnalyticsTracker:
    """Search analytics and tracking"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def track_search(self, query: str, user_id: str, results_found: int, 
                         search_time_ms: float, search_strategy: str) -> Dict[str, Any]:
        """Track search analytics"""
        analytics_data = {
            "query": query,
            "user_id": user_id,
            "results_found": results_found,
            "search_time_ms": search_time_ms,
            "search_strategy": search_strategy,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self._track_search_analytics(analytics_data)
    
    async def _track_search_analytics(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track search analytics - would save to analytics table"""
        try:
            # In a full implementation, this would save to an analytics table
            logger.info(f"Search analytics: {analytics_data}")
            
            return {
                "search_logged": True,
                "analytics": analytics_data
            }
            
        except Exception as e:
            logger.error(f"Failed to track search analytics: {e}")
            return {
                "search_logged": False,
                "analytics": analytics_data
            }

# Example usage and testing
if __name__ == "__main__":
    # This would be used for testing the search service
    import asyncio
    
    class MockSession:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def join(self, *args):
            return self
        def order_by(self, *args):
            return self
        def offset(self, offset):
            return self
        def limit(self, limit):
            return self
        def count(self):
            return 0
        def all(self):
            return []
    
    class MockAIService:
        def is_available(self):
            return True
        async def process_natural_language_search(self, query, project_id=None):
            return {"success": True, "query_interpretation": {"topics": [], "keywords": []}}
        async def suggest_keywords_for_content(self, content, context):
            return []
    
    async def test_search_service():
        try:
            search_service = SearchService(MockSession(), MockAIService())
            print("✅ Search service initialized successfully")
            
            # Test natural language search
            result = await search_service.natural_language_search("financial charts")
            print(f"✅ Natural language search completed: {result['search_strategy']}")
            
            # Test search suggestions
            suggestions = await search_service.get_search_suggestions("fin")
            print(f"✅ Search suggestions generated: {suggestions['total_suggestions']} suggestions")
            
        except Exception as e:
            print(f"❌ Search service test failed: {e}")
    
    # Run test
    asyncio.run(test_search_service())