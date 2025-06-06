# src/slideman/ui/components/welcome_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QWidget, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
import logging

class WelcomeDialog(QDialog):
    """Welcome dialog shown on first run to introduce users to SlideMan."""
    
    # Signals for different user choices
    startTutorialRequested = Signal()
    importSlidesRequested = Signal()
    loadDemoRequested = Signal()
    skipWelcomeRequested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Welcome to SlideMan")
        self.setFixedSize(700, 500)
        self.setModal(True)
        
        # Remove window decorations for a cleaner look
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the welcome dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create main container with styling
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
            }
        """)
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(25)
        
        # Hero section
        self._create_hero_section(container_layout)
        
        # Benefits section
        self._create_benefits_section(container_layout)
        
        # Action buttons section
        self._create_action_section(container_layout)
        
        # Skip/close section
        self._create_footer_section(container_layout)
        
        main_layout.addWidget(main_container)
        
    def _create_hero_section(self, layout):
        """Create the hero/welcome message section."""
        hero_layout = QVBoxLayout()
        hero_layout.setAlignment(Qt.AlignCenter)
        
        # Main welcome message
        welcome_label = QLabel("🎉 Welcome to SlideMan!")
        welcome_font = QFont()
        welcome_font.setPointSize(28)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: white; margin-bottom: 10px;")
        
        # Subtitle
        subtitle_label = QLabel("Transform how you manage PowerPoint slides")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin-bottom: 20px;")
        
        hero_layout.addWidget(welcome_label)
        hero_layout.addWidget(subtitle_label)
        layout.addLayout(hero_layout)
        
    def _create_benefits_section(self, layout):
        """Create the benefits/value proposition section."""
        benefits_layout = QHBoxLayout()
        benefits_layout.setSpacing(15)
        
        benefits = [
            ("🔍", "Find any slide\nin seconds"),
            ("🏷️", "Tag and organize\nyour content"),
            ("🎯", "Build presentations\nfaster"),
            ("📚", "Never lose\na slide again")
        ]
        
        for icon, text in benefits:
            benefit_card = self._create_benefit_card(icon, text)
            benefits_layout.addWidget(benefit_card)
            
        layout.addLayout(benefits_layout)
        
    def _create_benefit_card(self, icon, text):
        """Create an individual benefit card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: white;")
        
        # Text
        text_label = QLabel(text)
        text_font = QFont()
        text_font.setPointSize(11)
        text_label.setFont(text_font)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        card_layout.addWidget(icon_label)
        card_layout.addWidget(text_label)
        
        return card
        
    def _create_action_section(self, layout):
        """Create the main action buttons section."""
        action_layout = QVBoxLayout()
        action_layout.setSpacing(12)
        
        # Primary action - Start Tutorial
        self.tutorial_btn = QPushButton("🎓 Start Interactive Tutorial (Recommended)")
        self.tutorial_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        
        # Secondary actions container
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(10)
        
        self.import_btn = QPushButton("📁 Import My Slides")
        self.demo_btn = QPushButton("🔍 Explore Demo")
        
        for btn in [self.import_btn, self.demo_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: white;
                    padding: 12px 20px;
                    font-size: 14px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
            
        secondary_layout.addWidget(self.import_btn)
        secondary_layout.addWidget(self.demo_btn)
        
        action_layout.addWidget(self.tutorial_btn)
        action_layout.addLayout(secondary_layout)
        layout.addLayout(action_layout)
        
    def _create_footer_section(self, layout):
        """Create the footer section with skip option."""
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)
        
        self.skip_btn = QPushButton("Skip for now")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.7);
                padding: 8px 16px;
                font-size: 12px;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        
        footer_layout.addWidget(self.skip_btn)
        layout.addLayout(footer_layout)
        
    def _connect_signals(self):
        """Connect button signals to their respective slots."""
        self.tutorial_btn.clicked.connect(self._on_start_tutorial)
        self.import_btn.clicked.connect(self._on_import_slides)
        self.demo_btn.clicked.connect(self._on_load_demo)
        self.skip_btn.clicked.connect(self._on_skip_welcome)
        
    def _on_start_tutorial(self):
        """Handle start tutorial button click."""
        self.logger.info("User chose to start tutorial")
        self.startTutorialRequested.emit()
        self.accept()
        
    def _on_import_slides(self):
        """Handle import slides button click."""
        self.logger.info("User chose to import slides")
        self.importSlidesRequested.emit()
        self.accept()
        
    def _on_load_demo(self):
        """Handle load demo button click."""
        self.logger.info("User chose to explore demo")
        self.loadDemoRequested.emit()
        self.accept()
        
    def _on_skip_welcome(self):
        """Handle skip welcome button click."""
        self.logger.info("User chose to skip welcome")
        self.skipWelcomeRequested.emit()
        self.accept()
        
    def showEvent(self, event):
        """Override to add fade-in effect."""
        super().showEvent(event)
        # Center the dialog on the parent
        if self.parent():
            parent_center = self.parent().geometry().center()
            self.move(parent_center - self.rect().center())