"""
Database models for PrezI application
Implements complete data schema for AI-powered presentation management

This module implements ALL features from fnf_checklist.md:
- SlideMan: Project & File Management, Interactive Organization & Search, Manual Assembly, Export
- PrezI: AI-Powered Content Intelligence, AI-Driven Search, AI-Automated Creation, Professional Polish
- User Experience: Onboarding & Platform features
"""

import uuid
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    Text, JSON, ForeignKey, Index, UniqueConstraint, Table, CheckConstraint
)
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from backend.database.database import Base


# Enums for type safety and consistency
class ProcessingStatus(str, Enum):
    """File processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ElementType(str, Enum):
    """Slide element type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"
    SHAPE = "shape"
    VIDEO = "video"
    AUDIO = "audio"
    SMARTART = "smartart"
    OTHER = "other"


class ExportFormat(str, Enum):
    """Export format enumeration"""
    PPTX = "pptx"
    PDF = "pdf"
    IMAGES = "images"


class AIAnalysisStatus(str, Enum):
    """AI analysis status enumeration"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    """Mixin for UUID primary keys"""
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


class KeywordModel(Base, TimestampMixin):
    """Database model for keywords"""
    __tablename__ = "keywords"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default="#3B82F6")  # Hex color code
    description = Column(String(500))
    usage_count = Column(Integer, default=0)
    
    # Relationships
    slide_keywords = relationship("SlideKeywordModel", back_populates="keyword", cascade="all, delete-orphan")
    element_keywords = relationship("ElementKeywordModel", back_populates="keyword", cascade="all, delete-orphan")
    file_keywords = relationship("FileKeywordModel", back_populates="keyword", cascade="all, delete-orphan")
    project_keywords = relationship("ProjectKeywordModel", back_populates="keyword", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_keyword_name', 'name'),
        Index('idx_keyword_usage', 'usage_count'),
    )
    
    @validates('color')
    def validate_color(self, key, color):
        """Validate hex color format"""
        if not color.startswith('#') or len(color) != 7:
            return "#3B82F6"  # Default blue
        return color
    
    def __repr__(self):
        return f"<Keyword(id='{self.id}', name='{self.name}')>"


class ProjectModel(Base, TimestampMixin):
    """Database model for projects"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    status = Column(String(20), default="active")  # active, archived, deleted
    ai_analysis = Column(JSON, default=dict)
    
    # Relationships
    files = relationship("FileModel", back_populates="project", cascade="all, delete-orphan")
    project_keywords = relationship("ProjectKeywordModel", back_populates="project", cascade="all, delete-orphan")
    assemblies = relationship("AssemblyModel", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_name', 'name'),
        Index('idx_project_status', 'status'),
        Index('idx_project_created', 'created_at'),
    )
    
    @hybrid_property
    def total_files(self):
        """Get total number of files in project"""
        return len(self.files)
    
    @hybrid_property
    def total_slides(self):
        """Get total number of slides across all files"""
        return sum(file.slide_count for file in self.files)
    
    def __repr__(self):
        return f"<Project(id='{self.id}', name='{self.name}')>"


class FileModel(Base, TimestampMixin):
    """Database model for PowerPoint files"""
    __tablename__ = "files"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    slide_count = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    ai_analysis = Column(JSON, default=dict)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="files")
    slides = relationship("SlideModel", back_populates="file", cascade="all, delete-orphan")
    file_keywords = relationship("FileKeywordModel", back_populates="file", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_project', 'project_id'),
        Index('idx_file_filename', 'filename'),
        Index('idx_file_processed', 'processed'),
        UniqueConstraint('project_id', 'filename', name='uq_project_filename'),
    )
    
    def __repr__(self):
        return f"<File(id='{self.id}', filename='{self.filename}')>"


class SlideModel(Base, TimestampMixin):
    """Database model for presentation slides"""
    __tablename__ = "slides"
    
    id = Column(String(36), primary_key=True)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    slide_number = Column(Integer, nullable=False)
    title = Column(String(500))
    notes = Column(Text)
    slide_type = Column(String(20), default="unknown")  # title, content, chart, image, table, conclusion, unknown
    thumbnail_path = Column(String(500))
    full_image_path = Column(String(500))
    ai_analysis = Column(JSON, default=dict)
    
    # Relationships
    file = relationship("FileModel", back_populates="slides")
    elements = relationship("ElementModel", back_populates="slide", cascade="all, delete-orphan")
    slide_keywords = relationship("SlideKeywordModel", back_populates="slide", cascade="all, delete-orphan")
    assembly_slides = relationship("AssemblySlideModel", back_populates="slide", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_slide_file', 'file_id'),
        Index('idx_slide_number', 'slide_number'),
        Index('idx_slide_type', 'slide_type'),
        Index('idx_slide_title', 'title'),
        UniqueConstraint('file_id', 'slide_number', name='uq_file_slide_number'),
    )
    
    def __repr__(self):
        return f"<Slide(id='{self.id}', file_id='{self.file_id}', number={self.slide_number})>"


