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
        """Set up the sophisticated base layout for empty states."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(32)  # Sophisticated spacing
        self.main_layout.setContentsMargins(64, 64, 64, 64)  # Generous professional margins
        
    def _add_icon(self, icon_text: str, size: int = 48):
        """Add a sophisticated icon to the empty state."""
        icon_label = QLabel(icon_text)
        icon_font = QFont()
        icon_font.setPointSize(size)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: #667eea; margin-bottom: 8px;")  # Purple accent color
        self.main_layout.addWidget(icon_label)
        return icon_label
        
    def _add_title(self, title: str):
        """Add a sophisticated title to the empty state."""
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(24)  # Larger, more impressive
        title_font.setWeight(QFont.Weight.DemiBold)  # Professional weight
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #1f2937; margin-bottom: 16px;")  # Professional dark gray
        self.main_layout.addWidget(title_label)
        return title_label
        
    def _add_description(self, description: str):
        """Add a sophisticated description to the empty state."""
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #6b7280;
            font-size: 16px;
            font-weight: 400;
            line-height: 1.6;
            max-width: 480px;
            margin-bottom: 8px;
        """)
        self.main_layout.addWidget(desc_label)
        return desc_label
        
    def _add_primary_button(self, text: str, tooltip: str = "") -> QPushButton:
        """Add a sophisticated primary action button."""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 16px 32px;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                min-width: 160px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a67d8, stop:1 #6b73ff);
                transform: translateY(-1px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4c51bf, stop:1 #553c9a);
                transform: translateY(0px);
            }
        """)
        self.main_layout.addWidget(button, alignment=Qt.AlignCenter)
        return button
        
    def _add_secondary_button(self, text: str, tooltip: str = "") -> QPushButton:
        """Add a sophisticated secondary action button."""
        button = QPushButton(text)
        if tooltip:
            button.setToolTip(tooltip)
        button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #374151;
                padding: 14px 28px;
                font-size: 14px;
                font-weight: 500;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #f9fafb;
                color: #1f2937;
                border-color: #9ca3af;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }
            QPushButton:pressed {
                background-color: #f3f4f6;
                transform: translateY(0px);
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