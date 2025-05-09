from PySide6.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QFileDialog, QMessageBox, QStatusBar, QAbstractItemView, QStyledItemDelegate, QTableView)
from PySide6.QtGui import QAction, QIcon, QCursor, QPixmap, QPainter, QPen
from PySide6.QtCore import QSize, Qt, QModelIndex, QAbstractListModel, QAbstractTableModel, QMimeData, Slot, QThreadPool, Signal
import logging
import json
from pathlib import Path
from ...app_state import app_state
from ...models.slide import Slide
from ...services.thumbnail_cache import thumbnail_cache
from ...services.export_service import ExportWorker, ExportWorkerSignals
from ..widgets.delivery_preview_widget import DeliveryPreviewWidget

class FinalReviewModel(QAbstractListModel):
    """Model for displaying and reordering the final slide set."""
    SlideIdRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slides: list[Slide] = []
        self.logger = logging.getLogger(__name__)

    def rowCount(self, parent=QModelIndex()):
        return len(self._slides) if not parent.isValid() else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
        slide = self._slides[index.row()]
        if role == Qt.ItemDataRole.DecorationRole:
            return thumbnail_cache.get_thumbnail(slide.id)
        if role == Qt.ItemDataRole.DisplayRole:
            return f"Slide {slide.slide_index}"
        if role == self.SlideIdRole:
            return slide.id
        return None

    def load_final_set(self, ordered_ids: list[int]):
        self.beginResetModel()
        self._slides = []
        if ordered_ids:
            db = app_state.db_service
            if not db or not db._conn:
                self.logger.error("Database connection not available")
                self.endResetModel()
                return
                
            conn = db._conn
            cursor = conn.cursor()
            
            # Convert all IDs to integers to ensure proper comparison
            ordered_ids_int = [int(sid) if isinstance(sid, str) else sid for sid in ordered_ids]
            
            # Create placeholder for SQL query
            placeholder = ",".join("?" for _ in ordered_ids_int)
            sql = f"SELECT id, file_id, slide_index, thumb_rel_path, image_rel_path FROM slides WHERE id IN ({placeholder})"
            self.logger.debug(f"Executing SQL: {sql} with params: {ordered_ids_int}")
            cursor.execute(sql, ordered_ids_int)
            rows = cursor.fetchall()
            self.logger.debug(f"Found {len(rows)} slides for {len(ordered_ids_int)} ordered IDs")
            
            # Create a map of slide ID (as integer) to Slide objects
            slides_map = {}
            for row in rows:
                slide_id = row['id']
                slides_map[slide_id] = Slide(
                    id=slide_id, 
                    file_id=row['file_id'], 
                    slide_index=row['slide_index'],
                    thumb_rel_path=row['thumb_rel_path'], 
                    image_rel_path=row['image_rel_path']
                )
                self.logger.debug(f"Added slide ID {slide_id} to map")
            
            # Build the final slides list in the correct order
            self._slides = []
            for sid in ordered_ids_int:
                if sid in slides_map:
                    self._slides.append(slides_map[sid])
                    self.logger.debug(f"Added slide ID {sid} to final slides list")
                else:
                    self.logger.warning(f"Slide ID {sid} not found in database results")
            
            self.logger.debug(f"Final slide count in model: {len(self._slides)}")
        else:
            self.logger.debug("No ordered IDs provided to load_final_set")
        self.endResetModel()

    def flags(self, index):
        base = super().flags(index)
        if index.isValid():
            return base | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        return base | Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self):
        return ["application/x-slide-ids"]

    def mimeData(self, indexes):
        mime = QMimeData()
        ids = [self.data(idx, self.SlideIdRole) for idx in indexes if idx.isValid()]
        mime.setData("application/x-slide-ids", json.dumps(ids).encode())
        return mime

    def dropMimeData(self, mime, action, row, column, parent):
        if not mime.hasFormat("application/x-slide-ids"):
            return False
            
        # Extract the slide IDs from the mime data
        ids = json.loads(bytes(mime.data("application/x-slide-ids")).decode())
        moving = [s for s in self._slides if s.id in ids]
        
        if not moving:
            return False
            
        self.layoutAboutToBeChanged.emit()
        
        # Remove the slides being moved
        for s in moving:
            self._slides.remove(s)
            
        # Determine insert position
        insert_at = row if row != -1 else len(self._slides)
        
        # Insert the slides at the new position
        for s in moving:
            self._slides.insert(insert_at, s)
            insert_at += 1
            
        self.layoutChanged.emit()
        
        # Persist the new order to AppState
        # Make sure we're using integer IDs to maintain consistency
        new_order = [int(s.id) for s in self._slides]
        self.logger.debug(f"Persisting new slide order to AppState: {new_order}")
        app_state.set_assembly_order(new_order)
        
        return True

