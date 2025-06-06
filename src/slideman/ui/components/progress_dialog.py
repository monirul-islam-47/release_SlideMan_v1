# src/slideman/ui/components/progress_dialog.py

from PySide6.QtWidgets import (QProgressDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QProgressBar, QPushButton, QWidget,
                               QFrame, QApplication)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
import logging
import time

class EnhancedProgressDialog(QProgressDialog):
    """Enhanced progress dialog with ETA, detailed status, and better UX."""
    
    def __init__(self, title: str, operation_name: str, parent=None):
        super().__init__(parent)
        self.operation_name = operation_name
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.items_processed = 0
        self.total_items = 0
        self.current_item_name = ""
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumDuration(500)  # Show after 500ms
        self.setAutoClose(False)
        self.setAutoReset(False)
        
        self._setup_ui()
        
        # Update ETA every second
        self.eta_timer = QTimer()
        self.eta_timer.timeout.connect(self._update_eta)
        self.eta_timer.start(1000)
        
    def _setup_ui(self):
        """Set up the enhanced progress dialog UI."""
        # Set initial values
        self.setRange(0, 100)
        self.setValue(0)
        
        # Create custom widget for detailed progress
        self.progress_widget = QWidget()
        layout = QVBoxLayout(self.progress_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Main operation label
        self.main_label = QLabel(f"Processing {self.operation_name}...")
        main_font = QFont()
        main_font.setPointSize(11)
        main_font.setBold(True)
        self.main_label.setFont(main_font)
        layout.addWidget(self.main_label)
        
        # Current item label
        self.item_label = QLabel("Preparing...")
        self.item_label.setStyleSheet("color: #555; font-size: 10px;")
        layout.addWidget(self.item_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v of %m)")
        layout.addWidget(self.progress_bar)
        
        # Stats layout
        stats_layout = QHBoxLayout()
        
        # Items processed
        self.items_label = QLabel("Items: 0 of 0")
        self.items_label.setStyleSheet("font-size: 9px; color: #666;")
        stats_layout.addWidget(self.items_label)
        
        stats_layout.addStretch()
        
        # ETA
        self.eta_label = QLabel("ETA: Calculating...")
        self.eta_label.setStyleSheet("font-size: 9px; color: #666;")
        stats_layout.addWidget(self.eta_label)
        
        layout.addLayout(stats_layout)
        
        # Set the custom widget as the label
        self.setLabel(self.progress_widget)
        
        # Style the dialog
        self.setStyleSheet("""
            QProgressDialog {
                background-color: white;
                border: 1px solid #ccc;
            }
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 3px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
        """)
        
    def set_total_items(self, total: int):
        """Set the total number of items to process."""
        self.total_items = total
        self.progress_bar.setRange(0, total)
        self._update_display()
        
    def update_progress(self, items_completed: int, current_item: str = ""):
        """Update progress with number of items completed."""
        self.items_processed = items_completed
        self.current_item_name = current_item
        self.last_update_time = time.time()
        
        # Update progress bar
        self.progress_bar.setValue(items_completed)
        
        # Update main progress value for the dialog
        if self.total_items > 0:
            percentage = int((items_completed / self.total_items) * 100)
            self.setValue(percentage)
        
        self._update_display()
        
        # Process events to keep UI responsive
        QApplication.processEvents()
        
    def _update_display(self):
        """Update all display elements."""
        # Update current item
        if self.current_item_name:
            self.item_label.setText(f"Processing: {self.current_item_name}")
        else:
            self.item_label.setText("Processing...")
            
        # Update items count
        self.items_label.setText(f"Items: {self.items_processed} of {self.total_items}")
        
        # Update main label
        if self.total_items > 0:
            percentage = int((self.items_processed / self.total_items) * 100)
            self.main_label.setText(f"{self.operation_name} ({percentage}%)")
        else:
            self.main_label.setText(f"Processing {self.operation_name}...")
            
    def _update_eta(self):
        """Update the ETA calculation."""
        if self.items_processed == 0 or self.total_items == 0:
            self.eta_label.setText("ETA: Calculating...")
            return
            
        elapsed_time = time.time() - self.start_time
        rate = self.items_processed / elapsed_time  # items per second
        
        if rate > 0:
            remaining_items = self.total_items - self.items_processed
            eta_seconds = remaining_items / rate
            
            if eta_seconds < 60:
                eta_text = f"ETA: {int(eta_seconds)}s"
            elif eta_seconds < 3600:
                minutes = int(eta_seconds / 60)
                seconds = int(eta_seconds % 60)
                eta_text = f"ETA: {minutes}m {seconds}s"
            else:
                hours = int(eta_seconds / 3600)
                minutes = int((eta_seconds % 3600) / 60)
                eta_text = f"ETA: {hours}h {minutes}m"
                
            self.eta_label.setText(eta_text)
        else:
            self.eta_label.setText("ETA: Unknown")
            
    def finish_successfully(self):
        """Mark the operation as completed successfully."""
        self.setValue(100)
        self.progress_bar.setValue(self.total_items)
        self.main_label.setText(f"{self.operation_name} completed!")
        self.item_label.setText("All items processed successfully")
        self.eta_label.setText("Completed")
        
        # Stop the ETA timer
        self.eta_timer.stop()
        
        # Auto-close after 2 seconds
        QTimer.singleShot(2000, self.accept)
        
    def finish_with_error(self, error_message: str):
        """Mark the operation as completed with an error."""
        self.main_label.setText(f"{self.operation_name} failed")
        self.item_label.setText(f"Error: {error_message}")
        self.eta_label.setText("Failed")
        
        # Stop the ETA timer
        self.eta_timer.stop()
        
        # Change progress bar color to red
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 2px;
            }
        """)
        
    def closeEvent(self, event):
        """Clean up when dialog is closed."""
        self.eta_timer.stop()
        super().closeEvent(event)


class FileConversionProgressDialog(EnhancedProgressDialog):
    """Specialized progress dialog for file conversion operations."""
    
    def __init__(self, project_name: str, parent=None):
        super().__init__(
            "Converting Slides", 
            f"slides in '{project_name}'", 
            parent
        )
        self.slides_converted = 0
        self.current_file = ""
        self.current_slide = 0
        self.total_slides_in_file = 0
        
    def update_file_progress(self, file_name: str, slide_number: int, total_slides: int):
        """Update progress for current file being converted."""
        self.current_file = file_name
        self.current_slide = slide_number
        self.total_slides_in_file = total_slides
        
        # Update the current item display
        item_text = f"{file_name} (slide {slide_number} of {total_slides})"
        self.update_progress(self.slides_converted, item_text)
        
    def increment_slide_count(self):
        """Increment the total slides converted count."""
        self.slides_converted += 1
        self.update_progress(self.slides_converted, self.current_item_name)


class ProjectCopyProgressDialog(EnhancedProgressDialog):
    """Specialized progress dialog for project file copying operations."""
    
    def __init__(self, project_name: str, parent=None):
        super().__init__(
            "Creating Project", 
            f"files for '{project_name}'", 
            parent
        )
        
    def update_file_copy(self, file_name: str, files_copied: int):
        """Update progress for file copying."""
        self.update_progress(files_copied, f"Copying {file_name}")
        
        # Also update the progress bar text to show file names
        if self.total_items > 0:
            percentage = int((files_copied / self.total_items) * 100)
            self.progress_bar.setFormat(f"{percentage}% - {file_name}")
            
    def finish_copy_operation(self, files_copied: int):
        """Finish the copy operation."""
        self.main_label.setText(f"Project created with {files_copied} files!")
        self.item_label.setText("Ready for slide conversion")
        self.eta_label.setText("Completed")
        
        # Auto-close after 1.5 seconds
        QTimer.singleShot(1500, self.accept)