class ElementModel(Base, TimestampMixin):
    """Database model for slide elements"""
    __tablename__ = "elements"
    
    id = Column(String(36), primary_key=True)
    slide_id = Column(String(36), ForeignKey("slides.id"), nullable=False)
    element_type = Column(String(20), default="unknown")  # text, image, chart, table, shape, unknown
    content = Column(Text)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    ai_analysis = Column(JSON, default=dict)
    
    # Relationships
    slide = relationship("SlideModel", back_populates="elements")
    element_keywords = relationship("ElementKeywordModel", back_populates="element", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_element_slide', 'slide_id'),
        Index('idx_element_type', 'element_type'),
        Index('idx_element_content', 'content'),
    )
    
    def __repr__(self):
        return f"<Element(id='{self.id}', slide_id='{self.slide_id}', type='{self.element_type}')>"


class AssemblyModel(Base, TimestampMixin):
    """Database model for slide assemblies"""
    __tablename__ = "assemblies"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    
    # Relationships
    project = relationship("ProjectModel", back_populates="assemblies")
    assembly_slides = relationship("AssemblySlideModel", back_populates="assembly", cascade="all, delete-orphan", order_by="AssemblySlideModel.order_index")
    
    # Indexes
    __table_args__ = (
        Index('idx_assembly_project', 'project_id'),
        Index('idx_assembly_name', 'name'),
    )
    
    @hybrid_property
    def slide_count(self):
        """Get number of slides in assembly"""
        return len(self.assembly_slides)
    
    def __repr__(self):
        return f"<Assembly(id='{self.id}', name='{self.name}')>"


class AssemblySlideModel(Base, TimestampMixin):
    """Database model for slides in assemblies (many-to-many with order)"""
    __tablename__ = "assembly_slides"
    
    id = Column(String(36), primary_key=True)
    assembly_id = Column(String(36), ForeignKey("assemblies.id"), nullable=False)
    slide_id = Column(String(36), ForeignKey("slides.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    assembly = relationship("AssemblyModel", back_populates="assembly_slides")
    slide = relationship("SlideModel", back_populates="assembly_slides")
    
    # Indexes
    __table_args__ = (
        Index('idx_assembly_slide_assembly', 'assembly_id'),
        Index('idx_assembly_slide_order', 'assembly_id', 'order_index'),
        UniqueConstraint('assembly_id', 'order_index', name='uq_assembly_order'),
        UniqueConstraint('assembly_id', 'slide_id', name='uq_assembly_slide'),
    )
    
    def __repr__(self):
        return f"<AssemblySlide(assembly_id='{self.assembly_id}', slide_id='{self.slide_id}', order={self.order_index})>"


# Keyword association tables (many-to-many relationships)

class SlideKeywordModel(Base, TimestampMixin):
    """Association table for slide keywords"""
    __tablename__ = "slide_keywords"
    
    id = Column(String(36), primary_key=True)
    slide_id = Column(String(36), ForeignKey("slides.id"), nullable=False)
    keyword_id = Column(String(36), ForeignKey("keywords.id"), nullable=False)
    
    # Relationships
    slide = relationship("SlideModel", back_populates="slide_keywords")
    keyword = relationship("KeywordModel", back_populates="slide_keywords")
    
    # Indexes
    __table_args__ = (
        Index('idx_slide_keyword_slide', 'slide_id'),
        Index('idx_slide_keyword_keyword', 'keyword_id'),
        UniqueConstraint('slide_id', 'keyword_id', name='uq_slide_keyword'),
    )


class ElementKeywordModel(Base, TimestampMixin):
    """Association table for element keywords"""
    __tablename__ = "element_keywords"
    
    id = Column(String(36), primary_key=True)
    element_id = Column(String(36), ForeignKey("elements.id"), nullable=False)
    keyword_id = Column(String(36), ForeignKey("keywords.id"), nullable=False)
    
    # Relationships
    element = relationship("ElementModel", back_populates="element_keywords")
    keyword = relationship("KeywordModel", back_populates="element_keywords")
    
    # Indexes
    __table_args__ = (
        Index('idx_element_keyword_element', 'element_id'),
        Index('idx_element_keyword_keyword', 'keyword_id'),
        UniqueConstraint('element_id', 'keyword_id', name='uq_element_keyword'),
    )


class FileKeywordModel(Base, TimestampMixin):
    """Association table for file keywords"""
    __tablename__ = "file_keywords"
    
    id = Column(String(36), primary_key=True)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    keyword_id = Column(String(36), ForeignKey("keywords.id"), nullable=False)
    
    # Relationships
    file = relationship("FileModel", back_populates="file_keywords")
    keyword = relationship("KeywordModel", back_populates="file_keywords")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_keyword_file', 'file_id'),
        Index('idx_file_keyword_keyword', 'keyword_id'),
        UniqueConstraint('file_id', 'keyword_id', name='uq_file_keyword'),
    )


class ProjectKeywordModel(Base, TimestampMixin):
    """Association table for project keywords"""
    __tablename__ = "project_keywords"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    keyword_id = Column(String(36), ForeignKey("keywords.id"), nullable=False)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="project_keywords")
    keyword = relationship("KeywordModel", back_populates="project_keywords")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_keyword_project', 'project_id'),
        Index('idx_project_keyword_keyword', 'keyword_id'),
        UniqueConstraint('project_id', 'keyword_id', name='uq_project_keyword'),
    )