# src/slideman/ui/components/contextual_help.py

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, Signal
from PySide6.QtGui import QFont
import logging
from typing import Dict, Set

class HelpBubble(QWidget):
    """A contextual help bubble that can be shown next to UI elements."""
    
    closed = Signal()
    
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.message = message
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the help bubble UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Main bubble container
        bubble_frame = QFrame()
        bubble_frame.setStyleSheet("""
            QFrame {
                background-color: #f39c12;
                color: white;
                border-radius: 8px;
                padding: 10px;
                max-width: 250px;
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(Qt.black)
        bubble_frame.setGraphicsEffect(shadow)
        
        bubble_layout = QHBoxLayout(bubble_frame)
        bubble_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel("💡")
        icon_font = QFont()
        icon_font.setPointSize(14)
        icon_label.setFont(icon_font)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: white; font-size: 12px;")
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        close_btn.clicked.connect(self._close_bubble)
        
        bubble_layout.addWidget(icon_label)
        bubble_layout.addWidget(message_label)
        bubble_layout.addWidget(close_btn)
        
        layout.addWidget(bubble_frame)
        
    def show_at(self, target_widget: QWidget, position: str = "bottom"):
        """Show the bubble at the specified position relative to the target widget."""
        if not target_widget or not target_widget.isVisible():
            return
            
        # Get target widget's global position
        target_pos = target_widget.mapToGlobal(target_widget.rect().center())
        
        # Adjust position based on specified location
        if position == "bottom":
            pos = target_pos + target_widget.rect().bottomLeft() - target_widget.rect().center()
            pos.setY(pos.y() + 5)
        elif position == "top":
            pos = target_pos + target_widget.rect().topLeft() - target_widget.rect().center()
            pos.setY(pos.y() - self.height() - 5)
        elif position == "right":
            pos = target_pos + target_widget.rect().topRight() - target_widget.rect().center()
            pos.setX(pos.x() + 5)
        elif position == "left":
            pos = target_pos + target_widget.rect().topLeft() - target_widget.rect().center()
            pos.setX(pos.x() - self.width() - 5)
        else:
            pos = target_pos
            
        # Ensure bubble stays on screen
        screen = target_widget.screen().geometry() if target_widget.screen() else None
        if screen:
            if pos.x() < 0:
                pos.setX(5)
            elif pos.x() + self.width() > screen.width():
                pos.setX(screen.width() - self.width() - 5)
                
            if pos.y() < 0:
                pos.setY(5)
            elif pos.y() + self.height() > screen.height():
                pos.setY(screen.height() - self.height() - 5)
        
        self.move(pos)
        self.show()
        self.raise_()
        
        # Auto-hide after 8 seconds
        QTimer.singleShot(8000, self._close_bubble)
        
    def _close_bubble(self):
        """Close the help bubble with animation."""
        self.closed.emit()
        self.hide()
        self.deleteLater()


class OnboardingChecklist(QWidget):
    """A checklist widget to track user onboarding progress."""
    
    taskCompleted = Signal(str)  # task_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = {
            "import_first": {"title": "Import your first presentation", "completed": False},
            "tag_slides": {"title": "Tag 5 slides", "completed": False, "progress": 0, "target": 5},
            "first_search": {"title": "Perform your first search", "completed": False},
            "create_presentation": {"title": "Create a presentation", "completed": False},
            "advanced_features": {"title": "Explore advanced features", "completed": False}
        }
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the checklist UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("🎯 Getting Started Checklist")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Progress indicator
        self.progress_label = QLabel()
        self._update_progress_label()
        layout.addWidget(self.progress_label)
        
        # Task items
        self.task_widgets = {}
        for task_id, task_data in self.tasks.items():
            task_widget = self._create_task_widget(task_id, task_data)
            self.task_widgets[task_id] = task_widget
            layout.addWidget(task_widget)
            
    def _create_task_widget(self, task_id: str, task_data: dict) -> QWidget:
        """Create a widget for a single task."""
        task_frame = QFrame()
        task_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
                margin: 2px 0;
            }
        """)
        
        layout = QHBoxLayout(task_frame)
        
        # Checkbox/completion indicator
        status_label = QLabel("☐" if not task_data["completed"] else "✅")
        status_font = QFont()
        status_font.setPointSize(16)
        status_label.setFont(status_font)
        
        # Task title
        title_label = QLabel(task_data["title"])
        if task_data["completed"]:
            title_label.setStyleSheet("color: #28a745; text-decoration: line-through;")
        
        # Progress (for tasks with progress tracking)
        progress_label = QLabel()
        if "progress" in task_data and "target" in task_data:
            progress_text = f"({task_data['progress']}/{task_data['target']})"
            progress_label.setText(progress_text)
            progress_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        layout.addWidget(status_label)
        layout.addWidget(title_label)
        layout.addWidget(progress_label)
        layout.addStretch()
        
        return task_frame
        
    def _update_progress_label(self):
        """Update the overall progress label."""
        completed = sum(1 for task in self.tasks.values() if task["completed"])
        total = len(self.tasks)
        self.progress_label.setText(f"Progress: {completed}/{total} tasks completed")
        
        if completed == total:
            self.progress_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.progress_label.setStyleSheet("color: #6c757d;")
            
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed."""
        if task_id in self.tasks and not self.tasks[task_id]["completed"]:
            self.tasks[task_id]["completed"] = True
            self._refresh_task_widget(task_id)
            self._update_progress_label()
            self.taskCompleted.emit(task_id)
            
    def update_task_progress(self, task_id: str, progress: int):
        """Update progress for a task."""
        if task_id in self.tasks and "progress" in self.tasks[task_id]:
            self.tasks[task_id]["progress"] = progress
            if progress >= self.tasks[task_id].get("target", 1):
                self.mark_task_completed(task_id)
            else:
                self._refresh_task_widget(task_id)
                
    def _refresh_task_widget(self, task_id: str):
        """Refresh a specific task widget."""
        if task_id in self.task_widgets:
            old_widget = self.task_widgets[task_id]
            new_widget = self._create_task_widget(task_id, self.tasks[task_id])
            
            # Replace in layout
            layout = self.layout()
            index = layout.indexOf(old_widget)
            layout.removeWidget(old_widget)
            old_widget.deleteLater()
            layout.insertWidget(index, new_widget)
            self.task_widgets[task_id] = new_widget


class ContextualHelpManager:
    """Manages contextual help throughout the application."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.help_shown: Set[str] = set()
        self.active_bubbles: Dict[str, HelpBubble] = {}
        
    def show_help_bubble(self, widget: QWidget, message: str, position: str = "bottom", 
                        widget_id: str = None):
        """Show a help bubble for a widget."""
        if not widget or not widget.isVisible():
            return
            
        # Use widget's object name as ID if not provided
        if widget_id is None:
            widget_id = widget.objectName() or f"widget_{id(widget)}"
            
        # Don't show if already shown for this widget
        if widget_id in self.help_shown:
            return
            
        # Close any existing bubble for this widget
        if widget_id in self.active_bubbles:
            self.active_bubbles[widget_id].deleteLater()
            
        bubble = HelpBubble(message, parent=widget.window())
        bubble.closed.connect(lambda: self._on_bubble_closed(widget_id))
        
        self.active_bubbles[widget_id] = bubble
        bubble.show_at(widget, position)
        self.help_shown.add(widget_id)
        
        self.logger.debug(f"Showed help bubble for {widget_id}: {message}")
        
    def _on_bubble_closed(self, widget_id: str):
        """Handle bubble closure."""
        if widget_id in self.active_bubbles:
            del self.active_bubbles[widget_id]
            
    def should_show_help(self, widget_id: str) -> bool:
        """Check if help should be shown for a widget."""
        return widget_id not in self.help_shown
        
    def reset_help_state(self):
        """Reset help state for new user sessions."""
        self.help_shown.clear()
        for bubble in self.active_bubbles.values():
            bubble.deleteLater()
        self.active_bubbles.clear()


# Global instance
contextual_help = ContextualHelpManager()