class SlideTableModel(QAbstractTableModel):
    SlideIdRole = Qt.ItemDataRole.UserRole + 1
    def __init__(self, parent=None, columns=4):
        super().__init__(parent)
        self._slides: list[Slide] = []
        self.columns = columns

    def rowCount(self, parent=QModelIndex()):
        return (len(self._slides) + self.columns - 1) // self.columns

    def columnCount(self, parent=QModelIndex()):
        return self.columns

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        idx = index.row() * self.columns + index.column()
        if idx >= len(self._slides):
            return None
        slide = self._slides[idx]
        if role == Qt.ItemDataRole.DecorationRole:
            return thumbnail_cache.get_thumbnail(slide.id)
        if role == Qt.ItemDataRole.DisplayRole:
            return f"Slide {slide.slide_index}"
        if role == self.SlideIdRole:
            return slide.id
        return None

    def flags(self, index):
        base = super().flags(index)
        if index.isValid():
            return base | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        return base | Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self):
        return ["application/x-slide-ids"]

    def mimeData(self, indexes):
        mime = QMimeData()
        ids = [self.data(idx, self.SlideIdRole) for idx in indexes if idx.isValid()]
        mime.setData("application/x-slide-ids", json.dumps(ids).encode())
        return mime

    def dropMimeData(self, mime, action, row, column, parent):
        if not mime.hasFormat("application/x-slide-ids"):
            return False
        ids = json.loads(bytes(mime.data("application/x-slide-ids")).decode())
        moving = [s for s in self._slides if s.id in ids]
        if not moving:
            return False
        self.layoutAboutToBeChanged.emit()
        for s in moving:
            self._slides.remove(s)
        insert_at = row if row != -1 else len(self._slides)
        for s in moving:
            self._slides.insert(insert_at, s)
            insert_at += 1
        self.layoutChanged.emit()
        app_state.set_assembly_order([int(s.id) for s in self._slides])
        return True

    def load_data(self, ordered_ids: list[int]):
        self.beginResetModel()
        self._slides.clear()
        if ordered_ids:
            # reuse logic from FinalReviewModel.load_final_set
            db = app_state.db_service
            if db and db._conn:
                cursor = db._conn.cursor()
                ids_int = [int(sid) for sid in ordered_ids]
                placeholder = ",".join("?" for _ in ids_int)
                sql = f"SELECT id,file_id,slide_index,thumb_rel_path,image_rel_path FROM slides WHERE id IN ({placeholder})"
                cursor.execute(sql, ids_int)
                rows = cursor.fetchall()
                slides_map = {row['id']: Slide(id=row['id'], file_id=row['file_id'], slide_index=row['slide_index'], thumb_rel_path=row['thumb_rel_path'], image_rel_path=row['image_rel_path']) for row in rows}
                for sid in ids_int:
                    if sid in slides_map:
                        self._slides.append(slides_map[sid])
        self.endResetModel()

    def moveSlides(self, ids, target_pos):
        moving = [s for s in self._slides if s.id in ids]
        if not moving:
            return [int(s.id) for s in self._slides]
        self.layoutAboutToBeChanged.emit()
        for s in moving:
            self._slides.remove(s)
        insert_at = target_pos
        for s in moving:
            self._slides.insert(insert_at, s)
            insert_at += 1
        self.layoutChanged.emit()
        return [int(s.id) for s in self._slides]

class ThumbnailDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Draw thumbnail and label
        data = index.data(Qt.ItemDataRole.DecorationRole)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        pix = None
        if isinstance(data, QIcon):
            pix = data.pixmap(option.decorationSize)
        elif isinstance(data, QPixmap):
            pix = data
        if pix:
            painter.drawPixmap(option.rect.x(), option.rect.y(), pix)
        if text:
            painter.drawText(option.rect.x(), option.rect.y() + option.decorationSize.height() + 10, text)

    def sizeHint(self, option, index):
        # Match the table cell size
        base = super().sizeHint(option, index)
        return QSize(option.decorationSize.width(), option.decorationSize.height() + 20)

class SlideTableView(QTableView):
    """TableView subclass with custom drag/drop indicator and reorder signal."""
    slidesReordered = Signal(list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDropIndicatorShown(False)
        self._drop_target_index = QModelIndex()

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat("application/x-slide-ids"):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if not e.mimeData().hasFormat("application/x-slide-ids"):
            return e.ignore()
        self._drop_target_index = self.indexAt(e.pos())
        self.viewport().update()
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self._drop_target_index = QModelIndex()
        self.viewport().update()
        e.accept()

    def dropEvent(self, e):
        if not e.mimeData().hasFormat("application/x-slide-ids"):
            return super().dropEvent(e)
        e.acceptProposedAction()
        data = bytes(e.mimeData().data("application/x-slide-ids")).decode()
        ids = json.loads(data)
        idx = self._drop_target_index
        if idx.isValid():
            target_pos = idx.row() * self.model().columns + idx.column()
        else:
            target_pos = -1
        new_order = self.model().moveSlides(ids, target_pos)
        self.slidesReordered.emit(new_order)
        self._drop_target_index = QModelIndex()
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_target_index.isValid():
            rect = self.visualRect(self._drop_target_index)
            painter = QPainter(self.viewport())
            pen = QPen(Qt.GlobalColor.blue)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(1,1,-1,-1))
            painter.end()

