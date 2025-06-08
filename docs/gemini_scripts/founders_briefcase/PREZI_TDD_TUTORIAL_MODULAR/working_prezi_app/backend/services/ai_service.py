"""
AI Service Implementation for PrezI
Implements comprehensive OpenAI integration for intelligent presentation management
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import tiktoken

import openai
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.database.models import SlideModel, KeywordModel, ProjectModel

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class APIKeyError(Exception):
    """Custom exception for API key errors"""
    pass

class AIService:
    """
    Main AI service orchestrator that coordinates all AI-powered features
    Implements the complete AI intelligence system from CONSOLIDATED_FOUNDERS_BRIEFCASE.md
    """
    
    def __init__(self, db_session: Session, api_key: Optional[str] = None):
        self.db = db_session
        self.settings = get_settings()
        
        # Initialize OpenAI client
        self.api_key = api_key or self.settings.openai_api_key
        if not self.api_key:
            raise APIKeyError("OpenAI API key is required but not provided")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize specialized AI components
        self.content_analyzer = ContentAnalyzer(self.client)
        self.nlp_processor = NaturalLanguageProcessor(self.client)
        self.presentation_planner = PresentationPlanner(self.client)
        self.personality_engine = AIPersonalityEngine(self.client)
        
        # Token usage tracking
        self.token_counter = tiktoken.get_encoding("cl100k_base")
        
        logger.info("AI Service initialized successfully")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return (
            self.client is not None and 
            self.settings.ai_analysis_enabled and 
            self.api_key is not None
        )
    
    async def analyze_slide_content(self, slide_id: str) -> Dict[str, Any]:
        """
        Analyze slide content and generate insights
        Implements: AI-Powered Content Intelligence from spec
        """
        slide = self.db.query(SlideModel).filter(SlideModel.id == slide_id).first()
        if not slide:
            raise AIServiceError(f"Slide {slide_id} not found")
        
        slide_content = {
            "title": slide.title,
            "content": slide.notes or "",
            "slide_type": slide.slide_type,
            "elements": [
                {
                    "type": element.element_type,
                    "content": element.content or "",
                    "position": {
                        "x": element.position_x,
                        "y": element.position_y,
                        "width": element.width,
                        "height": element.height
                    }
                }
                for element in slide.elements
            ]
        }
        
        try:
            # Analyze content using AI
            analysis_result = await self.content_analyzer.analyze_slide_content(slide_content)
            
            if analysis_result["success"]:
                # Update slide with AI analysis
                if not slide.ai_analysis:
                    slide.ai_analysis = {}
                
                slide.ai_analysis.update({
                    "ai_topic": analysis_result["analysis"]["topic"],
                    "ai_summary": analysis_result["analysis"]["summary"],
                    "ai_key_insights": analysis_result["analysis"]["key_insights"],
                    "ai_confidence_score": analysis_result["analysis"]["confidence_score"],
                    "analyzed_at": datetime.now().isoformat()
                })
                self.db.commit()
                
                # Auto-create suggested keywords
                if self.settings.ai_auto_tag:
                    await self._create_suggested_keywords(slide, analysis_result["suggested_keywords"])
            
            return analysis_result
        except Exception as e:
            logger.error(f"Failed to analyze slide {slide_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_analysis": self._create_fallback_analysis(slide_content)
            }
    
    async def process_natural_language_search(self, query: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process natural language search queries
        Implements: AI-Driven Search & Discovery from spec
        """
        try:
            # Process search intent
            search_result = await self.nlp_processor.process_search_query(query)
            
            if not search_result:
                return {"success": False, "error": "Failed to process search query"}
            
            # Build database query based on AI interpretation
            slides_query = self.db.query(SlideModel)
            
            # Apply project filter if specified
            if project_id:
                slides_query = slides_query.join(SlideModel.file).filter(
                    SlideModel.file.has(project_id=project_id)
                )
            
            # Apply AI-interpreted filters
            if "topics" in search_result:
                # Filter by AI-analyzed topics
                topic_conditions = []
                for topic in search_result["topics"]:
                    topic_conditions.append(SlideModel.ai_analysis['ai_topic'].contains(topic))
                if topic_conditions:
                    slides_query = slides_query.filter(or_(*topic_conditions))
            
            if "keywords" in search_result:
                keyword_filter = SlideModel.keywords.any(
                    KeywordModel.name.in_(search_result["keywords"])
                )
                slides_query = slides_query.filter(keyword_filter)
            
            if "content_types" in search_result:
                type_filter = SlideModel.slide_type.in_(search_result["content_types"])
                slides_query = slides_query.filter(type_filter)
            
            results = slides_query.all()
            
            return {
                "success": True,
                "query_interpretation": search_result,
                "results": [
                    {
                        "slide_id": slide.id,
                        "title": slide.title,
                        "topic": slide.ai_analysis.get('ai_topic') if slide.ai_analysis else None,
                        "summary": slide.ai_analysis.get('ai_summary') if slide.ai_analysis else None,
                        "relevance_score": self._calculate_relevance_score(slide, search_result)
                    }
                    for slide in results
                ],
                "total_results": len(results)
            }
        except Exception as e:
            logger.error(f"Natural language search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_automated_presentation(self, intent: str, project_id: str) -> Dict[str, Any]:
        """
        Create automated presentation from user intent
        Implements: AI-Automated Presentation Creation from spec
        """
        try:
            # Get available slides from project
            available_slides = self._get_project_slides(project_id)
            
            if not available_slides:
                return {
                    "success": False,
                    "error": "No slides available in project for presentation creation"
                }
            
            # Generate presentation plan
            plan_result = await self.presentation_planner.create_presentation_plan(
                intent, available_slides
            )
            
            if not plan_result:
                return {"success": False, "error": "Failed to create presentation plan"}
            
            # Create assembly based on plan
            assembly_data = {
                "name": plan_result["title"],
                "description": plan_result["objective"],
                "slides": plan_result["slide_sequence"],
                "ai_generated": True,
                "ai_intent": intent,
                "ai_plan": plan_result
            }
            
            return {
                "success": True,
                "assembly_plan": assembly_data,
                "recommendations": plan_result.get("talking_points", []),
                "estimated_duration": plan_result.get("estimated_duration", 15)
            }
        except Exception as e:
            logger.error(f"Automated presentation creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def suggest_keywords_for_content(self, content: str, context: str = "general") -> List[Dict[str, Any]]:
        """
        Generate keyword suggestions for content
        Implements: Automated Keyword Suggestion from spec
        """
        try:
            suggestions = await self.content_analyzer.suggest_keywords(content, context)
            
            # Filter and rank suggestions
            filtered_suggestions = []
            for suggestion in suggestions:
                if suggestion["confidence"] >= 0.7:  # Only high-confidence suggestions
                    # Check if keyword already exists
                    existing_keyword = self.db.query(KeywordModel).filter(
                        KeywordModel.name == suggestion["keyword"]
                    ).first()
                    
                    suggestion["exists"] = existing_keyword is not None
                    suggestion["usage_count"] = existing_keyword.usage_count if existing_keyword else 0
                    
                    filtered_suggestions.append(suggestion)
            
            # Sort by confidence and existing usage
            filtered_suggestions.sort(
                key=lambda x: (x["confidence"], x["usage_count"]), 
                reverse=True
            )
            
            return filtered_suggestions[:10]  # Return top 10 suggestions
        except Exception as e:
            logger.error(f"Keyword suggestion failed: {e}")
            return []
    
    async def provide_contextual_assistance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide contextual suggestions and assistance
        Implements: Proactive & Personalized Partnership from spec
        """
        try:
            suggestions = await self.personality_engine.generate_contextual_suggestion(context)
            
            return {
                "suggestion": suggestions.get("message", ""),
                "action_type": suggestions.get("action_suggested"),
                "priority": suggestions.get("priority", "low"),
                "helpful_tips": suggestions.get("helpful_tips", [])
            }
        except Exception as e:
            logger.error(f"Contextual assistance failed: {e}")
            return {"suggestion": "", "action_type": None, "priority": "low", "helpful_tips": []}
    
    def _get_project_slides(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all slides from a project for planning"""
        slides = self.db.query(SlideModel).join(SlideModel.file).filter(
            SlideModel.file.has(project_id=project_id)
        ).all()
        
        return [
            {
                "id": slide.id,
                "title": slide.title,
                "topic": slide.ai_analysis.get('ai_topic', 'unknown') if slide.ai_analysis else 'unknown',
                "slide_type": slide.slide_type,
                "keywords": [kw.name for kw in slide.keywords],
                "summary": slide.ai_analysis.get('ai_summary', '') if slide.ai_analysis else '',
                "confidence": slide.ai_analysis.get('ai_confidence_score', 0.5) if slide.ai_analysis else 0.5
            }
            for slide in slides
        ]
    
    def _calculate_relevance_score(self, slide: SlideModel, search_result: Dict[str, Any]) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        
        # Topic relevance
        if slide.ai_analysis and slide.ai_analysis.get('ai_topic') in search_result.get("topics", []):
            score += 0.4
        
        # Keyword relevance
        slide_keywords = [kw.name for kw in slide.keywords]
        matching_keywords = set(slide_keywords) & set(search_result.get("keywords", []))
        score += (len(matching_keywords) / max(len(search_result.get("keywords", [])), 1)) * 0.3
        
        # Content type relevance
        if slide.slide_type in search_result.get("content_types", []):
            score += 0.2
        
        # AI confidence bonus
        if slide.ai_analysis:
            score += (slide.ai_analysis.get('ai_confidence_score', 0.5) * 0.1)
        
        return min(score, 1.0)
    
    def _create_suggested_keywords(self, slide: SlideModel, suggested_keywords: List[Dict[str, Any]]):
        """Create or associate suggested keywords with slide"""
        for suggestion in suggested_keywords:
            if suggestion["confidence"] >= 0.8:  # Only very confident suggestions
                # Check if keyword exists
                keyword = self.db.query(KeywordModel).filter(
                    KeywordModel.name == suggestion["keyword"]
                ).first()
                
                if not keyword:
                    # Create new keyword
                    keyword = KeywordModel(
                        name=suggestion["keyword"],
                        description=f"AI-suggested keyword (confidence: {suggestion['confidence']:.2f})",
                        # is_ai_suggested=True,
                        # ai_confidence=suggestion["confidence"],
                        # semantic_group=suggestion.get("category", "general")
                    )
                    self.db.add(keyword)
                    self.db.flush()
                
                # Associate with slide if not already associated
                if keyword not in slide.keywords:
                    slide.slide_keywords.append(keyword)
                    keyword.usage_count += 1
        
        self.db.commit()
    
    def _create_fallback_analysis(self, slide_content: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when AI processing fails"""
        return {
            "topic": "general",
            "slide_type": slide_content.get('slide_type', 'unknown'),
            "key_insights": ["Content analysis unavailable"],
            "confidence_score": 0.1,
            "summary": f"Slide with title: {slide_content.get('title', 'Unknown')}"
        }

class ContentAnalyzer:
    """
    Specialized AI component for content analysis and understanding
    """
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.model = get_settings().openai_model
    
    async def analyze_slide_content(self, slide_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze slide content and extract insights"""
        try:
            prompt = self._build_analysis_prompt(slide_content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert presentation analyst. Analyze slide content and provide structured insights including topic classification, key insights, and keyword suggestions. Respond with valid JSON only."""
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "analysis": result.get("slide_analysis", {}),
                "suggested_keywords": result.get("suggested_keywords", []),
                "element_analysis": result.get("element_analysis", [])
            }
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_analysis": self._generate_fallback_analysis(slide_content)
            }
    
    async def suggest_keywords(self, content: str, context: str = "general") -> List[Dict[str, Any]]:
        """Generate keyword suggestions for content"""
        try:
            prompt = f"""
            Analyze the following content and suggest relevant keywords for presentation management:
            
            Context: {context}
            Content: {content}
            
            Return JSON array:
            [
                {{"keyword": "keyword-name", "confidence": 0.9, "category": "business|financial|technical|general"}}
            ]
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Keyword suggestion failed: {e}")
            return []
    
    async def batch_analyze_slides(self, slides_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch analyze multiple slides efficiently"""
        results = []
        
        for slide_data in slides_data:
            try:
                result = await self.analyze_slide_content(slide_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze slide: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "fallback_analysis": self._generate_fallback_analysis(slide_data)
                })
        
        return results
    
    async def extract_chart_insights(self, chart_element: Dict[str, Any], slide_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific insights from chart elements"""
        try:
            prompt = f"""
            Analyze this chart element and extract business insights:
            
            Chart: {json.dumps(chart_element)}
            Slide context: {json.dumps(slide_context)}
            
            Return JSON:
            {{
                "chart_insights": ["insight1", "insight2"],
                "data_patterns": ["pattern1", "pattern2"],
                "business_implications": ["implication1", "implication2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Chart analysis failed: {e}")
            return {"chart_insights": [], "data_patterns": [], "business_implications": []}
    
    def _build_analysis_prompt(self, slide_content: Dict[str, Any]) -> str:
        """Build detailed analysis prompt"""
        return f"""
        Analyze this presentation slide and provide comprehensive insights:

        Title: {slide_content.get('title', 'No title')}
        Content: {slide_content.get('content', 'No content')}
        Slide Type: {slide_content.get('slide_type', 'unknown')}
        Elements: {len(slide_content.get('elements', []))} elements including {[e['type'] for e in slide_content.get('elements', [])]}

        Provide analysis in this JSON format:
        {{
            "slide_analysis": {{
                "topic": "main topic/theme",
                "slide_type": "title|content|chart|image|table|conclusion",
                "key_insights": ["insight1", "insight2", "insight3"],
                "confidence_score": 0.0-1.0,
                "summary": "brief summary of slide purpose and content"
            }},
            "suggested_keywords": [
                {{"keyword": "keyword-name", "confidence": 0.0-1.0, "category": "business|financial|technical|general"}}
            ],
            "element_analysis": [
                {{"element_type": "chart|image|text", "description": "what this element shows", "data_insights": ["insight1"], "importance": "high|medium|low"}}
            ]
        }}
        """
    
    def _generate_fallback_analysis(self, slide_content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic fallback analysis when AI fails"""
        return {
            "topic": "general",
            "slide_type": slide_content.get('slide_type', 'unknown'),
            "key_insights": ["Content analysis unavailable"],
            "confidence_score": 0.1,
            "summary": f"Slide with title: {slide_content.get('title', 'Unknown')}"
        }

class NaturalLanguageProcessor:
    """Natural language processing for search and commands"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.model = get_settings().openai_model
    
    async def process_search_query(self, query: str) -> Dict[str, Any]:
        """Process natural language search queries"""
        try:
            prompt = f"""
            Parse this search query and extract search intent and parameters:
            
            Query: "{query}"
            
            Return JSON:
            {{
                "search_intent": "find_content|create_assembly|tag_content|export",
                "content_types": ["chart", "image", "text", "table"],
                "topics": ["topic1", "topic2"],
                "keywords": ["keyword1", "keyword2"],
                "filters": {{}},
                "confidence": 0.0-1.0
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            return None
    
    async def process_assembly_command(self, command: str) -> Dict[str, Any]:
        """Process presentation assembly commands"""
        try:
            prompt = f"""
            Parse this presentation assembly command:
            
            Command: "{command}"
            
            Return JSON:
            {{
                "command_type": "create_presentation|modify_slides|export",
                "presentation_intent": "investor_pitch|sales_demo|training|report",
                "target_audience": "audience description",
                "required_topics": ["topic1", "topic2"],
                "presentation_structure": [
                    {{"section": "introduction", "slides": 1}},
                    {{"section": "main_content", "slides": 3}}
                ],
                "estimated_duration": 15,
                "suggested_slides": ["slide_type1", "slide_type2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Assembly command processing failed: {e}")
            return None
    
    async def detect_intent(self, command: str) -> Dict[str, Any]:
        """Detect user intent from command"""
        try:
            prompt = f"""
            Detect the user's intent from this command:
            
            Command: "{command}"
            
            Return JSON:
            {{
                "intent": "search|create_assembly|tag_content|export|get_help",
                "confidence": 0.0-1.0,
                "parameters": {{}}
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return {"intent": "unknown", "confidence": 0.0, "parameters": {}}

class PresentationPlanner:
    """AI-powered presentation planning and assembly"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.model = get_settings().openai_model
    
    async def create_presentation_plan(self, intent: str, available_slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive presentation plan"""
        try:
            prompt = f"""
            Create a presentation plan for this intent: "{intent}"
            
            Available slides: {json.dumps(available_slides[:20])}
            
            Return JSON:
            {{
                "title": "presentation title",
                "objective": "presentation objective",
                "target_audience": "audience description",
                "estimated_duration": 20,
                "slide_sequence": [
                    {{"position": 1, "slide_id": "id", "rationale": "why this slide", "transitions": "how it connects"}}
                ],
                "talking_points": ["point1", "point2"],
                "success_metrics": ["metric1", "metric2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=2000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Presentation planning failed: {e}")
            return None
    
    async def optimize_slide_order(self, current_order: List[str], available_slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize slide order for better flow"""
        try:
            prompt = f"""
            Optimize this slide order for better presentation flow:
            
            Current order: {current_order}
            Available slides: {json.dumps(available_slides)}
            
            Return JSON:
            {{
                "optimized_order": ["slide1", "slide2", "slide3"],
                "improvements": ["improvement1", "improvement2"],
                "flow_score": 0.0-1.0,
                "rationale": "explanation of changes"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Slide order optimization failed: {e}")
            return None
    
    async def suggest_missing_content(self, available_slides: List[Dict[str, Any]], presentation_topic: str) -> Dict[str, Any]:
        """Suggest missing content for better presentation"""
        try:
            prompt = f"""
            Analyze available slides and suggest missing content for: "{presentation_topic}"
            
            Available slides: {json.dumps(available_slides)}
            
            Return JSON:
            {{
                "missing_content": [
                    {{
                        "content_type": "slide|section",
                        "suggested_title": "title",
                        "rationale": "why needed",
                        "position": 2,
                        "priority": "high|medium|low"
                    }}
                ],
                "enhancement_suggestions": ["suggestion1", "suggestion2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Missing content analysis failed: {e}")
            return {"missing_content": [], "enhancement_suggestions": []}

class AIPersonalityEngine:
    """AI personality and contextual communication"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.model = get_settings().openai_model
    
    async def generate_contextual_suggestion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate helpful contextual suggestions"""
        try:
            prompt = f"""
            Based on this context, provide a helpful suggestion:
            
            Context: {json.dumps(context)}
            
            Return JSON:
            {{
                "message": "helpful suggestion message",
                "tone": "helpful|supportive|encouraging",
                "action_suggested": "specific_action",
                "rationale": "why this suggestion",
                "priority": "high|medium|low"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are PrezI, a helpful AI assistant for presentation management. Be friendly, professional, and supportive."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=800
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Contextual suggestion failed: {e}")
            return {"message": "", "tone": "helpful", "action_suggested": None, "priority": "low"}
    
    async def handle_user_error(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide friendly error handling"""
        try:
            prompt = f"""
            Create a user-friendly error message for this error:
            
            Error context: {json.dumps(error_context)}
            
            Return JSON:
            {{
                "user_message": "friendly error message",
                "suggested_actions": ["action1", "action2"],
                "tone": "supportive|helpful",
                "technical_details": "technical explanation for advanced users"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are PrezI. Convert technical errors into friendly, actionable messages."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=600
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
            return {
                "user_message": "An unexpected error occurred. Please try again.",
                "suggested_actions": ["Refresh the page", "Contact support"],
                "tone": "supportive",
                "technical_details": str(e)
            }
    
    async def provide_presentation_coaching(self, presentation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide presentation coaching and tips"""
        try:
            prompt = f"""
            Provide presentation coaching based on this context:
            
            Context: {json.dumps(presentation_context)}
            
            Return JSON:
            {{
                "coaching_advice": ["advice1", "advice2"],
                "presentation_tips": ["tip1", "tip2"],
                "timing_suggestions": ["timing1", "timing2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert presentation coach. Provide practical, actionable advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Presentation coaching failed: {e}")
            return {"coaching_advice": [], "presentation_tips": [], "timing_suggestions": []}

# Example usage and testing
if __name__ == "__main__":
    # This would be used for testing the AI service
    class MockSession:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def first(self):
            return None
        def all(self):
            return []
        def join(self, *args):
            return self
        def add(self, obj):
            pass
        def commit(self):
            pass
        def flush(self):
            pass
    
    # Test AI service initialization
    try:
        ai_service = AIService(MockSession(), api_key="test-key")
        print("✅ AI Service initialized successfully")
        print(f"Available: {ai_service.is_available()}")
        
    except APIKeyError as e:
        print(f"❌ API Key Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")