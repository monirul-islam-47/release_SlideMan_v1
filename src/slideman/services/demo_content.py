# src/slideman/services/demo_content.py

import logging
import json
from pathlib import Path
from typing import Optional, Dict, List
from ..models.project import Project
from ..models.slide import Slide
from ..models.keyword import Keyword

logger = logging.getLogger(__name__)

class DemoContentService:
    """Service for creating demo content and sample projects."""
    
    def __init__(self, db_service):
        self.db = db_service
        self.logger = logging.getLogger(__name__)
        
    def create_demo_project(self) -> Optional[int]:
        """
        Create a demo project with sample slides and keywords.
        
        Returns:
            Project ID if successful, None otherwise
        """
        try:
            self.logger.info("Creating demo project with sample content")
            
            # Create demo project
            project_name = "🎯 SlideMan Demo Project"
            demo_folder = Path.home() / "Documents" / "SlidemanProjects" / "Demo"
            demo_folder.mkdir(parents=True, exist_ok=True)
            
            project_id = self.db.add_project(project_name, str(demo_folder))
            if not project_id:
                self.logger.error("Failed to create demo project in database")
                return None
                
            # Create sample "file" entry (even though no actual PPTX exists)
            file_id = self.db.add_file(
                project_id, 
                "sample_presentation.pptx", 
                "sample_presentation.pptx", 
                "demo_checksum"
            )
            
            if not file_id:
                self.logger.error("Failed to create demo file in database")
                return None
                
            # Create sample slides with diverse content
            sample_slides = self._get_sample_slide_data()
            
            for slide_data in sample_slides:
                slide_id = self.db.add_slide(
                    file_id,
                    slide_data["slide_number"],
                    slide_data["title"],
                    slide_data["notes"],
                    "demo_thumbnail_path.png"  # Placeholder path
                )
                
                if slide_id:
                    # Add sample keywords to slides
                    for keyword_text in slide_data.get("keywords", []):
                        keyword_id = self.db.get_or_create_keyword(keyword_text)
                        if keyword_id:
                            self.db.add_slide_keyword(slide_id, keyword_id)
                            
            self.logger.info(f"Demo project created successfully with ID {project_id}")
            return project_id
            
        except Exception as e:
            self.logger.error(f"Failed to create demo project: {e}", exc_info=True)
            return None
    
    def _get_sample_slide_data(self) -> List[Dict]:
        """Get sample slide data for the demo project."""
        return [
            {
                "slide_number": 1,
                "title": "Welcome to SlideMan Demo",
                "notes": "This is a sample presentation to demonstrate SlideMan's features. You can tag slides, search content, and build new presentations from existing slides.",
                "keywords": ["Welcome", "Demo", "Introduction"]
            },
            {
                "slide_number": 2,
                "title": "Q1 2024 Sales Results",
                "notes": "Strong performance in Q1 with 25% growth over previous quarter. Key wins in enterprise accounts.",
                "keywords": ["Sales", "Q1", "2024", "Results", "Growth"]
            },
            {
                "slide_number": 3,
                "title": "Product Roadmap Overview",
                "notes": "Upcoming features planned for release in Q2 and Q3. Focus on user experience and performance improvements.",
                "keywords": ["Product", "Roadmap", "Features", "Development"]
            },
            {
                "slide_number": 4,
                "title": "Market Analysis - Competitive Landscape",
                "notes": "Analysis of key competitors and market positioning. Opportunities identified in emerging markets.",
                "keywords": ["Market", "Analysis", "Competition", "Strategy"]
            },
            {
                "slide_number": 5,
                "title": "Financial Summary - Budget vs Actual",
                "notes": "Budget performance review showing strong cost control and revenue growth. On track for annual targets.",
                "keywords": ["Finance", "Budget", "Actual", "Performance"]
            },
            {
                "slide_number": 6,
                "title": "Team Performance Metrics",
                "notes": "Team productivity metrics and KPI achievements. Recognition of top performers and areas for improvement.",
                "keywords": ["Team", "Performance", "Metrics", "KPI"]
            },
            {
                "slide_number": 7,
                "title": "Customer Feedback & Satisfaction",
                "notes": "Customer satisfaction scores improved to 4.2/5. Key feedback themes include ease of use and reliability.",
                "keywords": ["Customer", "Feedback", "Satisfaction", "Survey"]
            },
            {
                "slide_number": 8,
                "title": "Technology Infrastructure Update",
                "notes": "Infrastructure upgrades completed successfully. Improved system reliability and faster response times.",
                "keywords": ["Technology", "Infrastructure", "System", "Performance"]
            },
            {
                "slide_number": 9,
                "title": "Marketing Campaign Results",
                "notes": "Digital marketing campaigns showed strong ROI. Social media engagement up 40% quarter over quarter.",
                "keywords": ["Marketing", "Campaign", "ROI", "Digital", "Social Media"]
            },
            {
                "slide_number": 10,
                "title": "Next Steps & Action Items",
                "notes": "Summary of key action items and next steps. Timeline for Q2 initiatives and responsible parties assigned.",
                "keywords": ["Action Items", "Next Steps", "Timeline", "Q2"]
            }
        ]
    
    def has_demo_project(self) -> bool:
        """Check if a demo project already exists."""
        try:
            projects = self.db.get_all_projects()
            return any("SlideMan Demo Project" in project.name for project in projects)
        except Exception as e:
            self.logger.error(f"Error checking for existing demo project: {e}")
            return False
    
    def get_sample_keywords(self) -> List[str]:
        """Get a list of commonly used sample keywords for auto-complete."""
        return [
            "Sales", "Marketing", "Finance", "Product", "Strategy",
            "Q1", "Q2", "Q3", "Q4", "2024", "2025",
            "Results", "Performance", "Growth", "Revenue",
            "Customer", "Team", "Technology", "Infrastructure",
            "Budget", "Analysis", "Competition", "Market",
            "Demo", "Welcome", "Introduction", "Overview",
            "ROI", "KPI", "Metrics", "Feedback", "Survey"
        ]
    
    def populate_sample_keywords(self):
        """Pre-populate the database with sample keywords for better UX."""
        try:
            sample_keywords = self.get_sample_keywords()
            for keyword_text in sample_keywords:
                self.db.get_or_create_keyword(keyword_text)
            self.logger.info(f"Pre-populated {len(sample_keywords)} sample keywords")
        except Exception as e:
            self.logger.error(f"Failed to populate sample keywords: {e}", exc_info=True)