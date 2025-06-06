# src/slideman/ui/components/empty_states.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
import logging

class EmptyStateWidget(QWidget):
    """Base class for empty state widgets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._setup_base_layout()
        
    def _setup_base_layout(self):
        """Set up the base layout for empty states."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        
    def _add_icon(self, icon_text: str, size: int = 48):
        """Add an icon to the empty state."""
        icon_label = QLabel(icon_text)
        icon_font = QFont()
        icon_font.setPointSize(size)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: #95a5a6;")
        self.main_layout.addWidget(icon_label)
        return icon_label
        
    def _add_title(self, title: str):
        """Add a title to the empty state."""
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        self.main_layout.addWidget(title_label)
        return title_label
        
    def _add_description(self, description: str):
        """Add a description to the empty state."""
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 14px;
            line-height: 1.4;
            max-width: 400px;
        """)
        self.main_layout.addWidget(desc_label)
        return desc_label
        
    def _add_primary_button(self, text: str, tooltip: str = "") -> QPushButton:
        """Add a primary action button."""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.main_layout.addWidget(button, alignment=Qt.AlignCenter)
        return button
        
    def _add_secondary_button(self, text: str, tooltip: str = "") -> QPushButton:
        """Add a secondary action button."""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                padding: 8px 16px;
                font-size: 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                color: #2c3e50;
                border-color: #95a5a6;
            }
        """)
        self.main_layout.addWidget(button, alignment=Qt.AlignCenter)
        return button


class NoProjectsEmptyState(EmptyStateWidget):
    """Empty state for when no projects exist."""
    
    createProjectRequested = Signal()
    importDemoRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the no projects empty state UI."""
        # Icon
        self._add_icon("📁", 56)
        
        # Title
        self._add_title("Welcome to SlideMan!")
        
        # Description
        self._add_description(
            "You don't have any projects yet. Create your first project to start "
            "organizing your PowerPoint slides with tags and build presentations faster."
        )
        
        # Spacer
        self.main_layout.addSpacing(10)
        
        # Primary action
        self.create_btn = self._add_primary_button(
            "🚀 Create First Project",
            "Create a new project and import PowerPoint files"
        )
        
        # Secondary action
        self.demo_btn = self._add_secondary_button(
            "🔍 Load Demo Project",
            "Explore SlideMan with sample data"
        )
        
        # Connect signals
        self.create_btn.clicked.connect(self.createProjectRequested.emit)
        self.demo_btn.clicked.connect(self.importDemoRequested.emit)


class NoSlidesEmptyState(EmptyStateWidget):
    """Empty state for when no slides exist in a project."""
    
    importSlidesRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the no slides empty state UI."""
        # Icon
        self._add_icon("🎞️", 56)
        
        # Title
        self._add_title("No Slides Yet")
        
        # Description
        self._add_description(
            "This project doesn't contain any slides. Import PowerPoint files "
            "to start building your slide library."
        )
        
        # Spacer
        self.main_layout.addSpacing(10)
        
        # Primary action
        self.import_btn = self._add_primary_button(
            "📁 Import PowerPoint Files",
            "Add PPTX files to this project"
        )
        
        # Connect signals
        self.import_btn.clicked.connect(self.importSlidesRequested.emit)


class NoSearchResultsEmptyState(EmptyStateWidget):
    """Empty state for when search returns no results."""
    
    clearSearchRequested = Signal()
    modifySearchRequested = Signal()
    
    def __init__(self, search_query: str = "", parent=None):
        self.search_query = search_query
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the no search results empty state UI."""
        # Icon
        self._add_icon("🔍", 56)
        
        # Title
        if self.search_query:
            title = f"No results for '{self.search_query}'"
        else:
            title = "No search results"
        self._add_title(title)
        
        # Description
        self._add_description(
            "Try adjusting your search terms, checking for typos, or using different keywords. "
            "You can also browse all slides or try a broader search."
        )
        
        # Spacer
        self.main_layout.addSpacing(10)
        
        # Primary action
        self.clear_btn = self._add_primary_button(
            "🔄 Clear Search",
            "Show all slides"
        )
        
        # Secondary action
        self.modify_btn = self._add_secondary_button(
            "✏️ Modify Search",
            "Try different search terms"
        )
        
        # Connect signals
        self.clear_btn.clicked.connect(self.clearSearchRequested.emit)
        self.modify_btn.clicked.connect(self.modifySearchRequested.emit)
        
    def update_search_query(self, query: str):
        """Update the search query and refresh the UI."""
        self.search_query = query
        # Find and update the title label
        for i in range(self.main_layout.count()):
            widget = self.main_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and hasattr(widget, 'font'):
                font = widget.font()
                if font.bold() and font.pointSize() == 18:
                    # This is the title label
                    if query:
                        widget.setText(f"No results for '{query}'")
                    else:
                        widget.setText("No search results")
                    break


class NoKeywordsEmptyState(EmptyStateWidget):
    """Empty state for when no keywords exist."""
    
    createKeywordRequested = Signal()
    learnMoreRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the no keywords empty state UI."""
        # Icon
        self._add_icon("🏷️", 56)
        
        # Title
        self._add_title("No Keywords Yet")
        
        # Description
        self._add_description(
            "Keywords help you organize and find slides quickly. Start by adding "
            "keywords to your slides to create a searchable library."
        )
        
        # Spacer
        self.main_layout.addSpacing(10)
        
        # Benefits section
        benefits_frame = QFrame()
        benefits_layout = QVBoxLayout(benefits_frame)
        benefits_layout.setSpacing(8)
        
        benefits = [
            "🎯 Find slides instantly",
            "📊 Group related content",
            "🔄 Reuse slides across projects",
            "⚡ Build presentations faster"
        ]
        
        for benefit in benefits:
            benefit_label = QLabel(benefit)
            benefit_label.setStyleSheet("color: #27ae60; font-size: 12px;")
            benefits_layout.addWidget(benefit_label)
            
        self.main_layout.addWidget(benefits_frame, alignment=Qt.AlignCenter)
        self.main_layout.addSpacing(10)
        
        # Primary action
        self.create_btn = self._add_primary_button(
            "🏷️ Tag Your First Slide",
            "Go to SlideView to start tagging"
        )
        
        # Secondary action
        self.learn_btn = self._add_secondary_button(
            "💡 Learn About Keywords",
            "Understand how keywords work"
        )
        
        # Connect signals
        self.create_btn.clicked.connect(self.createKeywordRequested.emit)
        self.learn_btn.clicked.connect(self.learnMoreRequested.emit)


class LoadingState(QWidget):
    """Loading state widget with progress indication."""
    
    def __init__(self, message: str = "Loading...", parent=None):
        super().__init__(parent)
        self.message = message
        self.logger = logging.getLogger(__name__)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the loading state UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Loading animation (using text for now)
        self.spinner_label = QLabel("⏳")
        spinner_font = QFont()
        spinner_font.setPointSize(32)
        self.spinner_label.setFont(spinner_font)
        self.spinner_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinner_label)
        
        # Loading message
        self.message_label = QLabel(self.message)
        message_font = QFont()
        message_font.setPointSize(14)
        self.message_label.setFont(message_font)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.message_label)
        
    def update_message(self, message: str):
        """Update the loading message."""
        self.message = message
        self.message_label.setText(message)