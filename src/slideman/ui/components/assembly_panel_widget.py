# src/slideman/ui/components/assembly_panel_widget.py

import logging
from typing import Optional, List, Dict
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QListWidget,
                             QListWidgetItem, QSizePolicy, QGroupBox, QProgressBar,
                             QMenu, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QMimeData, QByteArray, QDataStream, QIODevice
from PySide6.QtGui import QFont, QPixmap, QDrag, QPainter, QDragEnterEvent, QDropEvent

from ...app_state import app_state
from ...event_bus import event_bus
from ...models.slide import Slide
from ...services.database import Database
from ...services.exceptions import DatabaseError
from ...services.thumbnail_cache import thumbnail_cache

class AssemblySlideItem(QListWidgetItem):
    """Custom list widget item for assembly slides with drag/drop support."""
    
    def __init__(self, slide: Slide, pixmap: Optional[QPixmap] = None):
        super().__init__()
        self.slide = slide
        self.pixmap = pixmap
        
        # Set up the item appearance
        self.setText(f"Slide {slide.slide_number}")
        if pixmap:
            self.setIcon(pixmap.scaled(QSize(60, 45), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Store slide data for drag/drop
        self.setData(Qt.UserRole, slide.id)
        
        # Set size hint for consistent item height
        self.setSizeHint(QSize(240, 70))


class AssemblyListWidget(QListWidget):
    """Custom list widget with drag/drop reordering support."""
    
    orderChanged = Signal(list)  # List of slide IDs in new order
    slideRemoved = Signal(int)   # Slide ID that was removed
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        
        # Enable custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for reordering."""
        super().dropEvent(event)
        # Emit order changed signal after drop
        self._emit_order_changed()
        
    def _emit_order_changed(self):
        """Emit the order changed signal with current slide order."""
        slide_ids = []
        for i in range(self.count()):
            item = self.item(i)
            if item:
                slide_id = item.data(Qt.UserRole)
                if slide_id is not None:
                    slide_ids.append(slide_id)
        self.orderChanged.emit(slide_ids)
        
    def _show_context_menu(self, position):
        """Show context menu for assembly items."""
        item = self.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        
        # Remove action
        remove_action = menu.addAction("🗑️ Remove from Assembly")
        remove_action.triggered.connect(lambda: self._remove_item(item))
        
        # Move to top action
        if self.row(item) > 0:
            move_top_action = menu.addAction("⬆️ Move to Top")
            move_top_action.triggered.connect(lambda: self._move_to_top(item))
            
        # Move to bottom action
        if self.row(item) < self.count() - 1:
            move_bottom_action = menu.addAction("⬇️ Move to Bottom")
            move_bottom_action.triggered.connect(lambda: self._move_to_bottom(item))
            
        menu.exec_(self.mapToGlobal(position))
        
    def _remove_item(self, item: QListWidgetItem):
        """Remove an item from the assembly."""
        slide_id = item.data(Qt.UserRole)
        if slide_id is not None:
            self.takeItem(self.row(item))
            self.slideRemoved.emit(slide_id)
            self._emit_order_changed()
            
    def _move_to_top(self, item: QListWidgetItem):
        """Move item to the top of the list."""
        row = self.row(item)
        item_widget = self.takeItem(row)
        self.insertItem(0, item_widget)
        self.setCurrentRow(0)
        self._emit_order_changed()
        
    def _move_to_bottom(self, item: QListWidgetItem):
        """Move item to the bottom of the list."""
        row = self.row(item)
        item_widget = self.takeItem(row)
        self.addItem(item_widget)
        self.setCurrentRow(self.count() - 1)
        self._emit_order_changed()


class AssemblyPanelWidget(QWidget):
    """
    Assembly panel widget for building presentations.
    Provides persistent assembly workspace that's always accessible.
    """
    
    # Signals
    previewRequested = Signal()
    exportRequested = Signal()
    assemblyChanged = Signal(list)  # List of slide IDs in assembly
    slideAddedToAssembly = Signal(int)  # Slide ID added
    slideRemovedFromAssembly = Signal(int)  # Slide ID removed
    
    def __init__(self, db_service: Database, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
        
        self.assembly_slides: List[Slide] = []
        self.is_collapsed = False
        
        self.setFixedWidth(280)  # Fixed width for assembly panel
        self.setObjectName("assemblyPanel")
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the assembly panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header section
        self._create_header_section(main_layout)
        
        # Assembly content
        self._create_assembly_content(main_layout)
        
        # Action buttons
        self._create_action_buttons(main_layout)
        
        # Progress section
        self._create_progress_section(main_layout)
        
        self._apply_styling()
        
    def _create_header_section(self, parent_layout: QVBoxLayout):
        """Create the header section with title and collapse button."""
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        self.title_label = QLabel("🎯 Assembly")
        self.title_label.setObjectName("panelTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.title_label.setFont(font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Collapse button
        self.collapse_btn = QPushButton("⬅")
        self.collapse_btn.setObjectName("collapseButton")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_btn)
        
        parent_layout.addLayout(header_layout)
        
        # Subtitle
        self.subtitle_label = QLabel("Building: New Presentation")
        self.subtitle_label.setObjectName("panelSubtitle")
        parent_layout.addWidget(self.subtitle_label)
        
    def _create_assembly_content(self, parent_layout: QVBoxLayout):
        """Create the main assembly content area."""
        # Assembly info
        info_layout = QHBoxLayout()
        self.slide_count_label = QLabel("0 slides")
        self.slide_count_label.setObjectName("assemblyInfo")
        info_layout.addWidget(self.slide_count_label)
        
        info_layout.addStretch()
        
        self.time_estimate_label = QLabel("~0 min")
        self.time_estimate_label.setObjectName("assemblyInfo")
        info_layout.addWidget(self.time_estimate_label)
        
        parent_layout.addLayout(info_layout)
        
        # Assembly slides list
        list_label = QLabel("Slides in Assembly:")
        list_label.setObjectName("sectionLabel")
        parent_layout.addWidget(list_label)
        
        # Scroll area for assembly list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setObjectName("assemblyScrollArea")
        
        self.assembly_list = AssemblyListWidget()
        self.assembly_list.setObjectName("assemblyList")
        self.assembly_list.orderChanged.connect(self._on_order_changed)
        self.assembly_list.slideRemoved.connect(self._on_slide_removed)
        
        scroll_area.setWidget(self.assembly_list)
        scroll_area.setMinimumHeight(200)
        scroll_area.setMaximumHeight(400)
        
        parent_layout.addWidget(scroll_area)
        
        # Drop zone for slides
        self.drop_zone = QLabel("Drop slides here to add to assembly")
        self.drop_zone.setObjectName("dropZone")
        self.drop_zone.setAlignment(Qt.AlignCenter)
        self.drop_zone.setMinimumHeight(80)
        self.drop_zone.setAcceptDrops(True)
        parent_layout.addWidget(self.drop_zone)
        
    def _create_action_buttons(self, parent_layout: QVBoxLayout):
        """Create action buttons for preview and export."""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Preview button
        self.preview_btn = QPushButton("👁️ Preview Assembly")
        self.preview_btn.setObjectName("actionButton")
        self.preview_btn.clicked.connect(self._on_preview_clicked)
        buttons_layout.addWidget(self.preview_btn)
        
        # Export button
        self.export_btn = QPushButton("📤 Export to PowerPoint")
        self.export_btn.setObjectName("exportButton")
        self.export_btn.clicked.connect(self._on_export_clicked)
        buttons_layout.addWidget(self.export_btn)
        
        # Clear assembly button
        self.clear_btn = QPushButton("🗑️ Clear Assembly")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        buttons_layout.addWidget(self.clear_btn)
        
        parent_layout.addLayout(buttons_layout)
        
    def _create_progress_section(self, parent_layout: QVBoxLayout):
        """Create progress section for operations."""
        self.progress_group = QGroupBox("Progress")
        self.progress_group.setObjectName("progressGroup")
        self.progress_group.setVisible(False)  # Hidden by default
        
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_label = QLabel("Preparing export...")
        self.progress_label.setObjectName("progressLabel")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        progress_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(self.progress_group)
        
    def _apply_styling(self):
        """Apply custom styling to the assembly panel."""
        self.setStyleSheet("""
            #assemblyPanel {
                background-color: #2b2b2b;
                border-left: 1px solid #3c3c3c;
            }
            
            #panelTitle {
                color: #ffffff;
                font-weight: bold;
                font-size: 12pt;
            }
            
            #panelSubtitle {
                color: #cccccc;
                font-size: 10pt;
                font-style: italic;
            }
            
            #assemblyInfo {
                color: #cccccc;
                font-size: 9pt;
                font-weight: 500;
            }
            
            #sectionLabel {
                color: #ffffff;
                font-weight: 500;
                font-size: 10pt;
            }
            
            #collapseButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                color: #ffffff;
                font-size: 10pt;
            }
            
            #collapseButton:hover {
                background-color: #4a4a4a;
            }
            
            #assemblyScrollArea {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            
            #assemblyList {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 9pt;
            }
            
            #assemblyList::item {
                padding: 4px;
                border-bottom: 1px solid #555555;
            }
            
            #assemblyList::item:hover {
                background-color: #4a4a4a;
            }
            
            #assemblyList::item:selected {
                background-color: #0078d4;
            }
            
            #dropZone {
                background-color: #3c3c3c;
                border: 2px dashed #555555;
                border-radius: 6px;
                color: #888888;
                font-size: 10pt;
                font-style: italic;
            }
            
            #actionButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 10px;
                color: #ffffff;
                font-size: 10pt;
                font-weight: 500;
            }
            
            #actionButton:hover {
                background-color: #4a4a4a;
                border-color: #777777;
            }
            
            #actionButton:disabled {
                background-color: #2b2b2b;
                border-color: #3c3c3c;
                color: #666666;
            }
            
            #exportButton {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            
            #exportButton:hover {
                background-color: #106ebe;
                border-color: #106ebe;
            }
            
            #exportButton:disabled {
                background-color: #2b2b2b;
                border-color: #3c3c3c;
                color: #666666;
            }
            
            #clearButton {
                background-color: #c42b1c;
                border: 1px solid #c42b1c;
            }
            
            #clearButton:hover {
                background-color: #a23028;
                border-color: #a23028;
            }
            
            #progressGroup {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                color: #ffffff;
            }
            
            #progressLabel {
                color: #cccccc;
                font-size: 9pt;
            }
            
            #progressBar {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                color: #ffffff;
            }
            
            #progressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
        
    def _connect_signals(self):
        """Connect internal and external signals."""
        # Connect to app state changes
        app_state.assemblyBasketChanged.connect(self._on_assembly_basket_changed)
        app_state.currentProjectChanged.connect(self._on_current_project_changed)
        
    @Slot()
    def _toggle_collapse(self):
        """Toggle the collapse state of the panel."""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.setFixedWidth(40)  # Collapsed width
            self.collapse_btn.setText("➡")
            # Hide all content except title and collapse button
            for i in range(1, self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(False)
        else:
            self.setFixedWidth(280)  # Full width
            self.collapse_btn.setText("⬅")
            # Show all content
            for i in range(1, self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(True)
                    
    def add_slide_to_assembly(self, slide: Slide):
        """Add a slide to the assembly."""
        if slide.id in [s.id for s in self.assembly_slides]:
            # Slide already in assembly
            return False
            
        self.assembly_slides.append(slide)
        
        # Get thumbnail for the slide
        pixmap = thumbnail_cache.get_thumbnail(slide.id)
        
        # Create and add list item
        item = AssemblySlideItem(slide, pixmap)
        self.assembly_list.addItem(item)
        
        self._update_assembly_info()
        self.slideAddedToAssembly.emit(slide.id)
        self.assemblyChanged.emit([s.id for s in self.assembly_slides])
        
        return True
        
    def remove_slide_from_assembly(self, slide_id: int):
        """Remove a slide from the assembly."""
        # Remove from internal list
        self.assembly_slides = [s for s in self.assembly_slides if s.id != slide_id]
        
        # Remove from UI list
        for i in range(self.assembly_list.count()):
            item = self.assembly_list.item(i)
            if item and item.data(Qt.UserRole) == slide_id:
                self.assembly_list.takeItem(i)
                break
                
        self._update_assembly_info()
        self.slideRemovedFromAssembly.emit(slide_id)
        self.assemblyChanged.emit([s.id for s in self.assembly_slides])
        
    def clear_assembly(self):
        """Clear all slides from the assembly."""
        self.assembly_slides.clear()
        self.assembly_list.clear()
        self._update_assembly_info()
        self.assemblyChanged.emit([])
        
    def get_assembly_slide_ids(self) -> List[int]:
        """Get the list of slide IDs in the current assembly order."""
        return [s.id for s in self.assembly_slides]
        
    def _update_assembly_info(self):
        """Update the assembly information display."""
        slide_count = len(self.assembly_slides)
        self.slide_count_label.setText(f"{slide_count} slide{'s' if slide_count != 1 else ''}")
        
        # Estimate time (assuming 1 minute per slide as default)
        time_estimate = slide_count * 1
        self.time_estimate_label.setText(f"~{time_estimate} min")
        
        # Update button states
        has_slides = slide_count > 0
        self.preview_btn.setEnabled(has_slides)
        self.export_btn.setEnabled(has_slides)
        self.clear_btn.setEnabled(has_slides)
        
        if not has_slides:
            self.drop_zone.setText("Drop slides here to add to assembly")
        else:
            self.drop_zone.setText(f"Drop more slides here ({slide_count} in assembly)")
            
    @Slot(list)
    def _on_order_changed(self, slide_ids: List[int]):
        """Handle assembly order change."""
        # Reorder internal slides list to match UI order
        slide_map = {s.id: s for s in self.assembly_slides}
        self.assembly_slides = [slide_map[sid] for sid in slide_ids if sid in slide_map]
        
        self.assemblyChanged.emit(slide_ids)
        
    @Slot(int)
    def _on_slide_removed(self, slide_id: int):
        """Handle slide removal from assembly."""
        self.remove_slide_from_assembly(slide_id)
        
    @Slot()
    def _on_preview_clicked(self):
        """Handle preview button click."""
        if not self.assembly_slides:
            return
            
        self.logger.info("Preview assembly requested")
        self.previewRequested.emit()
        
    @Slot()
    def _on_export_clicked(self):
        """Handle export button click."""
        if not self.assembly_slides:
            return
            
        self.logger.info("Export assembly requested")
        self.exportRequested.emit()
        
    @Slot()
    def _on_clear_clicked(self):
        """Handle clear assembly button click."""
        if not self.assembly_slides:
            return
            
        reply = QMessageBox.question(
            self, 
            "Clear Assembly",
            "Are you sure you want to clear all slides from the assembly?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_assembly()
            
    @Slot(list)
    def _on_assembly_basket_changed(self, slide_ids: List[int]):
        """Handle assembly basket change from app state."""
        # This will be called when assembly state changes from other parts of the app
        pass
        
    @Slot(str)
    def _on_current_project_changed(self, project_path: str):
        """Handle current project change."""
        # Clear assembly when project changes
        self.clear_assembly()
        
        # Update subtitle with project name
        if project_path:
            try:
                project = self.db_service.get_project_by_path(project_path)
                if project:
                    self.subtitle_label.setText(f"Building: {project.name} Presentation")
                else:
                    self.subtitle_label.setText("Building: New Presentation")
            except DatabaseError:
                self.subtitle_label.setText("Building: New Presentation")
        else:
            self.subtitle_label.setText("Building: New Presentation")
            
    def show_progress(self, message: str, maximum: int = 0):
        """Show progress for long-running operations."""
        self.progress_label.setText(message)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_group.setVisible(True)
        
    def update_progress(self, value: int):
        """Update progress value."""
        self.progress_bar.setValue(value)
        
    def hide_progress(self):
        """Hide progress display."""
        self.progress_group.setVisible(False)
        
    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasFormat("application/x-slide-id"):
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for adding slides to assembly."""
        if event.mimeData().hasFormat("application/x-slide-id"):
            slide_id = int(event.mimeData().data("application/x-slide-id").data())
            
            try:
                slide = self.db_service.get_slide_by_id(slide_id)
                if slide:
                    success = self.add_slide_to_assembly(slide)
                    if success:
                        event.acceptProposedAction()
                        self.logger.info(f"Added slide {slide_id} to assembly via drag-drop")
                    else:
                        self.logger.debug(f"Slide {slide_id} already in assembly")
            except DatabaseError as e:
                self.logger.error(f"Failed to add slide to assembly: {e}")
                
        event.ignore()