class DeliveryPage(QWidget):
    """Delivery Page: Final review and export of the assembled slides."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._is_exporting = False
        self._thread_pool = QThreadPool()
        
        # Add flag to track signal connection status
        self._signal_connected = False
        
        # Initialize UI
        self._init_ui()
        
        # We'll connect to the assemblyOrderChanged signal when the page is shown
        # This ensures the database is properly initialized before we try to load data

    def _init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Toolbar
        self.toolbar = QToolBar("Delivery Toolbar", self)
        # Placeholder actions
        self.action_thumbnail_up = QAction(QIcon(), "Thumbnail Size +", self)
        self.action_thumbnail_down = QAction(QIcon(), "Thumbnail Size -", self)
        self.action_sort = QAction(QIcon(), "Sort", self)
        self.action_open_ppt = QAction(QIcon(), "Open in PowerPoint", self)
        self.action_save_pptx = QAction(QIcon(), "Save As PPTX", self)
        # Add actions to toolbar
        self.toolbar.addAction(self.action_thumbnail_up)
        self.toolbar.addAction(self.action_thumbnail_down)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_sort)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_open_ppt)
        self.toolbar.addAction(self.action_save_pptx)
        main_layout.addWidget(self.toolbar)
        
        # Connect toolbar actions
        self.action_open_ppt.triggered.connect(self._handle_open_in_ppt)
        self.action_save_pptx.triggered.connect(self._handle_save_as_pptx)

        # Use DeliveryPreviewWidget for slide thumbnails (same behavior as assembly page)
        self.slide_preview = DeliveryPreviewWidget(self)
        # Configure appearance
        self.slide_preview.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.slide_preview.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        # Connect signals
        self.slide_preview.orderChanged.connect(app_state.set_assembly_order)
        main_layout.addWidget(self.slide_preview, 1)
        
        # Status bar for progress feedback
        self.status_bar = QStatusBar(self)
        main_layout.addWidget(self.status_bar)

    # Note: Original duplicate __init__ removed
        
    def showEvent(self, event):
        super().showEvent(event)
        
        # Connect to AppState signals to update when assembly order changes
        # Only connect if not already connected
        if not self._signal_connected:
            app_state.assemblyOrderChanged.connect(self._load_data)
            self._signal_connected = True
            self.logger.debug("Connected assemblyOrderChanged signal")
            
        # Load data whenever the page is shown
        self._load_data()
        
    def hideEvent(self, event):
        # Disconnect signals when page is hidden to prevent memory leaks
        if self._signal_connected:
            # Use a safe approach to disconnect signals
            try:
                # During application shutdown, app_state might already be deleted or in the process of being deleted
                # So we need to handle this gracefully
                self.logger.debug("Attempting to disconnect assemblyOrderChanged signal")
                app_state.assemblyOrderChanged.disconnect(self._load_data)
                self._signal_connected = False
                self.logger.debug("Successfully disconnected assemblyOrderChanged signal")
            except (TypeError, RuntimeError, AttributeError) as e:
                # This will catch various exceptions that might occur during shutdown
                # Including when the Qt C++ object is already deleted
                self.logger.warning(f"Exception during signal disconnection (normal during app shutdown): {e}")
                self._signal_connected = False
        
        # Always call the parent class method
        try:
            super().hideEvent(event)
        except Exception as e:
            # This might also fail during shutdown, so catch any exceptions
            self.logger.warning(f"Exception in parent hideEvent (normal during app shutdown): {e}")

    def _load_data(self, *args):
        """Load ordered slide IDs from AppState into the delivery preview."""
        ordered_ids = app_state.assembly_final_slide_ids
        self.logger.debug(f"Loading data in delivery page, ordered_ids: {ordered_ids}")
        
        if not ordered_ids:
            self.logger.warning("No slides in assembly_final_slide_ids")
            self._set_ui_busy(False, "No slides in assembly")
            self.slide_preview.clear()
            return
            
        # Load the ordered slides
        try:
            # Clear existing slides
            self.slide_preview.clear()
            
            # Get slide data from database
            db = app_state.db_service
            if not db or not db._conn:
                self.logger.error("Database connection not available")
                return
                
            # Convert all IDs to integers to ensure proper comparison
            ordered_ids_int = [int(sid) if isinstance(sid, str) else sid for sid in ordered_ids]
            
            # Create placeholder for SQL query
            placeholder = ",".join("?" for _ in ordered_ids_int)
            sql = f"SELECT id, file_id, slide_index, thumb_rel_path, image_rel_path FROM slides WHERE id IN ({placeholder})"
            
            cursor = db._conn.cursor()
            cursor.execute(sql, ordered_ids_int)
            rows = cursor.fetchall()
            
            # Create a map of slide ID to Slide objects
            slides_map = {}
            for row in rows:
                slide_id = row['id']
                slides_map[slide_id] = Slide(
                    id=slide_id, 
                    file_id=row['file_id'], 
                    slide_index=row['slide_index'],
                    thumb_rel_path=row['thumb_rel_path'], 
                    image_rel_path=row['image_rel_path']
                )
                
            # Add slides in the correct order
            added_count = 0
            for slide_id in ordered_ids_int:
                if slide_id in slides_map:
                    slide = slides_map[slide_id]
                    pix = thumbnail_cache.get_thumbnail(slide.id)
                    if self.slide_preview.add_slide(slide.id, pix, {"KeywordId": None}):
                        added_count += 1
                        
            self.logger.debug(f"Added {added_count} slides to delivery preview")
            self._set_ui_busy(False)
            
        except Exception as e:
            self.logger.error(f"Error loading slides: {e}", exc_info=True)
            self._set_ui_busy(False, f"Error loading slides: {str(e)}")

    def _set_ui_busy(self, is_busy, status_message=""):
        """Set the UI to busy or normal state with optional status message."""
        if is_busy:
            self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
            self.action_open_ppt.setEnabled(False)
            self.action_save_pptx.setEnabled(False)
            if status_message:
                self.status_bar.showMessage(status_message)
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.action_open_ppt.setEnabled(True)
            self.action_save_pptx.setEnabled(True)
            if not status_message:
                self.status_bar.clearMessage()
            else:
                self.status_bar.showMessage(status_message, 5000)  # Show for 5 seconds
    
    @Slot()
    def _handle_open_in_ppt(self):
        """Handle the 'Open in PowerPoint' action."""
        if self.slide_preview.count() == 0:
            QMessageBox.information(self, "No Slides", "There are no slides to open.")
            return
            
        # Set UI to busy state
        self._is_exporting = True
        self._set_ui_busy(True, "Opening in PowerPoint...")
        
        # Create signals and worker
        signals = ExportWorkerSignals()
        worker = ExportWorker(
            ordered_slide_ids=self.slide_preview.get_ordered_slide_indices(),
            output_mode='open',
            output_path=None,
            db_service=app_state.db_service
        )
        worker.signals = signals
        
        # Connect signals
        signals.exportProgress.connect(self._handle_export_progress)
        signals.exportFinished.connect(self._handle_export_finished)
        signals.exportError.connect(self._handle_export_error)
        
        # Start worker
        self.logger.info(f"Starting export worker for 'open' mode with {len(self.slide_preview.get_ordered_slide_indices())} slides")
        self._thread_pool.start(worker)
    
    @Slot()
    def _handle_save_as_pptx(self):
        """Handle the 'Save As PPTX' action."""
        if self.slide_preview.count() == 0:
            QMessageBox.information(self, "No Slides", "There are no slides to export.")
            return
        
        if self._is_exporting:
            QMessageBox.information(self, "Already Exporting", "An export operation is already in progress.")
            return
            
        # Get save location from user
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Presentation As",
            "",
            "PowerPoint Presentation (*.pptx)"
        )
        
        if not save_path:
            # User cancelled
            return
        
        # Add .pptx extension if not provided
        if not save_path.lower().endswith('.pptx'):
            save_path += '.pptx'
        
        # Set UI to busy state
        self._is_exporting = True
        self._set_ui_busy(True, "Saving presentation...")
        
        # Create signals and worker
        signals = ExportWorkerSignals()
        # Get ordered slide IDs from the preview widget
        slide_ids = self.slide_preview.get_ordered_slide_indices()
        worker = ExportWorker(
            ordered_slide_ids=slide_ids,
            output_mode='save',
            output_path=Path(save_path),
            db_service=app_state.db_service
        )
        worker.signals = signals
        
        # Connect signals
        signals.exportProgress.connect(self._handle_export_progress)
        signals.exportFinished.connect(self._handle_export_finished)
        signals.exportError.connect(self._handle_export_error)
        
        # Start worker
        self.logger.info(f"Starting export worker for 'save' mode with {len(slide_ids)} slides to {save_path}")
        self._thread_pool.start(worker)
    
    @Slot(int, int)
    def _handle_export_progress(self, current, total):
        """Update UI with export progress."""
        progress_pct = int((current / total) * 100) if total > 0 else 0
        self.status_bar.showMessage(f"Exporting slide {current}/{total} ({progress_pct}%)")
    
    @Slot(str)
    def _handle_export_finished(self, result_message):
        """Handle successful export completion."""
        self._is_exporting = False
        self._set_ui_busy(False, result_message)
        QMessageBox.information(self, "Export Complete", result_message)
    
    @Slot(str)
    def _handle_export_error(self, error_msg):
        """Handle export error."""
        self._is_exporting = False
        self._set_ui_busy(False, "Export failed")
        QMessageBox.critical(self, "Export Error", f"Failed to export presentation:\n{error_msg}")
