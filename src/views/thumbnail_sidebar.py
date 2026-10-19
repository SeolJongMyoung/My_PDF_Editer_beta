from typing import List
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QMenu,
)


class ThumbnailSidebar(QWidget):
    """좌측 사이드바: 페이지 썸네일 리스트, 페이지 삭제, 순서 이동, 90도 회전 UI"""

    page_selected = pyqtSignal(int)
    page_delete_requested = pyqtSignal(int)
    page_rotate_requested = pyqtSignal(int)
    page_move_requested = pyqtSignal(int, int)  # (from_index, to_index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(210)
        self.setMaximumWidth(270)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        title_label = QLabel("페이지 썸네일")
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title_label)

        # 상단 페이지 조작 빠른 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self.btn_up = QPushButton("▲ 이동")
        self.btn_up.setToolTip("선택한 페이지를 위로 이동")
        self.btn_down = QPushButton("▼ 이동")
        self.btn_down.setToolTip("선택한 페이지를 아래로 이동")
        self.btn_rotate = QPushButton("↻ 90°")
        self.btn_rotate.setToolTip("선택한 페이지를 시계방향 90도 회전")
        self.btn_delete = QPushButton("🗑 삭제")
        self.btn_delete.setToolTip("선택한 페이지 삭제")

        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_rotate)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        # 썸네일 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(120, 160))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(6)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        layout.addWidget(self.list_widget)

        # 이벤트 연결
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)
        self.btn_rotate.clicked.connect(self._rotate_current)
        self.btn_delete.clicked.connect(self._delete_current)

        self._updating = False

    def populate_thumbnails(self, thumbnails: List[QPixmap], current_index: int = 0):
        """썸네일 목록을 새로 고칩니다."""
        self._updating = True
        self.list_widget.clear()
        for idx, pixmap in enumerate(thumbnails):
            item = QListWidgetItem(f"페이지 {idx + 1}")
            if pixmap:
                item.setIcon(QIcon(pixmap))
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.list_widget.addItem(item)

        if 0 <= current_index < len(thumbnails):
            self.list_widget.setCurrentRow(current_index)
        self._updating = False

    def select_page(self, page_index: int):
        if 0 <= page_index < self.list_widget.count():
            self._updating = True
            self.list_widget.setCurrentRow(page_index)
            self._updating = False

    def _on_row_changed(self, row: int):
        if not self._updating and row >= 0:
            self.page_selected.emit(row)

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            self.page_move_requested.emit(row, row - 1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if 0 <= row < self.list_widget.count() - 1:
            self.page_move_requested.emit(row, row + 1)

    def _rotate_current(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.page_rotate_requested.emit(row)

    def _delete_current(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.page_delete_requested.emit(row)

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        row = self.list_widget.row(item)

        menu = QMenu(self)
        act_up = QAction("▲ 위로 이동", self)
        act_down = QAction("▼ 아래로 이동", self)
        act_rotate = QAction("↻ 90도 회전", self)
        act_delete = QAction("🗑 페이지 삭제", self)

        act_up.setEnabled(row > 0)
        act_down.setEnabled(row < self.list_widget.count() - 1)
        act_delete.setEnabled(self.list_widget.count() > 1)

        act_up.triggered.connect(lambda: self.page_move_requested.emit(row, row - 1))
        act_down.triggered.connect(lambda: self.page_move_requested.emit(row, row + 1))
        act_rotate.triggered.connect(lambda: self.page_rotate_requested.emit(row))
        act_delete.triggered.connect(lambda: self.page_delete_requested.emit(row))

        menu.addAction(act_up)
        menu.addAction(act_down)
        menu.addSeparator()
        menu.addAction(act_rotate)
        menu.addAction(act_delete)
        menu.exec(self.list_widget.mapToGlobal(pos))
