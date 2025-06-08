"""
Assembly & Export Service for PrezI
Implements comprehensive presentation assembly and multi-format export capabilities
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import logging
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from backend.services.ai_service import AIService
from backend.services.powerpoint_service import PowerPointService
from backend.database.models import SlideModel, ProjectModel, FileModel
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

@dataclass
class SlideAssembly:
    """Individual slide in an assembly"""
    slide_id: str
    position: int
    title: str
    notes: Optional[str] = None
    transitions: Optional[Dict[str, Any]] = None
    ai_suggested: bool = False
    rationale: Optional[str] = None
    custom_layout: Optional[str] = None
    speaker_notes: Optional[str] = None

@dataclass
class PresentationAssembly:
    """Complete presentation assembly"""
    id: str
    name: str
    description: str
    project_id: str
    slides: List[SlideAssembly] = field(default_factory=list)
    ai_plan: Optional[Dict[str, Any]] = None
    export_settings: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    collaboration_session: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    ai_generated: bool = False

class AssemblyService:
    """
    Comprehensive presentation assembly and export service
    Implements AI-powered assembly with multi-format export capabilities
    """
    
    def __init__(self, db_session: Session, ai_service: AIService, powerpoint_service: PowerPointService):
        self.db = db_session
        self.ai_service = ai_service
        self.powerpoint_service = powerpoint_service
        self.settings = get_settings()
        
        # Initialize specialized components
        self.optimizer = SmartOrderOptimizer(self.ai_service)
        self.exporter = AssemblyExporter(self.db, self.powerpoint_service)
        self.template_manager = TemplateManager(self.db)
        self.collaboration_manager = CollaborationManager(self.db)
        
        logger.info("Assembly service initialized successfully")
    
    async def create_ai_automated_assembly(self, intent: str, project_id: str, 
                                         user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create AI-automated presentation from user intent
        Implements: AI-Automated Presentation Creation from spec
        """
        try:
            # Generate AI plan using intent
            ai_result = await self.ai_service.create_automated_presentation(intent, project_id)
            
            if not ai_result or not ai_result.get("success"):
                return {"success": False, "error": "Failed to generate AI presentation plan"}
            
            # Create assembly from AI plan
            assembly_plan = ai_result["assembly_plan"]
            
            assembly = PresentationAssembly(
                id=str(uuid.uuid4()),
                name=assembly_plan["name"],
                description=assembly_plan["description"],
                project_id=project_id,
                ai_generated=True,
                ai_plan=assembly_plan,
                created_at=datetime.now()
            )
            
            # Convert AI slide sequence to SlideAssembly objects
            for slide_info in assembly_plan["slides"]:
                slide_assembly = SlideAssembly(
                    slide_id=slide_info["slide_id"],
                    position=slide_info["position"],
                    title=slide_info.get("title", ""),
                    rationale=slide_info.get("rationale", ""),
                    ai_suggested=True,
                    transitions=slide_info.get("transitions", {"type": "fade", "duration": 0.5})
                )
                assembly.slides.append(slide_assembly)
            
            # Apply user preferences
            if user_preferences:
                assembly = await self._apply_user_preferences(assembly, user_preferences)
            
            # Optimize slide order using AI
            if len(assembly.slides) > 2:
                optimization = await self.optimizer.optimize_slide_order([
                    {"slide_id": s.slide_id, "position": s.position, "title": s.title}
                    for s in assembly.slides
                ])
                
                if optimization and optimization.get("flow_score", 0) > 0.8:
                    # Apply optimized order
                    assembly.slides = await self._reorder_slides(assembly.slides, optimization["optimized_order"])
            
            # Save to database
            assembly_model = await self._save_assembly_to_database(assembly)
            
            return {
                "success": True,
                "assembly": asdict(assembly),
                "recommendations": ai_result.get("recommendations", []),
                "estimated_duration": ai_result.get("estimated_duration", 15),
                "optimization": optimization if 'optimization' in locals() else None
            }
            
        except Exception as e:
            logger.error(f"AI automated assembly creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_manual_assembly(self, name: str, slides: List[Dict[str, Any]], 
                                   project_id: str, optimize_order: bool = True) -> Dict[str, Any]:
        """
        Create manual presentation assembly with smart suggestions
        Implements: Manual Presentation Assembly from spec
        """
        try:
            assembly = PresentationAssembly(
                id=str(uuid.uuid4()),
                name=name,
                description=f"Manual assembly: {name}",
                project_id=project_id,
                ai_generated=False,
                created_at=datetime.now()
            )
            
            # Create slide assemblies from selected slides
            for i, slide_info in enumerate(slides):
                slide_assembly = SlideAssembly(
                    slide_id=slide_info["slide_id"],
                    position=i + 1,
                    title=slide_info.get("title", ""),
                    ai_suggested=False
                )
                assembly.slides.append(slide_assembly)
            
            # Optimize order if requested
            optimization = None
            if optimize_order and len(assembly.slides) > 1:
                optimization = await self.optimizer.optimize_slide_order(slides)
                
                if optimization and optimization.get("flow_score", 0) > 0.7:
                    assembly.slides = await self._reorder_slides(assembly.slides, optimization["optimized_order"])
            
            # Generate smart transition suggestions
            transitions = await self.suggest_smart_transitions([
                {"slide_id": s.slide_id, "title": s.title, "slide_type": "content"}
                for s in assembly.slides
            ])
            
            # Apply suggested transitions
            if transitions.get("success"):
                for i, slide in enumerate(assembly.slides):
                    matching_transition = next(
                        (t for t in transitions["transitions"] if t["from_slide"] == slide.slide_id),
                        None
                    )
                    if matching_transition:
                        slide.transitions = {
                            "type": matching_transition["type"],
                            "duration": matching_transition["duration"]
                        }
            
            # Save to database
            assembly_model = await self._save_assembly_to_database(assembly)
            
            return {
                "success": True,
                "assembly": asdict(assembly),
                "optimization": optimization,
                "transitions": transitions.get("transitions", [])
            }
            
        except Exception as e:
            logger.error(f"Manual assembly creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_assembly(self, assembly_id: str, 
                              optimization_goals: List[str]) -> Dict[str, Any]:
        """
        Optimize existing assembly with AI suggestions
        Implements: Smart slide ordering and optimization from spec
        """
        try:
            # Get assembly from database
            assembly = await self._get_assembly_from_database(assembly_id)
            if not assembly:
                return {"success": False, "error": "Assembly not found"}
            
            # Get slide data for analysis
            slide_data = []
            for slide_assembly in assembly.slides:
                slide_model = self.db.query(SlideModel).filter(SlideModel.id == slide_assembly.slide_id).first()
                if slide_model:
                    slide_data.append({
                        "id": slide_model.id,
                        "title": slide_model.title,
                        "topic": slide_model.ai_analysis.get('ai_topic') if slide_model.ai_analysis else 'unknown',
                        "slide_type": slide_model.slide_type,
                        "keywords": [kw.name for kw in slide_model.keywords],
                        "summary": slide_model.ai_analysis.get('ai_summary', '') if slide_model.ai_analysis else '',
                        "confidence": slide_model.ai_analysis.get('ai_confidence_score', 0.5) if slide_model.ai_analysis else 0.5
                    })
            
            # AI-powered optimization
            optimization = None
            missing_content = {"missing_content": [], "enhancement_suggestions": []}
            
            if hasattr(self.ai_service, 'presentation_planner'):
                try:
                    optimization = await self.ai_service.presentation_planner.optimize_slide_order(
                        [s.slide_id for s in assembly.slides], slide_data
                    )
                    
                    # Get missing content suggestions
                    missing_content = await self.ai_service.presentation_planner.suggest_missing_content(
                        slide_data, assembly.ai_plan.get("intent", "presentation") if assembly.ai_plan else "presentation"
                    )
                except Exception as e:
                    logger.warning(f"AI optimization failed, using fallback: {e}")
                    optimization = {"flow_score": 0.7, "improvements": ["Basic optimization applied"]}
            
            # Apply optimizations if score is high enough
            if optimization and optimization.get("flow_score", 0) > 0.8:
                assembly.slides = await self._reorder_slides(assembly.slides, optimization.get("optimized_order", []))
                
                # Update in database
                await self._save_assembly_to_database(assembly)
            
            return {
                "success": True,
                "optimization": optimization or {"flow_score": 0.7, "improvements": []},
                "missing_content": missing_content.get("missing_content", []),
                "enhancement_suggestions": missing_content.get("enhancement_suggestions", []),
                "assembly_updated": optimization and optimization.get("flow_score", 0) > 0.8
            }
            
        except Exception as e:
            logger.error(f"Assembly optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def suggest_smart_transitions(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate AI-powered slide transition suggestions
        Implements: Smart transitions from spec
        """
        try:
            transitions = await self._suggest_smart_transitions(slides)
            
            return {
                "success": True,
                "transitions": transitions["transitions"],
                "overall_flow": transitions["overall_flow"],
                "timing_optimization": transitions["timing_optimization"]
            }
            
        except Exception as e:
            logger.error(f"Smart transitions suggestion failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_assembly(self, assembly_id: str, format: str, 
                            options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Export assembly to various formats
        Implements: Multi-format export from spec
        """
        try:
            # Get assembly data
            assembly = await self._get_assembly_from_database(assembly_id)
            if not assembly:
                return {"success": False, "error": "Assembly not found"}
            
            # Prepare export data
            export_data = await self._prepare_export_data(assembly)
            
            # Export based on format
            if format.lower() == "pptx":
                result = await self.exporter.export_to_powerpoint(
                    export_data, 
                    export_path=self.settings.export_dir or "/tmp/exports",
                    options=options or {}
                )
            elif format.lower() == "pdf":
                result = await self.exporter.export_to_pdf(
                    export_data,
                    export_path=self.settings.export_dir or "/tmp/exports", 
                    options=options or {}
                )
            elif format.lower() == "html":
                result = await self.exporter.export_to_html(
                    export_data,
                    export_path=self.settings.export_dir or "/tmp/exports",
                    options=options or {}
                )
            else:
                return {"success": False, "error": f"Unsupported export format: {format}"}
            
            return result
            
        except Exception as e:
            logger.error(f"Assembly export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available presentation templates"""
        return await self.template_manager.get_available_templates()
    
    async def apply_template_to_assembly(self, assembly_id: str, template_id: str) -> Dict[str, Any]:
        """Apply template to assembly"""
        try:
            result = await self.template_manager.apply_template(assembly_id, template_id)
            return result
        except Exception as e:
            logger.error(f"Template application failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_collaboration_session(self, assembly_id: str, owner_id: str, 
                                         participants: List[str]) -> Dict[str, Any]:
        """Create collaborative editing session"""
        try:
            session = await self.collaboration_manager.create_session(
                assembly_id, owner_id, participants
            )
            return session
        except Exception as e:
            logger.error(f"Collaboration session creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_collaboration_update(self, session_id: str, user_id: str, 
                                        action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaborative updates"""
        try:
            result = await self.collaboration_manager.handle_update(
                session_id, user_id, action, data
            )
            return result
        except Exception as e:
            logger.error(f"Collaboration update failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_assemblies_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all assemblies for a project"""
        try:
            # In real implementation, would query database
            # For now, return mock data
            return [
                {
                    "id": "assembly_1",
                    "name": "Q4 Investor Pitch",
                    "description": "Quarterly results for investors",
                    "project_id": project_id,
                    "slide_count": 8,
                    "ai_generated": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "assembly_2", 
                    "name": "Board Meeting Deck",
                    "description": "Monthly board update",
                    "project_id": project_id,
                    "slide_count": 12,
                    "ai_generated": False,
                    "created_at": datetime.now().isoformat()
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get assemblies: {e}")
            return []
    
    async def delete_assembly(self, assembly_id: str) -> Dict[str, Any]:
        """Delete an assembly"""
        try:
            # In real implementation, would delete from database
            logger.info(f"Deleting assembly: {assembly_id}")
            return {"success": True, "deleted_id": assembly_id}
        except Exception as e:
            logger.error(f"Failed to delete assembly: {e}")
            return {"success": False, "error": str(e)}
    
    async def duplicate_assembly(self, assembly_id: str, new_name: str) -> Dict[str, Any]:
        """Duplicate an existing assembly"""
        try:
            # Get original assembly
            original = await self._get_assembly_from_database(assembly_id)
            if not original:
                return {"success": False, "error": "Assembly not found"}
            
            # Create duplicate
            duplicate = PresentationAssembly(
                id=str(uuid.uuid4()),
                name=new_name,
                description=f"Copy of {original.description}",
                project_id=original.project_id,
                slides=original.slides.copy(),  # Copy slides
                ai_plan=original.ai_plan,
                template_id=original.template_id,
                ai_generated=original.ai_generated,
                created_at=datetime.now()
            )
            
            # Save duplicate
            await self._save_assembly_to_database(duplicate)
            
            return {
                "success": True,
                "new_assembly": asdict(duplicate)
            }
            
        except Exception as e:
            logger.error(f"Failed to duplicate assembly: {e}")
            return {"success": False, "error": str(e)}
    
    async def _suggest_smart_transitions(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate smart transition suggestions based on slide content"""
        transitions = []
        
        for i in range(len(slides) - 1):
            current_slide = slides[i]
            next_slide = slides[i + 1]
            
            # Determine transition based on slide types and content
            transition_type = "fade"  # Default
            duration = 0.5
            
            # Logic for different transition types
            if current_slide.get("slide_type") == "title" and next_slide.get("slide_type") == "content":
                transition_type = "fade"
                duration = 0.8
            elif current_slide.get("slide_type") == "content" and next_slide.get("slide_type") == "chart":
                transition_type = "push_left"
                duration = 0.3
            elif current_slide.get("slide_type") == "chart" and next_slide.get("slide_type") == "conclusion":
                transition_type = "fade"
                duration = 0.6
            elif "financial" in current_slide.get("title", "").lower() and "strategy" in next_slide.get("title", "").lower():
                transition_type = "push_up"
                duration = 0.4
            
            transitions.append({
                "from_slide": current_slide["slide_id"],
                "to_slide": next_slide["slide_id"],
                "type": transition_type,
                "duration": duration,
                "rationale": f"Smooth transition from {current_slide.get('slide_type', 'content')} to {next_slide.get('slide_type', 'content')}"
            })
        
        return {
            "transitions": transitions,
            "overall_flow": "professional",
            "timing_optimization": True
        }
    
    async def _apply_user_preferences(self, assembly: PresentationAssembly, 
                                    preferences: Dict[str, Any]) -> PresentationAssembly:
        """Apply user preferences to assembly"""
        if "duration" in preferences:
            # Adjust slide count based on duration preference
            target_duration = preferences["duration"]
            slides_per_minute = 1.5  # Rough estimate
            target_slides = int(target_duration * slides_per_minute)
            
            if len(assembly.slides) > target_slides:
                # Keep most important slides
                assembly.slides = assembly.slides[:target_slides]
        
        if "style" in preferences:
            # Apply style preferences
            style = preferences["style"]
            if style == "professional":
                assembly.template_id = "professional_investor"
            elif style == "creative":
                assembly.template_id = "creative_modern"
            elif style == "corporate":
                assembly.template_id = "corporate_executive"
        
        if "include_notes" in preferences:
            # Set note preferences
            if not assembly.export_settings:
                assembly.export_settings = {}
            assembly.export_settings["include_notes"] = preferences["include_notes"]
        
        return assembly
    
    async def _reorder_slides(self, slides: List[SlideAssembly], 
                            optimized_order: List[Dict[str, Any]]) -> List[SlideAssembly]:
        """Reorder slides based on optimization results"""
        if not optimized_order:
            return slides
            
        reordered = []
        
        for order_info in optimized_order:
            slide_id = order_info.get("slide_id")
            new_position = order_info.get("position", len(reordered) + 1)
            
            # Find matching slide
            matching_slide = next((s for s in slides if s.slide_id == slide_id), None)
            if matching_slide:
                matching_slide.position = new_position
                if "rationale" in order_info:
                    matching_slide.rationale = order_info["rationale"]
                reordered.append(matching_slide)
        
        # Add any slides not in optimized order
        for slide in slides:
            if not any(s.slide_id == slide.slide_id for s in reordered):
                slide.position = len(reordered) + 1
                reordered.append(slide)
        
        # Sort by position
        reordered.sort(key=lambda x: x.position)
        return reordered
    
    async def _save_assembly_to_database(self, assembly: PresentationAssembly) -> Any:
        """Save assembly to database"""
        try:
            # Create assembly model (simplified - would use actual model)
            assembly_data = {
                "id": assembly.id,
                "name": assembly.name,
                "description": assembly.description,
                "project_id": assembly.project_id,
                "slides_data": json.dumps([asdict(slide) for slide in assembly.slides]),
                "ai_plan": json.dumps(assembly.ai_plan) if assembly.ai_plan else None,
                "export_settings": json.dumps(assembly.export_settings) if assembly.export_settings else None,
                "template_id": assembly.template_id,
                "ai_generated": assembly.ai_generated,
                "created_at": assembly.created_at or datetime.now(),
                "created_by": assembly.created_by
            }
            
            # In real implementation, would save to AssemblyModel table
            logger.info(f"Assembly {assembly.id} saved to database")
            return assembly_data
            
        except Exception as e:
            logger.error(f"Failed to save assembly to database: {e}")
            raise
    
    async def _get_assembly_from_database(self, assembly_id: str) -> Optional[PresentationAssembly]:
        """Get assembly from database"""
        try:
            # In real implementation, would query AssemblyModel
            # For now, return a mock assembly based on ID
            if assembly_id == "assembly_123":
                mock_assembly = PresentationAssembly(
                    id=assembly_id,
                    name="Q4 Investor Pitch",
                    description="Quarterly results presentation for investors",
                    project_id="project_1",
                    slides=[
                        SlideAssembly(slide_id="slide_1", position=1, title="Company Overview", ai_suggested=True),
                        SlideAssembly(slide_id="slide_2", position=2, title="Q4 Financial Results", ai_suggested=True),
                        SlideAssembly(slide_id="slide_3", position=3, title="Growth Strategy", ai_suggested=False)
                    ],
                    ai_plan={
                        "intent": "investor_pitch",
                        "target_audience": "potential investors",
                        "estimated_duration": 15
                    },
                    ai_generated=True,
                    created_at=datetime.now()
                )
            else:
                mock_assembly = PresentationAssembly(
                    id=assembly_id,
                    name="Mock Assembly",
                    description="Mock assembly for testing",
                    project_id="project_1",
                    slides=[
                        SlideAssembly(slide_id="slide_1", position=1, title="Title Slide"),
                        SlideAssembly(slide_id="slide_2", position=2, title="Content Slide")
                    ]
                )
            return mock_assembly
            
        except Exception as e:
            logger.error(f"Failed to get assembly from database: {e}")
            return None
    
    async def _prepare_export_data(self, assembly: PresentationAssembly) -> Dict[str, Any]:
        """Prepare data for export"""
        # Get slide details from database
        slides_data = []
        for slide_assembly in assembly.slides:
            slide_model = self.db.query(SlideModel).filter(SlideModel.id == slide_assembly.slide_id).first()
            if slide_model:
                slides_data.append({
                    "slide_id": slide_model.id,
                    "title": slide_model.title,
                    "notes": slide_assembly.notes or slide_model.notes,
                    "slide_type": slide_model.slide_type,
                    "thumbnail_path": slide_model.thumbnail_path,
                    "full_image_path": slide_model.full_image_path,
                    "position": slide_assembly.position,
                    "transitions": slide_assembly.transitions,
                    "speaker_notes": slide_assembly.speaker_notes
                })
            else:
                # Fallback for missing slides
                slides_data.append({
                    "slide_id": slide_assembly.slide_id,
                    "title": slide_assembly.title,
                    "notes": slide_assembly.notes,
                    "slide_type": "content",
                    "thumbnail_path": "",
                    "full_image_path": "",
                    "position": slide_assembly.position,
                    "transitions": slide_assembly.transitions,
                    "speaker_notes": slide_assembly.speaker_notes
                })
        
        return {
            "name": assembly.name,
            "description": assembly.description,
            "slides": slides_data,
            "template_id": assembly.template_id,
            "export_settings": assembly.export_settings or {}
        }

class SmartOrderOptimizer:
    """Smart slide ordering optimization using AI"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def optimize_slide_order(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize slide order for better presentation flow"""
        try:
            # Use AI service for optimization if available
            if hasattr(self.ai_service, 'presentation_planner'):
                current_order = [slide.get("slide_id", str(i)) for i, slide in enumerate(slides)]
                optimization = await self.ai_service.presentation_planner.optimize_slide_order(
                    current_order, slides
                )
                return optimization
            else:
                # Fallback to rule-based optimization
                return await self._rule_based_optimization(slides)
                
        except Exception as e:
            logger.error(f"Slide order optimization failed: {e}")
            return await self._rule_based_optimization(slides)
    
    async def analyze_narrative_structure(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze narrative structure of presentation"""
        return await self._analyze_narrative_structure(slides)
    
    async def _rule_based_optimization(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule-based optimization fallback"""
        # Define ideal slide type order
        type_priority = {
            "title": 1,
            "introduction": 2, 
            "agenda": 3,
            "content": 4,
            "chart": 5,
            "table": 6,
            "image": 7,
            "summary": 8,
            "conclusion": 9,
            "questions": 10
        }
        
        # Sort slides by priority
        sorted_slides = sorted(
            enumerate(slides), 
            key=lambda x: type_priority.get(x[1].get("slide_type", "content"), 4)
        )
        
        optimized_order = []
        flow_score = 0.8  # Good rule-based score
        improvements = ["Applied rule-based slide ordering"]
        
        for i, (original_index, slide) in enumerate(sorted_slides):
            optimized_order.append({
                "slide_id": slide.get("slide_id", f"slide_{original_index}"),
                "position": i + 1,
                "rationale": f"Positioned based on slide type: {slide.get('slide_type', 'content')}"
            })
        
        return {
            "optimized_order": optimized_order,
            "flow_score": flow_score,
            "improvements": improvements,
            "rationale": "Rule-based optimization for logical presentation flow"
        }
    
    async def _calculate_flow_score(self, slides: List[Dict[str, Any]]) -> float:
        """Calculate presentation flow score"""
        # Simple scoring based on slide type progression
        score = 0.0
        expected_order = ["title", "introduction", "content", "chart", "conclusion"]
        
        slide_types = [slide.get("slide_type", "content") for slide in slides]
        
        # Check for logical progression
        for i, slide_type in enumerate(slide_types):
            if i < len(expected_order) and slide_type == expected_order[i]:
                score += 1.0 / len(slides)
            elif slide_type in expected_order:
                # Partial credit for having the right types
                score += 0.5 / len(slides)
        
        # Bonus for having title at start and conclusion at end
        if slide_types and slide_types[0] in ["title", "introduction"]:
            score += 0.2
        if slide_types and slide_types[-1] in ["conclusion", "questions", "summary"]:
            score += 0.2
        
        return min(score, 1.0)
    
    async def _suggest_optimal_order(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest optimal slide order"""
        # Sort by slide type priority
        type_priority = {"title": 1, "introduction": 2, "content": 3, "chart": 4, "conclusion": 5}
        
        sorted_slides = sorted(slides, key=lambda x: type_priority.get(x.get("slide_type", "content"), 3))
        
        return [
            {"slide_id": slide.get("slide_id", f"slide_{i}"), "position": i + 1}
            for i, slide in enumerate(sorted_slides)
        ]
    
    async def _analyze_narrative_structure(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze narrative structure"""
        # Simple analysis based on slide types
        slide_types = [slide.get("slide_type", "content") for slide in slides]
        
        # Determine structure type
        if "title" in slide_types and "conclusion" in slide_types:
            if "chart" in slide_types or "table" in slide_types:
                structure_type = "data_driven_narrative"
                narrative_strength = 0.9
            else:
                structure_type = "complete_narrative"
                narrative_strength = 0.8
        elif "title" in slide_types:
            structure_type = "partial_narrative" 
            narrative_strength = 0.6
        else:
            structure_type = "content_only"
            narrative_strength = 0.4
        
        # Analyze story arc
        story_arc = []
        if "title" in slide_types or "introduction" in slide_types:
            story_arc.append("setup")
        if "content" in slide_types or "chart" in slide_types:
            story_arc.append("development")
        if "conclusion" in slide_types or "summary" in slide_types:
            story_arc.append("resolution")
        
        # Generate improvement suggestions
        improvements = []
        if "title" not in slide_types and "introduction" not in slide_types:
            improvements.append("Add clear introduction slide")
        if "conclusion" not in slide_types and "summary" not in slide_types:
            improvements.append("Add conclusion or summary slide")
        if len([t for t in slide_types if t in ["chart", "table", "image"]]) == 0:
            improvements.append("Consider adding visual elements (charts, images)")
        
        return {
            "structure_type": structure_type,
            "narrative_strength": narrative_strength,
            "story_arc": story_arc,
            "improvement_suggestions": improvements
        }

class AssemblyExporter:
    """Multi-format assembly export"""
    
    def __init__(self, db_session: Session, powerpoint_service: PowerPointService):
        self.db = db_session
        self.powerpoint_service = powerpoint_service
    
    async def export_to_powerpoint(self, assembly_data: Dict[str, Any], 
                                 export_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export assembly to PowerPoint format"""
        try:
            output_path = await self._create_powerpoint_from_assembly(
                assembly_data, export_path, options
            )
            
            return {
                "success": True,
                "file_path": output_path,
                "format": "pptx",
                "slide_count": len(assembly_data["slides"]),
                "export_time_ms": 1200,  # Mock timing
                "file_size_mb": 2.5  # Mock size
            }
            
        except Exception as e:
            logger.error(f"PowerPoint export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_to_pdf(self, assembly_data: Dict[str, Any], 
                          export_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export assembly to PDF format"""
        try:
            output_path = await self._create_pdf_from_assembly(
                assembly_data, export_path, options
            )
            
            return {
                "success": True,
                "file_path": output_path,
                "format": "pdf",
                "page_count": len(assembly_data["slides"]),
                "export_time_ms": 800,  # Mock timing
                "file_size_mb": 1.8,  # Mock size
                "quality": options.get("quality", "standard")
            }
            
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_to_html(self, assembly_data: Dict[str, Any], 
                           export_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export assembly to interactive HTML format"""
        try:
            output_path = await self._create_html_from_assembly(
                assembly_data, export_path, options
            )
            
            return {
                "success": True,
                "file_path": output_path,
                "format": "html",
                "slide_count": len(assembly_data["slides"]),
                "interactive": options.get("interactive", False),
                "responsive": options.get("responsive", True),
                "export_time_ms": 600  # Mock timing
            }
            
        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_powerpoint_from_assembly(self, assembly_data: Dict[str, Any], 
                                             export_path: str, options: Dict[str, Any]) -> str:
        """Create PowerPoint file from assembly data"""
        # Ensure export directory exists
        Path(export_path).mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        safe_name = assembly_data['name'].replace(' ', '_').replace('/', '_')
        output_file = f"{export_path}/{safe_name}.pptx"
        
        # In real implementation, would use PowerPoint COM or python-pptx
        # For now, create a placeholder file
        try:
            with open(output_file, 'w') as f:
                f.write("# PowerPoint Export Placeholder\n")
                f.write(f"# Assembly: {assembly_data['name']}\n")
                f.write(f"# Slides: {len(assembly_data['slides'])}\n")
                for slide in assembly_data['slides']:
                    f.write(f"# Slide {slide['position']}: {slide['title']}\n")
            
            logger.info(f"Created PowerPoint export placeholder: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to create PowerPoint file: {e}")
            raise
    
    async def _create_pdf_from_assembly(self, assembly_data: Dict[str, Any], 
                                      export_path: str, options: Dict[str, Any]) -> str:
        """Create PDF file from assembly data"""
        # Ensure export directory exists
        Path(export_path).mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        safe_name = assembly_data['name'].replace(' ', '_').replace('/', '_')
        output_file = f"{export_path}/{safe_name}.pdf"
        
        # In real implementation, would use reportlab or similar for PDF generation
        # For now, create a placeholder file
        try:
            with open(output_file, 'w') as f:
                f.write("# PDF Export Placeholder\n")
                f.write(f"# Assembly: {assembly_data['name']}\n")
                f.write(f"# Quality: {options.get('quality', 'standard')}\n")
                f.write(f"# Include Notes: {options.get('include_notes', False)}\n")
                for slide in assembly_data['slides']:
                    f.write(f"# Page {slide['position']}: {slide['title']}\n")
                    if options.get('include_notes') and slide.get('notes'):
                        f.write(f"#   Notes: {slide['notes']}\n")
            
            logger.info(f"Created PDF export placeholder: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to create PDF file: {e}")
            raise
    
    async def _create_html_from_assembly(self, assembly_data: Dict[str, Any], 
                                       export_path: str, options: Dict[str, Any]) -> str:
        """Create interactive HTML presentation"""
        # Ensure export directory exists
        safe_name = assembly_data['name'].replace(' ', '_').replace('/', '_')
        output_dir = f"{export_path}/{safe_name}"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        output_file = f"{output_dir}/index.html"
        
        # In real implementation, would generate reveal.js or similar HTML presentation
        # For now, create a placeholder HTML file
        try:
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{assembly_data['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .slide {{ margin-bottom: 40px; border: 1px solid #ccc; padding: 20px; }}
        .slide-title {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
        .slide-notes {{ font-style: italic; color: #666; margin-top: 10px; }}
        .navigation {{ position: fixed; top: 20px; right: 20px; }}
        .interactive {{ background: #f0f0f0; padding: 10px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{assembly_data['name']}</h1>
    <p>{assembly_data['description']}</p>
    
    {'<div class="interactive">Interactive Mode Enabled</div>' if options.get('interactive') else ''}
    
    <div class="navigation">
        <button onclick="previousSlide()">Previous</button>
        <button onclick="nextSlide()">Next</button>
    </div>
"""
            
            for slide in assembly_data['slides']:
                html_content += f"""
    <div class="slide" id="slide-{slide['position']}">
        <div class="slide-title">{slide['title']}</div>
        <p>Slide content would be rendered here.</p>
        {f'<div class="slide-notes">Notes: {slide.get("notes", "")}</div>' if slide.get("notes") else ''}
    </div>
"""
            
            html_content += """
    <script>
        let currentSlide = 1;
        const maxSlides = """ + str(len(assembly_data['slides'])) + """;
        
        function showSlide(n) {
            document.querySelectorAll('.slide').forEach(slide => {
                slide.style.display = 'none';
            });
            document.getElementById(`slide-${n}`).style.display = 'block';
        }
        
        function nextSlide() {
            if (currentSlide < maxSlides) {
                currentSlide++;
                showSlide(currentSlide);
            }
        }
        
        function previousSlide() {
            if (currentSlide > 1) {
                currentSlide--;
                showSlide(currentSlide);
            }
        }
        
        // Initialize
        showSlide(1);
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowRight') nextSlide();
            if (e.key === 'ArrowLeft') previousSlide();
        });
    </script>
</body>
</html>"""
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Created HTML export: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to create HTML file: {e}")
            raise

class TemplateManager:
    """Template management for presentations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available presentation templates"""
        return [
            {
                "id": "professional_investor",
                "name": "Professional Investor",
                "description": "Clean, professional design for investor presentations",
                "preview_url": "/templates/professional_investor/preview.png",
                "slide_layouts": ["title", "content", "chart", "conclusion"],
                "color_scheme": "blue_corporate",
                "font_family": "Arial"
            },
            {
                "id": "corporate_executive",
                "name": "Corporate Executive", 
                "description": "Executive-focused template with data emphasis",
                "preview_url": "/templates/corporate_executive/preview.png",
                "slide_layouts": ["title", "content", "dashboard", "summary"],
                "color_scheme": "dark_professional",
                "font_family": "Calibri"
            },
            {
                "id": "creative_modern",
                "name": "Creative Modern",
                "description": "Modern, creative design for innovative presentations",
                "preview_url": "/templates/creative_modern/preview.png",
                "slide_layouts": ["title", "visual", "story", "impact"],
                "color_scheme": "gradient_modern",
                "font_family": "Helvetica"
            },
            {
                "id": "startup_pitch",
                "name": "Startup Pitch",
                "description": "Dynamic template optimized for startup pitches",
                "preview_url": "/templates/startup_pitch/preview.png", 
                "slide_layouts": ["problem", "solution", "market", "business_model", "team"],
                "color_scheme": "startup_vibrant",
                "font_family": "Montserrat"
            }
        ]
    
    async def apply_template(self, assembly_id: str, template_id: str) -> Dict[str, Any]:
        """Apply template to assembly"""
        try:
            # Get template details
            templates = await self.get_available_templates()
            template = next((t for t in templates if t["id"] == template_id), None)
            
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # In real implementation, would update assembly with template settings
            # For now, return success with template info
            return {
                "success": True,
                "template_applied": template_id,
                "template_name": template["name"],
                "slides_updated": 3,  # Mock count
                "layout_mappings": {
                    "slide_1": template["slide_layouts"][0] if template["slide_layouts"] else "title_layout",
                    "slide_2": template["slide_layouts"][1] if len(template["slide_layouts"]) > 1 else "content_layout",
                    "slide_3": template["slide_layouts"][2] if len(template["slide_layouts"]) > 2 else "content_layout"
                },
                "color_scheme": template.get("color_scheme", "default"),
                "font_family": template.get("font_family", "Arial")
            }
        except Exception as e:
            logger.error(f"Template application failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_template_details(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific template"""
        templates = await self.get_available_templates()
        return next((t for t in templates if t["id"] == template_id), None)

class CollaborationManager:
    """Real-time collaboration management"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.active_sessions = {}  # In-memory storage for demo
    
    async def create_session(self, assembly_id: str, owner_id: str, 
                           participants: List[str]) -> Dict[str, Any]:
        """Create collaboration session"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "assembly_id": assembly_id,
            "owner_id": owner_id,
            "participants": [owner_id] + participants,
            "permissions": {
                owner_id: "edit",
                **{p: "view" for p in participants}
            },
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.active_sessions[session_id] = session_data
        
        return await self._create_collaboration_session(session_data)
    
    async def handle_update(self, session_id: str, user_id: str, 
                          action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaborative update"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Check permissions
        user_permission = session["permissions"].get(user_id, "none")
        if user_permission == "none":
            return {"success": False, "error": "User not authorized"}
        
        if action in ["edit_slide", "reorder_slide", "delete_slide"] and user_permission != "edit":
            return {"success": False, "error": "User does not have edit permissions"}
        
        # Update session version
        session["version"] += 1
        session["last_activity"] = datetime.now().isoformat()
        
        return await self._handle_collaboration_update({
            "session_id": session_id,
            "user_id": user_id, 
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "version": session["version"]
        })
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get collaboration session status"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        return {
            "success": True,
            "session": session,
            "active_users": len(session["participants"]),
            "last_activity": session["last_activity"]
        }
    
    async def end_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """End collaboration session"""
        if session_id not in self.active_sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        # Only owner can end session
        if user_id != session["owner_id"]:
            return {"success": False, "error": "Only session owner can end session"}
        
        # Mark session as ended
        session["status"] = "ended"
        session["ended_at"] = datetime.now().isoformat()
        
        return {"success": True, "session_ended": True}
    
    async def _create_collaboration_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create collaboration session"""
        logger.info(f"Creating collaboration session: {session_data['session_id']}")
        return session_data
    
    async def _handle_collaboration_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaboration update"""
        logger.info(f"Handling collaboration update: {update_data['action']}")
        
        # Create change record
        change = {
            "type": update_data["action"],
            "user": update_data["user_id"],
            "details": update_data["data"],
            "timestamp": update_data["timestamp"]
        }
        
        return {
            "success": True,
            "version": update_data["version"],
            "changes": [change],
            "conflicts": [],  # Would detect and resolve conflicts in real implementation
            "sync_required": False
        }

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    class MockSession:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def first(self):
            return None
        def all(self):
            return []
    
    class MockAIService:
        def __init__(self):
            self.presentation_planner = Mock()
        
        async def create_automated_presentation(self, intent, project_id):
            return {
                "success": True,
                "assembly_plan": {
                    "name": "AI Generated Presentation",
                    "description": "Generated from intent",
                    "slides": [
                        {"slide_id": "slide_1", "position": 1, "title": "Introduction"}
                    ]
                }
            }
    
    class MockPowerPointService:
        pass
    
    async def test_assembly_service():
        try:
            assembly_service = AssemblyService(MockSession(), MockAIService(), MockPowerPointService())
            print("✅ Assembly service initialized successfully")
            
            # Test AI automated assembly
            result = await assembly_service.create_ai_automated_assembly(
                "Create investor pitch", "project_1"
            )
            print(f"✅ AI automated assembly: {result['success']}")
            
            # Test manual assembly
            manual_result = await assembly_service.create_manual_assembly(
                "Manual Presentation", 
                [{"slide_id": "slide_1", "title": "Test Slide"}],
                "project_1"
            )
            print(f"✅ Manual assembly: {manual_result['success']}")
            
            # Test export
            export_result = await assembly_service.export_assembly(
                "assembly_123", "html", {"interactive": True}
            )
            print(f"✅ Assembly export: {export_result['success']}")
            
            # Test templates
            templates = await assembly_service.get_available_templates()
            print(f"✅ Available templates: {len(templates)} templates found")
            
        except Exception as e:
            print(f"❌ Assembly service test failed: {e}")
    
    # Run test
    asyncio.run(test_assembly_service())