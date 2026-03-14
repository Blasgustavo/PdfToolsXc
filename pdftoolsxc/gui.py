"""
PdfToolsXc - GUI Principal
Sidebar izquierdo con iconos Nerdfont + Panel derecho para archivos
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton,
    QFrame, QScrollArea, QSlider, QCheckBox, QGroupBox,
    QFileDialog, QMessageBox, QProgressBar, QGridLayout, QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QSize, QPoint, QRect, QEvent
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QColor, QPalette, QDragEnterEvent, QDropEvent, QPixmap, QResizeEvent


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._item_list = []

    def addItem(self, item):
        self._item_list.append(item)

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def count(self):
        return len(self._item_list)

    def sizeHint(self):
        return QSize(200, 200)

    def setSpacing(self, spacing):
        self._spacing = spacing

    def spacing(self):
        return self._spacing

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def _do_layout(self, rect, test_only=False):
        m = self.contentsMargins()
        available_width = rect.width() - m.left() - m.right()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        line_height = 0
        spacing = self._spacing

        for item in self._item_list:
            widget = item.widget()
            if widget:
                size_hint = item.sizeHint()
                width = size_hint.width()
                height = size_hint.height()

                if x + width > rect.right() - m.right():
                    x = rect.x() + m.left()
                    y += line_height + spacing
                    line_height = 0

                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), size_hint))

                line_height = max(line_height, height)
                x += width + spacing

        total_height = y + line_height - rect.top() - m.top()
        return total_height

    def update(self):
        if self.parentWidget():
            self.parentWidget().update()
            self.parentWidget().updateGeometry()
            self.invalidate()


def get_font_path() -> str:
    base_path = Path(__file__).parent
    font_path = base_path / "resources" / "fonts" / "JetBrainsMonoNerdFont-Regular.ttf"
    if font_path.exists():
        return str(font_path)
    return ""


TOOLS = [
    {"id": "formatter", "name": "Formatter", "icon": "nf-md-file_document", "desc": "Escalar, comprimir, calidad"},
    {"id": "merger", "name": "Merge", "icon": "nf-md-file_document_multiple", "desc": "Unir PDFs"},
    {"id": "splitter", "name": "Split", "icon": "nf-md-file_document_outline", "desc": "Dividir PDF"},
    {"id": "to_images", "name": "To Images", "icon": "nf-md-image", "desc": "Convertir a imágenes"},
    {"id": "ocr", "name": "OCR", "icon": "nf-md-text_recognition", "desc": "Extraer texto"},
    {"id": "organizer", "name": "Organizer", "icon": "nf-md-swap_horizontal", "desc": "Reordenar páginas"},
]


class ToolButton(QPushButton):
    def __init__(self, tool_id: str, name: str, icon_code: str, desc: str, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self.name = name
        self.icon_code = icon_code
        self.desc = desc
        self.selected = False
        
        icons = {
            "nf-md-file_document": "\uf1c4",
            "nf-md-file_document_multiple": "\uf1c5",
            "nf-md-file_document_outline": "\uf1c6",
            "nf-md-image": "\uf2d6",
            "nf-md-text_recognition": "\uf2d7",
            "nf-md-swap_horizontal": "\uf1c2",
        }
        self.icon_display = icons.get(icon_code, "\uf15b")
        
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._update_style()
        
    def _update_style(self):
        if self.selected:
            bg_color = "#37373d"
            text_color = "#ffffff"
            border_color = "#4fc1ff"
        else:
            bg_color = "transparent"
            text_color = "#cccccc"
            border_color = "transparent"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: none;
                border-left: 3px solid {border_color};
                border-radius: 0px;
                padding: 8px 12px;
                text-align: left;
                font-size: 13px;
                color: {text_color};
                margin: 1px 4px;
            }}
            QPushButton:hover {{
                background-color: #2a2d2e;
            }}
            QPushButton:pressed {{
                background-color: #37373d;
            }}
        """)
        
        self.setText(f"{self.icon_display} {self.name}")
        self.setIcon(QIcon())
        self.setIconSize(QSize(16, 16))
        
    def _get_nerdfont_icon(self) -> str:
        icons = {
            "nf-md-file_document": "\uf1c4",
            "nf-md-file_document_multiple": "\uf1c5",
            "nf-md-file_document_outline": "\uf1c6",
            "nf-md-image": "\uf2d6",
            "nf-md-text_recognition": "\uf2d7",
            "nf-md-swap_horizontal": "\uf1c2",
            "nf-md-format_letter": "\uf1dc",
            "nf-md-cog": "\uf493",
            "nf-md-upload": "\uf093",
            "nf-md-download": "\uf019",
            "nf-md-play": "\uf144",
        }
        return icons.get(self.icon_code, "\uf15b")
        
    def set_selected(self, selected: bool):
        self.selected = selected
        self._update_style()


