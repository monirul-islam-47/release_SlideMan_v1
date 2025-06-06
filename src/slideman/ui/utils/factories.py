"""UI factory functions for creating consistent widget configurations."""

from typing import Optional, Tuple, List
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QPushButton, QToolButton, QListView, QTableView,
    QHBoxLayout, QVBoxLayout, QFrame, QSplitter, QGroupBox,
    QLabel, QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QSizePolicy, QHeaderView
)
from PySide6.QtGui import QIcon


def create_icon_button(
    icon_name: str,
    tooltip: str = "",
    size: Tuple[int, int] = (24, 24),
    checkable: bool = False,
    parent: Optional[QWidget] = None
) -> QToolButton:
    """Create a tool button with an icon.
    
    Args:
        icon_name: Name of the icon resource
        tooltip: Tooltip text
        size: Size of the button as (width, height)
        checkable: Whether button is checkable
        parent: Parent widget
        
    Returns:
        Configured QToolButton
    """
    button = QToolButton(parent)
    button.setIcon(QIcon(icon_name))
    button.setIconSize(QSize(*size))
    button.setFixedSize(QSize(*size))
    
    if tooltip:
        button.setToolTip(tooltip)
        
    button.setCheckable(checkable)
    button.setAutoRaise(True)
    
    return button


def create_action_button(
    text: str,
    icon_name: Optional[str] = None,
    tooltip: str = "",
    enabled: bool = True,
    parent: Optional[QWidget] = None
) -> QPushButton:
    """Create a standard action button.
    
    Args:
        text: Button text
        icon_name: Optional icon resource name
        tooltip: Tooltip text
        enabled: Whether button is enabled
        parent: Parent widget
        
    Returns:
        Configured QPushButton
    """
    button = QPushButton(text, parent)
    
    if icon_name:
        button.setIcon(QIcon(icon_name))
        
    if tooltip:
        button.setToolTip(tooltip)
        
    button.setEnabled(enabled)
    
    return button


def create_button_row(
    buttons: List[Tuple[str, str, Optional[str]]],
    spacing: int = 5,
    parent: Optional[QWidget] = None
) -> Tuple[QWidget, List[QPushButton]]:
    """Create a horizontal row of buttons.
    
    Args:
        buttons: List of (text, object_name, icon_name) tuples
        spacing: Spacing between buttons
        parent: Parent widget
        
    Returns:
        Tuple of (container widget, list of buttons)
    """
    container = QWidget(parent)
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(spacing)
    
    button_widgets = []
    
    for text, obj_name, icon_name in buttons:
        btn = create_action_button(text, icon_name, parent=container)
        btn.setObjectName(obj_name)
        layout.addWidget(btn)
        button_widgets.append(btn)
        
    layout.addStretch()
    
    return container, button_widgets


def create_filter_section(
    filters: List[Tuple[str, str, str]],
    parent: Optional[QWidget] = None
) -> QWidget:
    """Create a filter section with labeled controls.
    
    Args:
        filters: List of (label, control_type, object_name) tuples
                control_type can be 'combo', 'spin', 'check', 'line'
        parent: Parent widget
        
    Returns:
        Container widget with filter controls
    """
    container = QWidget(parent)
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    
    for label_text, control_type, obj_name in filters:
        label = QLabel(f"{label_text}:", container)
        layout.addWidget(label)
        
        if control_type == 'combo':
            control = QComboBox(container)
        elif control_type == 'spin':
            control = QSpinBox(container)
            control.setMinimum(0)
            control.setMaximum(9999)
        elif control_type == 'check':
            control = QCheckBox(container)
        elif control_type == 'line':
            control = QLineEdit(container)
            control.setPlaceholderText(f"Filter by {label_text.lower()}...")
        else:
            continue
            
        control.setObjectName(obj_name)
        layout.addWidget(control)
        
        # Add some spacing between filter groups
        layout.addSpacing(10)
        
    layout.addStretch()
    
    return container


def create_splitter(
    orientation: Qt.Orientation,
    sizes: List[int],
    widgets: List[QWidget],
    parent: Optional[QWidget] = None
) -> QSplitter:
    """Create a configured splitter with widgets.
    
    Args:
        orientation: Horizontal or Vertical orientation
        sizes: Initial sizes for each widget
        widgets: Widgets to add to splitter
        parent: Parent widget
        
    Returns:
        Configured QSplitter
    """
    splitter = QSplitter(orientation, parent)
    
    for widget in widgets:
        splitter.addWidget(widget)
        
    if sizes and len(sizes) == len(widgets):
        splitter.setSizes(sizes)
        
    # Style the splitter handle
    splitter.setHandleWidth(5)
    splitter.setChildrenCollapsible(False)
    
    return splitter


def create_table_view(
    selection_behavior: QTableView.SelectionBehavior = QTableView.SelectionBehavior.SelectRows,
    selection_mode: QTableView.SelectionMode = QTableView.SelectionMode.ExtendedSelection,
    alternating_colors: bool = True,
    sortable: bool = True,
    parent: Optional[QWidget] = None
) -> QTableView:
    """Create a consistently configured table view.
    
    Args:
        selection_behavior: Row or item selection
        selection_mode: Single, multi, extended selection
        alternating_colors: Whether to alternate row colors
        sortable: Whether columns are sortable
        parent: Parent widget
        
    Returns:
        Configured QTableView
    """
    table = QTableView(parent)
    
    # Selection
    table.setSelectionBehavior(selection_behavior)
    table.setSelectionMode(selection_mode)
    
    # Appearance
    table.setAlternatingRowColors(alternating_colors)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)
    
    # Sorting
    if sortable:
        table.setSortingEnabled(True)
        
    # Header configuration
    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setHighlightSections(False)
    
    # Context menu
    table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    
    return table


def create_frame_section(
    title: str,
    content_widget: QWidget,
    collapsible: bool = False,
    parent: Optional[QWidget] = None
) -> QGroupBox:
    """Create a framed section with title.
    
    Args:
        title: Section title
        content_widget: Widget to place inside frame
        collapsible: Whether section can be collapsed (not implemented)
        parent: Parent widget
        
    Returns:
        Configured QGroupBox
    """
    group = QGroupBox(title, parent)
    layout = QVBoxLayout(group)
    layout.addWidget(content_widget)
    
    # Style
    group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            border: 1px solid palette(mid);
            border-radius: 4px;
            margin-top: 0.5em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    return group


def create_status_bar_widget(
    items: List[Tuple[str, str]],
    parent: Optional[QWidget] = None
) -> QWidget:
    """Create a widget for status bar with multiple labeled values.
    
    Args:
        items: List of (label, object_name) tuples for status items
        parent: Parent widget
        
    Returns:
        Container widget with status labels
    """
    container = QWidget(parent)
    layout = QHBoxLayout(container)
    layout.setContentsMargins(5, 0, 5, 0)
    
    for i, (label_text, obj_name) in enumerate(items):
        if i > 0:
            # Add separator
            sep = QFrame(container)
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(sep)
            
        label = QLabel(f"{label_text}:", container)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        value = QLabel("0", container)
        value.setObjectName(obj_name)
        layout.addWidget(value)
        
        layout.addSpacing(10)
        
    layout.addStretch()
    
    return container