class DropZone(QFrame):
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        icon_label = QLabel("\uf0ce")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        click_label = QLabel("\uf093  Click para seleccionar")
        click_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        click_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #3b82f6;
                margin-top: 10px;
            }
        """)
        
        font_path = get_font_path()
        if font_path:
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    icon_label.setStyleSheet(f"""
                        QLabel {{
                            font-family: '{font_families[0]}', monospace;
                            font-size: 64px;
                            color: #6b7280;
                        }}
                    """)
        
        title = QLabel("Arrastra archivos aquí")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #cccccc;
            }
        """)
        
        subtitle = QLabel("PDF, PNG, JPG, JPEG")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #808080;
            }
        """)
        
        self.click_label = QLabel("\uf093  Click para seleccionar")
        self.click_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.click_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #0e639c;
                margin-top: 10px;
            }
        """)
        
        layout.addStretch()
        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.click_label)
        layout.addStretch()
        
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 2px dashed #555555;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #0e639c;
                background-color: #2a2d2e;
            }
        """)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()
        super().mousePressEvent(event)
        
    def _open_file_dialog(self):
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos PDF",
            "",
            "Archivos PDF (*.pdf);;Imágenes (*.png *.jpg *.jpeg);;Todos los archivos (*.*)"
        )
        if files:
            self.files_dropped.emit(files)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #2a2d2e;
                    border: 2px dashed #0e639c;
                    border-radius: 8px;
                }
            """)
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 2px dashed #555555;
                border-radius: 8px;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and (path.lower().endswith('.pdf') or 
                        path.lower().endswith('.png') or 
                        path.lower().endswith('.jpg') or 
                        path.lower().endswith('.jpeg')):
                files.append(path)
        
        if files:
            self.files_dropped.emit(files)
            
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 2px dashed #555555;
                border-radius: 8px;
            }
        """)


class Sidebar(QFrame):
    tool_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons: List[ToolButton] = []
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 15)
        layout.setSpacing(4)
        
        title = QLabel("PdfToolsXc")
        title.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #858585;
                padding: 8px 12px 12px 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(title)
        
        for tool in TOOLS:
            btn = ToolButton(tool["id"], tool["name"], tool["icon"], tool["desc"])
            btn.clicked.connect(lambda checked, t=tool["id"]: self._on_tool_clicked(t))
            self.buttons.append(btn)
            layout.addWidget(btn)
            
        layout.addStretch()
        
        self.buttons[0].set_selected(True)
        
        self.setFixedWidth(180)
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
            }
        """)
        
    def _on_tool_clicked(self, tool_id: str):
        for btn in self.buttons:
            btn.set_selected(btn.tool_id == tool_id)
        self.tool_selected.emit(tool_id)


class OptionsPanel(QFrame):
    def __init__(self, tool_id: str = "formatter", parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        if self.tool_id == "formatter":
            self._setup_formatter_options(layout)
        else:
            placeholder = QLabel("Opciones de herramienta")
            placeholder.setStyleSheet("color: #808080; font-size: 14px;")
            layout.addWidget(placeholder)
            
        layout.addStretch()
        
    def _setup_formatter_options(self, layout: QVBoxLayout):
        scale_group = QGroupBox("Escalar")
        scale_layout = QVBoxLayout()
        
        self.chk_a4 = QCheckBox("Escalar a A4 (2480×3508)")
        self.chk_a4.setChecked(True)
        self.chk_a4.setStyleSheet("color: #cccccc;")
        
        self.chk_fit = QCheckBox("Ajustar a página")
        self.chk_fit.setStyleSheet("color: #cccccc;")
        
        scale_layout.addWidget(self.chk_a4)
        scale_layout.addWidget(self.chk_fit)
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        quality_group = QGroupBox("Calidad")
        quality_layout = QVBoxLayout()
        
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(10)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        
        self.quality_label = QLabel("85%")
        self.quality_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_label.setText(f"{v}%")
        )
        
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        compress_group = QGroupBox("Compresión")
        compress_layout = QVBoxLayout()
        
        self.chk_compress = QCheckBox("Comprimir imágenes")
        self.chk_compress.setChecked(True)
        self.chk_compress.setStyleSheet("color: #cccccc;")
        
        compress_layout.addWidget(self.chk_compress)
        compress_group.setLayout(compress_layout)
        layout.addWidget(compress_group)
        
        for group in [scale_group, quality_group, compress_group]:
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    color: #cccccc;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_tool = "formatter"
        self.files: List[str] = []
        self.loaded_files: List[str] = []
        self.page_counter = 1
        self.zoom_level = 0.95
        self._setup_ui()
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize and obj == self.thumbnail_scroll.viewport():
            self._relayout_thumbnails()
        return super().eventFilter(obj, event)
    
    def _relayout_thumbnails(self):
        base_width = 150
        base_height = 200
        thumb_width = int(base_width * self.zoom_level)
        
        viewport_width = self.thumbnail_scroll.viewport().width()
        if viewport_width > 0:
            spacing = 15
            cols = max(1, (viewport_width - 20) // (thumb_width + spacing))
        else:
            cols = 4
        
        current_files = self.files.copy()
        
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.loaded_files = []
        self.files = current_files
        self.page_counter = 1
        self._load_thumbnails()
        
    def _setup_ui(self):
        self.setWindowTitle("PdfToolsXc - Herramientas PDF")
        self.setMinimumSize(1100, 750)
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #cccccc;
            }
            QMessageBox {
                background-color: #252526;
            }
            QMessageBox QLabel {
                font-size: 14px;
                color: #cccccc;
            }
            QMessageBox QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1177bb;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 14px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 7px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: transparent;
                height: 14px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #424242;
                border-radius: 7px;
                min-width: 40px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = Sidebar()
        self.sidebar.tool_selected.connect(self._on_tool_selected)
        main_layout.addWidget(self.sidebar)
        
        content = QFrame()
        content.setStyleSheet("background-color: #1e1e1e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        content_layout.addWidget(self.drop_zone)
        
        self.workspace_header = QFrame()
        self.workspace_header.setVisible(False)
        self.workspace_header.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        workspace_header_layout = QHBoxLayout(self.workspace_header)
        workspace_header_layout.setContentsMargins(10, 8, 10, 8)
        
        workspace_title = QLabel("  Workspace")
        workspace_title.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
            }
        """)
        
        workspace_header_layout.addWidget(workspace_title)
        workspace_header_layout.addStretch()
        
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setFixedSize(28, 28)
        self.btn_zoom_out.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_out = QIcon("assets/zoomout_zoom.png")
        self.btn_zoom_out.setIcon(icon_out)
        self.btn_zoom_out.setIconSize(QSize(18, 18))
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.btn_zoom_out.clicked.connect(self._on_zoom_out)
        
        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setFixedSize(28, 28)
        self.btn_zoom_in.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_in = QIcon("assets/zoomin_zoom.png")
        self.btn_zoom_in.setIcon(icon_in)
        self.btn_zoom_in.setIconSize(QSize(18, 18))
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.btn_zoom_in.clicked.connect(self._on_zoom_in)
        
        zoom_buttons_layout = QHBoxLayout()
        zoom_buttons_layout.setSpacing(4)
        zoom_buttons_layout.addWidget(self.btn_zoom_out)
        zoom_buttons_layout.addWidget(self.btn_zoom_in)
        
        workspace_header_layout.addLayout(zoom_buttons_layout)
        
        self.workspace_container = QFrame()
        self.workspace_container.setVisible(False)
        self.workspace_container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
            }
        """)
        workspace_container_layout = QVBoxLayout(self.workspace_container)
        workspace_container_layout.setContentsMargins(0, 0, 0, 0)
        workspace_container_layout.setSpacing(0)
        
        workspace_container_layout.addWidget(self.workspace_header)
        
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setVisible(False)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumbnail_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
                padding: 10px;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 10px;
                border: none;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background-color: #0e639c;
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #1177bb;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        self.thumbnail_scroll.setWidgetResizable(True)
        
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_widget)
        self.thumbnail_layout.setSpacing(10)
        self.thumbnail_layout.setContentsMargins(10, 10, 10, 10)
        self.thumbnail_scroll.setWidget(self.thumbnail_widget)
        self.thumbnail_scroll.viewport().installEventFilter(self)
        
        workspace_container_layout.addWidget(self.thumbnail_scroll)
        
        content_layout.addWidget(self.workspace_container)
        
        options_layout = QHBoxLayout()
        
        self.options_panel = OptionsPanel(self.current_tool)
        options_layout.addWidget(self.options_panel)
        
        action_layout = QVBoxLayout()
        
        self.btn_add_more = QPushButton("\uf055  Agregar más archivos")
        self.btn_add_more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_more.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0e639c;
                border: 2px dashed #0e639c;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a2d2e;
                border-style: solid;
            }
        """)
        self.btn_add_more.clicked.connect(self._on_add_more_clicked)
        action_layout.addWidget(self.btn_add_more)
        
        self.btn_process = QPushButton("\uf144  PROCESAR")
        self.btn_process.setFixedHeight(50)
        self.btn_process.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_process.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #3c3c3c;
                text-align: center;
                color: #cccccc;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 4px;
            }
        """)
        
        action_layout.addWidget(self.btn_process)
        action_layout.addWidget(self.progress_bar)
        
        self.btn_process.clicked.connect(self._on_process_clicked)
        
        options_layout.addLayout(action_layout)
        content_layout.addLayout(options_layout)
        
        main_layout.addWidget(content)
        
    def _on_tool_selected(self, tool_id: str):
        self.current_tool = tool_id
        
        for i in reversed(range(self.options_panel.layout().count())):
            widget = self.options_panel.layout().itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        new_options = OptionsPanel(tool_id)
        self.options_panel.layout().insertWidget(0, new_options)
        self.options_panel = new_options
        
    def _clear_thumbnails(self):
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.loaded_files = []
        self.page_counter = 1
        
    def _on_files_dropped(self, files: List[str]):
        for f in files:
            if f not in self.files:
                self.files.append(f)
        
        self.drop_zone.setVisible(False)
        self._load_thumbnails()
        
    def _on_zoom_in(self):
        if self.zoom_level < 2.0:
            self.zoom_level = min(2.0, self.zoom_level + 0.25)
            self._update_zoom()
            
    def _on_zoom_out(self):
        if self.zoom_level > 0.95:
            self.zoom_level = max(0.5, self.zoom_level - 0.25)
            self._update_zoom()
            
    def _update_zoom(self):
        self.btn_zoom_out.setEnabled(self.zoom_level > 0.95)
        self.btn_zoom_in.setEnabled(self.zoom_level < 2.0)
        self._relayout_thumbnails()
        
    def _on_add_more_clicked(self):
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos PDF",
            "",
            "Archivos PDF (*.pdf);;Imágenes (*.png *.jpg *.jpeg);;Todos los archivos (*.*)"
        )
        if files:
            self._on_files_dropped(files)
        
    def _load_thumbnails(self):
        self.thumbnail_scroll.setVisible(True)
        self.workspace_container.setVisible(True)
        self.workspace_header.setVisible(True)
        
        from PIL import Image
        import pypdfium2 as pdfium
        import tempfile
        import os
        
        base_width = 150
        base_height = 200
        thumb_width = int(base_width * self.zoom_level)
        thumb_height = int(base_height * self.zoom_level)
        
        viewport_width = self.thumbnail_scroll.viewport().width()
        if viewport_width > 0:
            spacing = 15
            cols = max(1, (viewport_width - 20) // (thumb_width + spacing))
        else:
            cols = 4
        
        row = self.thumbnail_layout.count() // cols
        col = self.thumbnail_layout.count() % cols
        
        for file_path in self.files:
            if file_path in self.loaded_files:
                continue
                
            self.loaded_files.append(file_path)
            
            try:
                path = Path(file_path)
                ext = path.suffix.lower()
                
                if ext == '.pdf':
                    pdf = pdfium.PdfDocument(str(path))
                    total_pages = len(pdf)
                    
                    for page_num in range(total_pages):
                        page = pdf[page_num]
                        scale = 0.5 * self.zoom_level
                        bitmap = page.render(scale=scale)
                        pil_img = bitmap.to_pil()
                        pil_img = pil_img.convert('RGB')
                        
                        img_width, img_height = pil_img.size
                        target_width = thumb_width - 20
                        target_height = thumb_height - 20
                        
                        ratio = min(target_width / img_width, target_height / img_height)
                        new_width = int(img_width * ratio)
                        new_height = int(img_height * ratio)
                        pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        canvas = Image.new('RGB', (thumb_width, thumb_height), '#2d2d2d')
                        paste_x = (thumb_width - new_width) // 2
                        paste_y = (thumb_height - new_height) // 2
                        canvas.paste(pil_img, (paste_x, paste_y))
                        
                        temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                        os.close(temp_fd)
                        canvas.save(temp_path, "JPEG", quality=90)
                        
                        thumb_label = QLabel()
                        pixmap = QPixmap(temp_path)
                        thumb_label.setPixmap(pixmap)
                        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        page_label = QLabel(f"Pág {self.page_counter}")
                        self.page_counter += 1
                        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        page_label.setStyleSheet("""
                            color: #ffffff;
                            font-size: 11px;
                            font-weight: bold;
                            background-color: #0e639c;
                            border-radius: 10px;
                            padding: 4px 10px;
                            min-width: 45px;
                        """)
                        
                        container = QFrame()
                        container.setFixedSize(thumb_width, thumb_height + 30)
                        container.setStyleSheet("""
                            QFrame {
                                background-color: #2d2d2d;
                                border: 1px solid #3c3c3c;
                                border-radius: 8px;
                                padding: 6px;
                            }
                            QFrame:hover {
                                border-color: #0e639c;
                                background-color: #37373d;
                            }
                        """)
                        
                        v_layout = QVBoxLayout(container)
                        v_layout.setContentsMargins(4, 4, 4, 4)
                        v_layout.setSpacing(2)
                        v_layout.addWidget(thumb_label, 0, Qt.AlignmentFlag.AlignCenter)
                        v_layout.addWidget(page_label, 0, Qt.AlignmentFlag.AlignCenter)
                        
                        self.thumbnail_layout.addWidget(container, row, col)
                        
                        col += 1
                        if col >= cols:
                            col = 0
                            row += 1
                            
                else:
                    pil_img = Image.open(str(path))
                    pil_img = pil_img.convert('RGB')
                    pil_img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                    
                    temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                    os.close(temp_fd)
                    pil_img.save(temp_path, "JPEG", quality=90)
                    
                    thumb_label = QLabel()
                    pixmap = QPixmap(temp_path)
                    thumb_label.setPixmap(pixmap.scaled(thumb_width, thumb_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    thumb_label.setScaledContents(False)
                    thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    name_label = QLabel(path.name[:15] + "..." if len(path.name) > 15 else path.name)
                    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_label.setStyleSheet("""
                        color: #cccccc;
                        font-size: 10px;
                        font-weight: bold;
                    """)
                    
                    container = QFrame()
                    container.setFixedWidth(thumb_width)
                    container.setStyleSheet("""
                        QFrame {
                            background-color: #2d2d2d;
                            border: 1px solid #3c3c3c;
                            border-radius: 8px;
                            padding: 8px;
                        }
                        QFrame:hover {
                            border-color: #0e639c;
                            background-color: #37373d;
                        }
                    """)
                    
                    v_layout = QVBoxLayout(container)
                    v_layout.setContentsMargins(4, 4, 4, 4)
                    v_layout.setSpacing(4)
                    v_layout.addWidget(thumb_label, 0, Qt.AlignmentFlag.AlignCenter)
                    v_layout.addWidget(name_label, 0, Qt.AlignmentFlag.AlignCenter)
                    
                    container.setFixedSize(thumb_width, thumb_height + 30)
                    self.thumbnail_layout.addWidget(container, row, col)
                    
                    col += 1
                    if col >= cols:
                        col = 0
                        row += 1
                    
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
                import traceback
                traceback.print_exc()
        
        self.thumbnail_layout.setSpacing(10)
        self.thumbnail_layout.update()
        
    def _on_process_clicked(self):
        if not self.files:
            QMessageBox.warning(self, "Sin archivos", "Arrastra archivos primero")
            return
            
        self.btn_process.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            if self.current_tool == "formatter":
                self._process_formatter()
            elif self.current_tool == "merger":
                self._process_merger()
            elif self.current_tool == "splitter":
                self._process_splitter()
            elif self.current_tool == "to_images":
                self._process_to_images()
            elif self.current_tool == "ocr":
                self._process_ocr()
            elif self.current_tool == "organizer":
                self._process_organizer()
                
            QMessageBox.information(self, "✅ Éxito", "Procesamiento completado\nguardado en la misma carpeta")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error: {str(e)}")
            
        finally:
            self.btn_process.setEnabled(True)
            self.progress_bar.setVisible(False)
            
    def _process_formatter(self):
        from pdftoolsxc.tools import formatter
        
        quality = getattr(self.options_panel, 'quality_slider', None)
        quality_value = quality.value() if quality else 85
        
        scale_a4 = getattr(self.options_panel, 'chk_a4', None)
        do_scale = scale_a4.isChecked() if scale_a4 else True
        
        compress = getattr(self.options_panel, 'chk_compress', None)
        do_compress = compress.isChecked() if compress else True
        
        if not self.files:
            return

        first_path = Path(self.files[0])
        parent = first_path.parent

        if len(self.files) == 1:
            stem = first_path.stem
            output_path = parent / f"{stem}_updated.pdf"
        else:
            output_path = parent / "combined_updated.pdf"

        # Indeterminate while heavy processing
        self.progress_bar.setRange(0, 0)
        formatter.process_files([str(p) for p in self.files], str(output_path), quality=quality_value)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
    def _process_merger(self):
        QMessageBox.information(self, "Merge", "Herramienta Merge - Próximamente")
        
    def _process_splitter(self):
        QMessageBox.information(self, "Split", "Herramienta Split - Próximamente")
        
    def _process_to_images(self):
        QMessageBox.information(self, "To Images", "Herramienta To Images - Próximamente")
        
    def _process_ocr(self):
        QMessageBox.information(self, "OCR", "Herramienta OCR - Próximamente")
        
    def _process_organizer(self):
        QMessageBox.information(self, "Organizer", "Herramienta Organizer - Próximamente")


def main():
    import os
    os.environ['QT_QPA_PLATFORM'] = 'windows'
    
    app = QApplication(sys.argv)
    
    font_path = get_font_path()
    if font_path:
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font = QFont(font_families[0], 12)
                app.setFont(font)
    
    window = MainWindow()
    window.show()
    window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)
    window.raise_()
    window.activateWindow()
    window.setFocus()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
