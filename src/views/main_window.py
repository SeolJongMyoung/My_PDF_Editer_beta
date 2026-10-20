import math
import sys
import time
from enum import Enum
from typing import Callable, Dict, List, Optional, Set, Tuple
from PyQt6.QtCore import Qt, QSize, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QKeySequence,
    QPixmap,
    QPainter,
    QPainterPath,
    QPolygonF,
    QPen,
    QColor,
    QBrush,
    QFont,
    QMouseEvent,
    QKeyEvent,
    QCloseEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QToolBar,
    QToolButton,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QPushButton,
    QScrollArea,
    QLabel,
    QLineEdit,
    QStatusBar,
    QFrame,
    QMenu,
    QMessageBox,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QButtonGroup,
    QColorDialog,
    QStackedWidget,
    QSpinBox,
)
from src.__version__ import APP_VERSION, get_window_title
from src.utils.modern_icons import ModernIcons
from src.views.dialogs.about_dialog import AboutDialog
from src.views.dialogs.help_dialog import HelpDialog


class CursorMode(Enum):
    """마우스 커서 및 편집 도구 모드 정의"""
    VIEW = "선택/보기 모드"
    TEXT_EDIT = "텍스트 수정 모드"
    BOX_REVIEW = "박스 검토 모드"
    CLOUD_MARK = "클라우드 마크 모드"
    HIGHLIGHT = "하이라이트 모드"
    STAMP_MARK = "당초/변경 마크 모드"


MODERN_QSS = """
/* 전체 기본 폰트 및 흰색 바탕 */
QMainWindow {
    background-color: #ffffff;
    font-family: "Malgun Gothic", "Segoe UI", sans-serif;
    font-size: 12px;
    color: #18181b;
}

/* 상단 메뉴 표시줄 (QMenuBar & QMenu) */
QMenuBar {
    background-color: #ffffff;
    color: #18181b;
    border-bottom: 1px solid #e4e4e7;
    padding: 2px 6px;
    font-size: 12px;
}
QMenuBar::item {
    background-color: transparent;
    color: #27272a;
    padding: 5px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #f4f4f5;
    color: #18181b;
}
QMenuBar::item:pressed {
    background-color: #e4e4e7;
    color: #18181b;
}
QMenu {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 4px;
    font-size: 12px;
}
QMenu::item {
    padding: 6px 28px 6px 24px;
    border-radius: 4px;
    color: #27272a;
}
QMenu::item:selected {
    background-color: #f4f4f5;
    color: #18181b;
}
QMenu::item:disabled {
    color: #a1a1aa;
    background-color: transparent;
}
QMenu::separator {
    height: 1px;
    background-color: #e4e4e7;
    margin: 4px 6px;
}

/* 메뉴 표시줄 우측 코너 연속 스크롤 ON/OFF 토글 스위치 버튼 */
QPushButton#MenuBarScrollToggleBtn {
    background-color: #f4f4f5;
    color: #52525b;
    border: 1px solid #d4d4d8;
    border-radius: 10px;
    padding: 2px 10px;
    margin: 2px 6px 2px 0px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#MenuBarScrollToggleBtn:hover {
    background-color: #e4e4e7;
    color: #18181b;
}
QPushButton#MenuBarScrollToggleBtn:checked {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #93c5fd;
}
QPushButton#MenuBarScrollToggleBtn:checked:hover {
    background-color: #dbeafe;
}

/* 상단 1줄 고정 툴바 (모던 그레이스케일 톤) */
QToolBar#TopMainToolbar {
    background-color: #fafafa;
    border-bottom: 1px solid #e4e4e7;
    padding: 0px;
    spacing: 0px;
}
QWidget#ToolbarRowContainer {
    background-color: #fafafa;
}

/* 일반 툴바 버튼 (그레이스케일 미니멀 스타일) */
QToolButton#ModernToolBtn {
    background-color: transparent;
    color: #3f3f46;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
    font-weight: 500;
}
QToolButton#ModernToolBtn:hover {
    background-color: #f4f4f5;
    border-color: #e4e4e7;
    color: #18181b;
}
QToolButton#ModernToolBtn:pressed {
    background-color: #e4e4e7;
}
QToolButton#ModernToolBtn:disabled {
    color: #cbd5e1;
    background-color: transparent;
    border-color: transparent;
}
QToolButton#ModernToolBtn:checked {
    background-color: #e4e4e7;
    color: #18181b;
    border: 1px solid #a1a1aa;
    font-weight: 700;
}

/* 모드 전환 세그먼트 캡슐 그룹 */
QFrame#ModeSegmentGroup {
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 7px;
    padding: 2px;
}
QToolButton#SegmentToolBtn {
    background-color: transparent;
    color: #52525b;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}
QToolButton#SegmentToolBtn:hover {
    color: #18181b;
    background-color: #ebebf0;
}
QToolButton#SegmentToolBtn:checked {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #d4d4d8;
    font-weight: 700;
}

/* 툴바 수직 구분선 */
QFrame#ToolbarDivider {
    background-color: #e4e4e7;
    max-width: 1px;
    min-width: 1px;
    margin: 6px 6px;
}

/* 중앙 QSplitter 핸들 */
QSplitter::handle {
    background-color: #e4e4e7;
    width: 1px;
}
QSplitter::handle:hover {
    background-color: #71717a;
}

/* 좌측 사이드바 패널 */
QFrame#LeftSidebar {
    background-color: #fafafa;
    border-right: 1px solid #e4e4e7;
}
QLabel#SidebarTitle {
    color: #27272a;
    font-weight: 700;
    font-size: 12px;
    padding: 4px 2px;
}

/* 썸네일 리스트 위젯: 행 전체(텍스트 포함) 기본 하이라이트는 비활성화 */
QListWidget#ThumbnailList {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 6px 4px;
    outline: none;
}
QListWidget#ThumbnailList::item {
    background-color: transparent;
    border: none;
    margin: 2px 0px;
    padding: 0px;
}
QListWidget#ThumbnailList::item:hover {
    background-color: transparent;
    border: none;
}
QListWidget#ThumbnailList::item:selected {
    background-color: transparent;
    border: none;
}

/* 우측 책갈피(Bookmark) 패널 */
QFrame#RightBookmarkPanel {
    background-color: #fafafa;
    border-left: 1px solid #e4e4e7;
}
QListWidget#BookmarkList {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget#BookmarkList::item {
    background-color: #ffffff;
    border-bottom: 1px solid #f4f4f5;
    border-radius: 4px;
    padding: 7px 8px;
    color: #3f3f46;
}
QListWidget#BookmarkList::item:hover {
    background-color: #f4f4f5;
    color: #18181b;
}
QListWidget#BookmarkList::item:selected {
    background-color: #f4f4f5;
    border: 1px solid #d4d4d8;
    color: #18181b;
    font-weight: bold;
}

/* 우측 끝 접혀있을 때 나타나는 열기 탭 버튼 */
QPushButton#BookmarkOpenTabBtn {
    background-color: #fafafa;
    color: #3f3f46;
    border: 1px solid #d4d4d8;
    border-right: none;
    border-top-left-radius: 6px;
    border-bottom-left-radius: 6px;
    padding: 12px 4px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#BookmarkOpenTabBtn:hover {
    background-color: #f4f4f5;
    color: #18181b;
    border-color: #a1a1aa;
}

/* 사이드바 조작 버튼 공통 (그레이스케일 톤) */
QPushButton#SmallSidebarBtn {
    background-color: #ffffff;
    color: #3f3f46;
    border: 1px solid #d4d4d8;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#SmallSidebarBtn:hover {
    background-color: #f4f4f5;
    border-color: #a1a1aa;
    color: #18181b;
}
QPushButton#SmallSidebarBtn:pressed {
    background-color: #e4e4e7;
}
QPushButton#SmallSidebarBtn:disabled {
    color: #cbd5e1;
    border-color: #e4e4e7;
}
QPushButton#DeleteSidebarBtn {
    background-color: #ffffff;
    color: #52525b;
    border: 1px solid #d4d4d8;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#DeleteSidebarBtn:hover {
    background-color: #f4f4f5;
    border-color: #71717a;
    color: #18181b;
}
QPushButton#DeleteSidebarBtn:disabled {
    color: #cbd5e1;
    border-color: #e4e4e7;
}

/* 중앙 메인 PDF 뷰어 (순백색 바탕면) */
QScrollArea#CanvasScrollArea {
    background-color: #ffffff;
    border: none;
}
QWidget#CanvasContainer {
    background-color: #ffffff;
}
QLabel#PageCanvasLabel {
    background-color: #ffffff;
    border: 1px solid #d4d4d8;
    color: #71717a;
    font-size: 14px;
}

/* 중앙 뷰어 상단 컨텍스트 도구 속성 바 (Tool Property Bar) */
QFrame#ToolPropBarFrame {
    background-color: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
}
QLabel#ToolPropTitleBadge {
    background-color: #27272a;
    color: #ffffff;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
}
QLabel#ToolPropFieldLabel {
    color: #334155;
    font-size: 11px;
    font-weight: 700;
}
QLabel#ToolPropHintLabel {
    color: #64748b;
    font-size: 11px;
}
QPushButton#ToolPropActionBtn {
    background-color: #dc2626;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#ToolPropActionBtn:hover {
    background-color: #b91c1c;
}
QPushButton#ToolPropSecondaryBtn {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#ToolPropSecondaryBtn:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}
QPushButton#StampTypeToggleBtn {
    background-color: #ffffff;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#StampTypeToggleBtn:checked {
    background-color: #dc2626;
    color: #ffffff;
    border-color: #b91c1c;
}
QSpinBox#ToolPropSpin, QDoubleSpinBox#ToolPropSpin, QComboBox#ToolPropCombo {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: 600;
}

/* 중앙 뷰어 상단 슬림 찾기 바 (Find Bar) */
QFrame#FindBarFrame {
    background-color: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
}
QLabel#FindTitleLabel {
    color: #334155;
    font-size: 12px;
    font-weight: 700;
}
QLineEdit#FindInputEdit {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 12px;
}
QLineEdit#FindInputEdit:focus {
    border: 1.5px solid #2563eb;
}
QLabel#FindCountLabel {
    color: #475569;
    font-size: 12px;
    font-weight: 600;
    padding: 0px 6px;
}
QPushButton#FindNavBtn, QPushButton#FindCloseBtn {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#FindNavBtn:hover, QPushButton#FindCloseBtn:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
    color: #0f172a;
}
QPushButton#FindNavBtn:disabled {
    color: #cbd5e1;
    border-color: #e2e8f0;
}

/* 하단 상태표시줄 (그레이스케일 톤) */
QStatusBar {
    background-color: #fafafa;
    color: #52525b;
    border-top: 1px solid #e4e4e7;
    padding: 2px 8px;
}
QStatusBar::item {
    border: none;
}
QLabel#StatusPageLabel, QLabel#StatusZoomLabel, QLabel#StatusModeLabel {
    color: #52525b;
    font-size: 12px;
    padding: 2px 10px;
}
QLabel#StatusModeBadge {
    background-color: #27272a;
    color: #ffffff;
    border-radius: 4px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 11px;
}
"""


class ThumbnailItemWidget(QWidget):
    """
    개별 썸네일 항목 위젯:
    단일/다중 선택 시 'Page N' 텍스트는 하이라이트에 포함하지 않고
    오직 상단 썸네일 이미지 박스(thumb_label)에만 테두리 하이라이트를 적용합니다.
    """

    def __init__(self, page_number: int, pixmap: Optional[QPixmap] = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_thumbnail_pixmap(pixmap)
        layout.addWidget(self.thumb_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.page_text_label = QLabel(f"Page {page_number}")
        self.page_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_text_label.setStyleSheet(
            "background: transparent; border: none; color: #52525b; font-size: 11px; font-weight: normal;"
        )
        layout.addWidget(self.page_text_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_selected(False)

    def set_thumbnail_pixmap(self, pixmap: Optional[QPixmap]):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                120,
                160,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.thumb_label.setPixmap(scaled)
            self.thumb_label.setFixedSize(scaled.width() + 12, scaled.height() + 12)
        else:
            self.thumb_label.setText("PDF")
            self.thumb_label.setFixedSize(110, 145)

    def set_selected(self, selected: bool):
        if selected:
            self.thumb_label.setStyleSheet(
                """
                QLabel {
                    background-color: #e4e4e7;
                    border: 2.5px solid #18181b;
                    border-radius: 6px;
                    padding: 3px;
                }
                """
            )
        else:
            self.thumb_label.setStyleSheet(
                """
                QLabel {
                    background-color: #ffffff;
                    border: 1px solid #e4e4e7;
                    border-radius: 6px;
                    padding: 5px;
                }
                """
            )


class DraggableThumbnailList(QListWidget):
    """
    1) 내부 선택된 페이지를 마우스로 드래그할 때 들어갈 페이지 사이에 구분선(Drop Indicator)을 그리고,
       마우스 클릭을 떼면 (선택된 페이지 인덱스 리스트, 들어갈 슬롯 인덱스) 시그널을 방출합니다.
    2) 윈도우 탐색기에서 외부 .pdf 파일을 드래그하여 올렸을 때도 들어갈 자리에 구분선을 표시하고,
       마우스를 떼면 (외부 PDF 파일 경로, 들어갈 슬롯 인덱스) 시그널을 방출합니다.
    """

    pages_drop_requested = pyqtSignal(list, int)
    external_pdf_dropped = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._press_pos: Optional[QPointF] = None
        self._pressed_on_selected: bool = False
        self._pressed_row: int = -1
        self._is_dragging_pages: bool = False
        self._is_dragging_external_pdf: bool = False
        self._drop_slot: Optional[int] = None
        self._drop_y: Optional[int] = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.count() > 0:
            self._press_pos = event.position()
            item = self.itemAt(event.pos())
            self._pressed_row = self.row(item) if item else -1

            modifiers = event.modifiers()
            no_mod = not (
                modifiers
                & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
            )
            # 이미 다중 선택된 항목 위에서 그냥 클릭을 시작할 때는 드래그를 위해 다중 선택 상태를 유지
            if item and item.isSelected() and no_mod and len(self.selectedIndexes()) > 1:
                self._pressed_on_selected = True
                return

        self._pressed_on_selected = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            self._press_pos is not None
            and (event.buttons() & Qt.MouseButton.LeftButton)
            and self.count() > 1
        ):
            dist = (event.position() - self._press_pos).manhattanLength()
            if dist >= max(8, QApplication.startDragDistance()):
                self._is_dragging_pages = True
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                self._auto_scroll_if_near_edge(event.pos().y())
                self._update_drop_indicator(event.pos().y())
                self.viewport().update()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = self._is_dragging_pages
            drop_slot = self._drop_slot

            self._is_dragging_pages = False
            self._press_pos = None
            self._drop_slot = None
            self._drop_y = None
            self.viewport().unsetCursor()
            self.viewport().update()

            if was_dragging and drop_slot is not None:
                selected_rows = sorted(idx.row() for idx in self.selectedIndexes())
                if selected_rows:
                    self.pages_drop_requested.emit(selected_rows, drop_slot)
                return

            # 다중 선택된 항목 위에서 드래그하지 않고 단순 클릭만 했다가 뗀 경우 단일 선택으로 전환
            if self._pressed_on_selected and self._pressed_row >= 0:
                self._pressed_on_selected = False
                self.clearSelection()
                self.setCurrentRow(self._pressed_row)
                return

        self._pressed_on_selected = False
        super().mouseReleaseEvent(event)

    # -------------------------------------------------------------------------
    # 윈도우 탐색기 외부 PDF 파일 드래그 앤 드롭 처리
    # -------------------------------------------------------------------------
    @staticmethod
    def _extract_pdf_path_from_mime(mime_data) -> Optional[str]:
        if mime_data and mime_data.hasUrls():
            for url in mime_data.urls():
                local_path = url.toLocalFile()
                if local_path and local_path.lower().endswith(".pdf"):
                    return local_path
        return None

    def dragEnterEvent(self, event):
        pdf_path = self._extract_pdf_path_from_mime(event.mimeData())
        if pdf_path:
            self._is_dragging_external_pdf = True
            self._update_drop_indicator(int(event.position().y()))
            self.viewport().update()
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        pdf_path = self._extract_pdf_path_from_mime(event.mimeData())
        if pdf_path:
            self._is_dragging_external_pdf = True
            y = int(event.position().y())
            self._auto_scroll_if_near_edge(y)
            self._update_drop_indicator(y)
            self.viewport().update()
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        if self._is_dragging_external_pdf:
            self._is_dragging_external_pdf = False
            self._drop_slot = None
            self._drop_y = None
            self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        pdf_path = self._extract_pdf_path_from_mime(event.mimeData())
        if pdf_path:
            y = int(event.position().y())
            self._update_drop_indicator(y)
            slot = self._drop_slot if self._drop_slot is not None else self.count()

            self._is_dragging_external_pdf = False
            self._drop_slot = None
            self._drop_y = None
            self.viewport().update()

            event.acceptProposedAction()
            self.external_pdf_dropped.emit(pdf_path, slot)
        else:
            super().dropEvent(event)

    def _auto_scroll_if_near_edge(self, y: int):
        """드래그 중 위/아래 가장자리에 가까워지면 리스트를 자동으로 스크롤합니다."""
        margin = 28
        vbar = self.verticalScrollBar()
        if y < margin:
            vbar.setValue(vbar.value() - 12)
        elif y > self.viewport().height() - margin:
            vbar.setValue(vbar.value() + 12)

    def _update_drop_indicator(self, y: int):
        """마우스 Y 좌표를 기준으로 들어갈 슬롯(0 ~ count)과 구분선 Y 좌표를 계산합니다."""
        count = self.count()
        if count == 0:
            self._drop_slot = 0
            self._drop_y = max(24, self.viewport().height() // 2)
            return

        for i in range(count):
            rect = self.visualItemRect(self.item(i))
            if y < rect.center().y():
                self._drop_slot = i
                if i == 0:
                    self._drop_y = max(6, rect.top() + 2)
                else:
                    prev_rect = self.visualItemRect(self.item(i - 1))
                    self._drop_y = int((prev_rect.bottom() + rect.top()) / 2)
                return

        # 마지막 아이템 중앙보다 아래쪽인 경우 맨 끝(count) 슬롯
        last_rect = self.visualItemRect(self.item(count - 1))
        self._drop_slot = count
        self._drop_y = min(self.viewport().height() - 6, last_rect.bottom() - 2)

    def paintEvent(self, event):
        super().paintEvent(event)
        if (
            not (self._is_dragging_pages or self._is_dragging_external_pdf)
            or self._drop_y is None
            or self._drop_slot is None
        ):
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.viewport().width()
        y = self._drop_y
        left_x = 12
        right_x = w - 12

        # 1. 구분선 (진한 다크 차콜 실선 + 양끝 원형 마커)
        line_color = QColor("#18181b")
        pen = QPen(line_color, 2.5, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(left_x, y), QPointF(right_x, y))

        painter.setBrush(QBrush(line_color))
        painter.drawEllipse(QPointF(left_x, y), 4.0, 4.0)
        painter.drawEllipse(QPointF(right_x, y), 4.0, 4.0)

        # 2. 중앙 위치 안내 배지 ("1p 앞", "2p · 3p 사이", "마지막 뒤" 또는 외부 PDF 합병 안내)
        count = self.count()
        prefix = "PDF 합병: " if self._is_dragging_external_pdf else ""
        if count == 0:
            label_text = f"{prefix}새 문서로 열기"
        elif self._drop_slot == 0:
            label_text = f"{prefix}1p 앞(맨 위)"
        elif self._drop_slot >= count:
            label_text = f"{prefix}{count}p 뒤(맨 끝)"
        else:
            label_text = f"{prefix}{self._drop_slot}p · {self._drop_slot + 1}p 사이"

        font = QFont("Malgun Gothic", 9, QFont.Weight.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        badge_w = fm.horizontalAdvance(label_text) + 16
        badge_h = 18
        badge_rect = QRectF((w - badge_w) / 2.0, y - (badge_h / 2.0), badge_w, badge_h)

        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.setBrush(QBrush(line_color))
        painter.drawRoundedRect(badge_rect, 9.0, 9.0)

        painter.setPen(QColor("#ffffff"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label_text)
        painter.end()


class InteractivePageLabel(QLabel):
    """
    PDF 페이지 Pixmap을 표시하고, 마우스 드래그(또는 다중 클릭 다각형/당초·변경 스탬프) 영역을 실시간으로 그리며
    완료 시 화면 좌표(QRectF 또는 다각형 꼭짓점 리스트)와 현재 모드를 방출하는 캔버스 라벨 위젯
    """

    canvas_interacted = pyqtSignal(QRectF, CursorMode)
    page_canvas_interacted = pyqtSignal(int, QRectF, CursorMode)
    cloud_polygon_completed = pyqtSignal(int, list)  # (page_index, List[QPointF])
    stamp_mark_clicked = pyqtSignal(int)             # (page_index)
    page_clicked = pyqtSignal(int)

    SNAP_START_RADIUS = 14.0

    def __init__(self, page_index: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("PageCanvasLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.page_index: int = page_index
        self.cursor_mode: CursorMode = CursorMode.VIEW
        self.has_pdf_page: bool = False
        self.current_zoom: float = 1.0
        self.tool_style: Dict[str, object] = {}

        self._dragging: bool = False
        self._start_pos: Optional[QPointF] = None
        self._current_pos: Optional[QPointF] = None

        # 클라우드 마크용 다중 클릭 꼭짓점 및 현재 마우스 호버 위치
        self._cloud_points: List[QPointF] = []
        self._cloud_hover_pos: Optional[QPointF] = None

        # 당초/변경 마크 호버 미리보기 상태
        self._stamp_hover: bool = False

        self._search_rects: List[QRectF] = []
        self._active_search_rect: Optional[QRectF] = None

    def set_tool_style(self, style_dict: Dict[str, object], zoom: float = 1.0):
        self.tool_style = style_dict
        self.current_zoom = max(0.25, float(zoom))
        self.update()

    def set_search_highlights(
        self, rects: List[QRectF], active_rect: Optional[QRectF] = None
    ):
        """PDF 픽스맵 재렌더링 없이 검색된 단어 영역만 오버레이로 즉시 갱신합니다."""
        self._search_rects = list(rects)
        self._active_search_rect = active_rect
        self.update()

    def cancel_cloud_polygon(self):
        if self._cloud_points or self._cloud_hover_pos is not None:
            self._cloud_points.clear()
            self._cloud_hover_pos = None
            self.update()

    def finish_cloud_polygon(self) -> bool:
        """3개 이상의 꼭짓점이 모였을 때 클라우드 마크 다각형 생성을 완료합니다."""
        if len(self._cloud_points) < 3:
            self.cancel_cloud_polygon()
            return False
        pts = list(self._cloud_points)
        self._cloud_points.clear()
        self._cloud_hover_pos = None
        self.update()
        self.cloud_polygon_completed.emit(self.page_index, pts)
        return True

    def set_cursor_mode(self, mode: CursorMode):
        if self.cursor_mode == CursorMode.CLOUD_MARK and mode != CursorMode.CLOUD_MARK:
            self.cancel_cloud_polygon()
        if mode != CursorMode.STAMP_MARK and self._stamp_hover:
            self._stamp_hover = False
        self.cursor_mode = mode
        if mode == CursorMode.VIEW:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == CursorMode.TEXT_EDIT:
            self.setCursor(Qt.CursorShape.IBeamCursor)
        elif mode == CursorMode.STAMP_MARK:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
        self.update()

    def _is_near_cloud_start(self, pos: QPointF) -> bool:
        if len(self._cloud_points) < 3:
            return False
        p0 = self._cloud_points[0]
        return math.hypot(pos.x() - p0.x(), pos.y() - p0.y()) <= self.SNAP_START_RADIUS

    def mousePressEvent(self, event: QMouseEvent):
        if not self.has_pdf_page:
            super().mousePressEvent(event)
            return

        # 당초/변경 마크 모드: 페이지 좌클릭 시 해당 페이지 우측 상단에 즉시 삽입
        if self.cursor_mode == CursorMode.STAMP_MARK:
            self.setFocus()
            self.page_clicked.emit(self.page_index)
            if event.button() == Qt.MouseButton.LeftButton:
                self.stamp_mark_clicked.emit(self.page_index)
                event.accept()
                return

        # 클라우드 마크 모드: 좌클릭으로 꼭짓점 추가 (시작점 클릭 시 완료), 우클릭 시 즉시 완료!
        if self.cursor_mode == CursorMode.CLOUD_MARK:
            self.setFocus()
            self.page_clicked.emit(self.page_index)
            pos = event.position()

            if event.button() == Qt.MouseButton.RightButton:
                if len(self._cloud_points) >= 3:
                    self.finish_cloud_polygon()
                else:
                    self.cancel_cloud_polygon()
                event.accept()
                return

            if event.button() == Qt.MouseButton.LeftButton:
                if self._is_near_cloud_start(pos):
                    self.finish_cloud_polygon()
                    event.accept()
                    return

                # 직전 꼭짓점과 너무 가까운 중복 클릭(더블클릭 2번째 타 등)은 무시
                if self._cloud_points:
                    last_pt = self._cloud_points[-1]
                    if math.hypot(pos.x() - last_pt.x(), pos.y() - last_pt.y()) < 3.5:
                        event.accept()
                        return

                self._cloud_points.append(QPointF(pos.x(), pos.y()))
                self._cloud_hover_pos = QPointF(pos.x(), pos.y())
                self.update()
                event.accept()
                return

        if event.button() == Qt.MouseButton.LeftButton:
            self.page_clicked.emit(self.page_index)
            if self.cursor_mode != CursorMode.VIEW:
                self._dragging = True
                self._start_pos = event.position()
                self._current_pos = event.position()
                self.update()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if (
            self.has_pdf_page
            and self.cursor_mode == CursorMode.CLOUD_MARK
            and event.button() == Qt.MouseButton.LeftButton
        ):
            if len(self._cloud_points) >= 3:
                self.finish_cloud_polygon()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.cursor_mode == CursorMode.STAMP_MARK and self.has_pdf_page:
            if not self._stamp_hover:
                self._stamp_hover = True
                self.update()
            return
        if self.cursor_mode == CursorMode.CLOUD_MARK and self._cloud_points:
            self._cloud_hover_pos = event.position()
            self.update()
            return
        if self._dragging:
            self._current_pos = event.position()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._stamp_hover:
            self._stamp_hover = False
            self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if self.cursor_mode == CursorMode.CLOUD_MARK and self._cloud_points:
            key = event.key()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
                if len(self._cloud_points) >= 3:
                    self.finish_cloud_polygon()
                    event.accept()
                    return
            elif key == Qt.Key.Key_Backspace:
                self._cloud_points.pop()
                self.update()
                event.accept()
                return
            elif key == Qt.Key.Key_Escape:
                self.cancel_cloud_polygon()
                event.accept()
                return
        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.cursor_mode in (CursorMode.CLOUD_MARK, CursorMode.STAMP_MARK):
            return
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._current_pos = event.position()

            if self._start_pos is not None and self._current_pos is not None:
                rect = QRectF(self._start_pos, self._current_pos).normalized()
                if self.cursor_mode == CursorMode.TEXT_EDIT:
                    self.canvas_interacted.emit(rect, self.cursor_mode)
                    self.page_canvas_interacted.emit(self.page_index, rect, self.cursor_mode)
                else:
                    if rect.width() >= 5.0 and rect.height() >= 5.0:
                        self.canvas_interacted.emit(rect, self.cursor_mode)
                        self.page_canvas_interacted.emit(self.page_index, rect, self.cursor_mode)

            self._start_pos = None
            self._current_pos = None
            self.update()
        else:
            super().mouseReleaseEvent(event)

    def _rgb_to_qcolor(
        self, rgb_tuple: Tuple[float, float, float], alpha: int = 255
    ) -> QColor:
        r = int(round(rgb_tuple[0] * 255))
        g = int(round(rgb_tuple[1] * 255))
        b = int(round(rgb_tuple[2] * 255))
        return QColor(r, g, b, alpha)

    def _draw_stamp_hover_preview(self, painter: QPainter):
        """당초/변경 마크 모드에서 마우스를 올린 페이지 우측 상단에 실시간 미리보기 박스를 표시합니다."""
        stamp_text = str(self.tool_style.get("stamp_text", "당초"))
        bw = float(self.tool_style.get("stamp_box_w", 72.0)) * self.current_zoom
        bh = float(self.tool_style.get("stamp_box_h", 32.0)) * self.current_zoom
        top_m = float(self.tool_style.get("stamp_top_margin", 24.0)) * self.current_zoom
        right_m = float(self.tool_style.get("stamp_right_margin", 28.0)) * self.current_zoom
        border_w = float(self.tool_style.get("stamp_border_width", 2.5)) * self.current_zoom
        fsize = float(self.tool_style.get("stamp_font_size", 15.0)) * self.current_zoom
        is_bold = bool(self.tool_style.get("stamp_is_bold", True))
        rgb = self.tool_style.get("stamp_color", (0.90, 0.08, 0.08))

        rx = float(self.width()) - right_m - bw
        ry = top_m
        target_rect = QRectF(rx, ry, bw, bh)

        stroke_col = self._rgb_to_qcolor(rgb, 215)
        fill_col = self._rgb_to_qcolor(rgb, 18)
        pen = QPen(stroke_col, max(1.2, border_w), Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill_col))
        painter.drawRect(target_rect)

        font = QFont("Malgun Gothic")
        font.setPixelSize(max(8, int(round(fsize))))
        font.setBold(is_bold)
        painter.setFont(font)
        painter.setPen(stroke_col)
        painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, stamp_text)

        # 안내 배지
        hint_msg = f"클릭: {self.page_index + 1}p 우측 상단에 [{stamp_text}] 마크 넣기"
        hint_font = QFont("Malgun Gothic", 9)
        hint_font.setBold(True)
        painter.setFont(hint_font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(hint_msg) + 16
        th = 22
        bx = max(8.0, min(rx + bw - tw, float(self.width() - tw - 8)))
        by = ry + bh + 6.0
        badge_rect = QRectF(bx, by, float(tw), float(th))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(39, 39, 42, 215)))
        painter.drawRoundedRect(badge_rect, 5.0, 5.0)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, hint_msg)

    def _draw_cloud_polygon_preview(self, painter: QPainter):
        """다중 클릭 중인 다각형 외곽선과 내부 반투명 빗금(Hatch) 영역 및 완료 안내 배지를 그립니다."""
        if not self._cloud_points:
            return

        cloud_rgb = self.tool_style.get("cloud_color", (0.93, 0.2, 0.2))
        cloud_w = float(self.tool_style.get("cloud_width", 2.2))

        preview_pts = list(self._cloud_points)
        if self._cloud_hover_pos is not None:
            if not self._is_near_cloud_start(self._cloud_hover_pos):
                preview_pts.append(self._cloud_hover_pos)

        # 1) 면적 내부 흐린 배경 + 45도 사선 빗금(Hatch) 채우기
        if len(preview_pts) >= 3:
            poly = QPolygonF(preview_pts)
            poly_path = QPainterPath()
            poly_path.addPolygon(poly)
            poly_path.closeSubpath()

            painter.fillPath(poly_path, QBrush(self._rgb_to_qcolor(cloud_rgb, 24)))

            painter.save()
            painter.setClipPath(poly_path)
            hatch_pen = QPen(self._rgb_to_qcolor(cloud_rgb, 95), 1.15, Qt.PenStyle.SolidLine)
            painter.setPen(hatch_pen)
            bbox = poly.boundingRect()
            min_x = int(bbox.left()) - int(bbox.height()) - 16
            max_x = int(bbox.right()) + 16
            top_y = bbox.top() - 4
            bot_y = bbox.bottom() + 4
            span_h = bot_y - top_y
            step = 10
            for x in range(min_x, max_x, step):
                painter.drawLine(
                    QPointF(float(x), bot_y),
                    QPointF(float(x) + span_h, top_y),
                )
            painter.restore()

        # 2) 확정된 꼭짓점 사이 실선 연결
        solid_pen = QPen(self._rgb_to_qcolor(cloud_rgb, 235), max(1.5, cloud_w), Qt.PenStyle.SolidLine)
        painter.setPen(solid_pen)
        for i in range(len(self._cloud_points) - 1):
            painter.drawLine(self._cloud_points[i], self._cloud_points[i + 1])

        # 3) 현재 마우스 위치까지의 점선 가이드라인 및 시작점으로 닫히는 면적 가이드라인
        if self._cloud_hover_pos is not None:
            dash_pen = QPen(self._rgb_to_qcolor(cloud_rgb, 195), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(dash_pen)
            target_pt = (
                self._cloud_points[0]
                if self._is_near_cloud_start(self._cloud_hover_pos)
                else self._cloud_hover_pos
            )
            painter.drawLine(self._cloud_points[-1], target_pt)
            if len(self._cloud_points) >= 2 and target_pt != self._cloud_points[0]:
                painter.drawLine(target_pt, self._cloud_points[0])

        # 4) 각 꼭짓점 핸들 및 시작점(P0) 스냅 링 표시
        near_start = (
            self._cloud_hover_pos is not None
            and self._is_near_cloud_start(self._cloud_hover_pos)
        )
        for idx, pt in enumerate(self._cloud_points):
            if idx == 0 and len(self._cloud_points) >= 3:
                ring_color = QColor(22, 163, 74, 240) if near_start else self._rgb_to_qcolor(cloud_rgb, 235)
                fill_color = QColor(187, 247, 208, 220) if near_start else QColor(255, 255, 255, 240)
                radius = 7.0 if near_start else 5.5
                painter.setPen(QPen(ring_color, 2.2))
                painter.setBrush(QBrush(fill_color))
                painter.drawEllipse(pt, radius, radius)
            else:
                painter.setPen(QPen(self._rgb_to_qcolor(cloud_rgb, 235), 1.8))
                painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
                painter.drawEllipse(pt, 4.0, 4.0)

        # 5) 마우스 커서 근처에 완료 조작 안내 배지 표시
        anchor = self._cloud_hover_pos or self._cloud_points[-1]
        if len(self._cloud_points) < 3:
            msg = f"점 {len(self._cloud_points)}개 선택됨 (최소 3개 이상 클릭하세요)"
            bg_col = QColor(39, 39, 42, 215)
        elif near_start:
            msg = "시작점 클릭: 클라우드 마크 완성!"
            bg_col = QColor(21, 128, 61, 230)
        else:
            msg = "더블클릭 · 우클릭 · 시작점 클릭 · Enter로 클라우드 마크 완성"
            bg_col = QColor(185, 28, 28, 220)

        font = QFont("Malgun Gothic", 9)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(msg) + 18
        th = 24
        bx = min(max(8.0, anchor.x() + 14.0), max(8.0, float(self.width() - tw - 8)))
        by = max(8.0, anchor.y() - 32.0)
        badge_rect = QRectF(bx, by, float(tw), float(th))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(badge_rect, 6.0, 6.0)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, msg)

    def paintEvent(self, event):
        super().paintEvent(event)

        has_search = self.has_pdf_page and (
            bool(self._search_rects) or self._active_search_rect is not None
        )
        has_drag = (
            self._dragging
            and self._start_pos is not None
            and self._current_pos is not None
        )
        has_cloud = (
            self.has_pdf_page
            and self.cursor_mode == CursorMode.CLOUD_MARK
            and bool(self._cloud_points)
        )
        has_stamp = (
            self.has_pdf_page
            and self.cursor_mode == CursorMode.STAMP_MARK
            and self._stamp_hover
        )
        if not has_search and not has_drag and not has_cloud and not has_stamp:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1) 검색 일치 항목 하이라이트 오버레이 (재렌더링 0회)
        if has_search:
            match_pen = QPen(QColor(202, 138, 4, 185), 1.0, Qt.PenStyle.SolidLine)
            match_brush = QBrush(QColor(250, 204, 21, 105))
            painter.setPen(match_pen)
            painter.setBrush(match_brush)
            for r in self._search_rects:
                painter.drawRoundedRect(r.adjusted(-1, -1, 1, 1), 2.0, 2.0)

            if self._active_search_rect is not None:
                active_pen = QPen(QColor(234, 88, 12, 245), 2.0, Qt.PenStyle.SolidLine)
                active_brush = QBrush(QColor(249, 115, 22, 135))
                painter.setPen(active_pen)
                painter.setBrush(active_brush)
                painter.drawRoundedRect(
                    self._active_search_rect.adjusted(-2, -2, 2, 2), 2.5, 2.5
                )

        # 2) 클라우드 마크 다중 클릭 다각형 + 내부 빗금(Hatch) 오버레이
        if has_cloud:
            self._draw_cloud_polygon_preview(painter)

        # 3) 당초/변경 마크 우측 상단 호버 미리보기
        if has_stamp:
            self._draw_stamp_hover_preview(painter)

        # 4) 마우스 드래그 박스 오버레이
        if has_drag:
            rect = QRectF(self._start_pos, self._current_pos).normalized()

            if self.cursor_mode == CursorMode.BOX_REVIEW:
                box_rgb = self.tool_style.get("box_color", (1.0, 0.0, 0.0))
                box_w = float(self.tool_style.get("box_width", 2.0)) * self.current_zoom
                pen = QPen(self._rgb_to_qcolor(box_rgb, 235), max(1.0, box_w), Qt.PenStyle.SolidLine)
                brush = QBrush(self._rgb_to_qcolor(box_rgb, 32))
            elif self.cursor_mode == CursorMode.HIGHLIGHT:
                hl_rgb = self.tool_style.get("highlight_color", (1.0, 0.95, 0.0))
                pen = QPen(self._rgb_to_qcolor(hl_rgb, 230), 1.5, Qt.PenStyle.DashLine)
                brush = QBrush(self._rgb_to_qcolor(hl_rgb, 105))
            else:
                pen = QPen(QColor(39, 39, 42, 220), 1.5, Qt.PenStyle.DashLine)
                brush = QBrush(QColor(39, 39, 42, 30))

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(rect)

        painter.end()


class FindLineEdit(QLineEdit):
    """Enter(다음), Shift+Enter(이전), Esc(닫기) 키 이벤트를 지원하는 검색 입력창"""

    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    find_close_requested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_F3):
            if mods & Qt.KeyboardModifier.ShiftModifier:
                self.find_prev_requested.emit()
            else:
                self.find_next_requested.emit()
            event.accept()
            return
        if key == Qt.Key.Key_Escape:
            self.find_close_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class ZoomScrollArea(QScrollArea):
    """
    Ctrl + 마우스 휠 확대/축소, 가상화 연속 스크롤 뷰포트 감지,
    단일 페이지 경계 휠 넘김 및 키보드 페이지 이동을 지원하는 스크롤 영역
    """

    wheel_zoom_requested = pyqtSignal(float)
    boundary_page_step_requested = pyqtSignal(int)     # 단일 페이지 모드에서 상/하단 끝 휠 이동 (-1, +1)
    key_page_navigation_requested = pyqtSignal(str)    # "prev", "next", "first", "last"
    viewport_changed = pyqtSignal()                    # 스크롤/리사이즈 발생 시 가시 영역 갱신 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.continuous_scroll_mode: bool = True
        self._last_boundary_turn_ts: float = 0.0
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)

    def _on_scroll_value_changed(self, _value: int):
        self.viewport_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.viewport_changed.emit()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.wheel_zoom_requested.emit(0.15)
            elif delta < 0:
                self.wheel_zoom_requested.emit(-0.15)
            event.accept()
            return

        if not self.continuous_scroll_mode:
            delta = event.angleDelta().y()
            vbar = self.verticalScrollBar()
            now = time.monotonic()
            if delta < 0 and vbar.value() >= vbar.maximum():
                if now - self._last_boundary_turn_ts >= 0.14:
                    self._last_boundary_turn_ts = now
                    self.boundary_page_step_requested.emit(1)
                event.accept()
                return
            elif delta > 0 and vbar.value() <= vbar.minimum():
                if now - self._last_boundary_turn_ts >= 0.14:
                    self._last_boundary_turn_ts = now
                    self.boundary_page_step_requested.emit(-1)
                event.accept()
                return

        super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        vbar = self.verticalScrollBar()

        if key in (Qt.Key.Key_PageUp, Qt.Key.Key_Left):
            self.key_page_navigation_requested.emit("prev")
            event.accept()
            return
        if key in (Qt.Key.Key_PageDown, Qt.Key.Key_Right):
            self.key_page_navigation_requested.emit("next")
            event.accept()
            return
        if key == Qt.Key.Key_Space:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.key_page_navigation_requested.emit("prev")
            else:
                self.key_page_navigation_requested.emit("next")
            event.accept()
            return
        if key == Qt.Key.Key_Home:
            self.key_page_navigation_requested.emit("first")
            event.accept()
            return
        if key == Qt.Key.Key_End:
            self.key_page_navigation_requested.emit("last")
            event.accept()
            return
        if key == Qt.Key.Key_Up:
            if not self.continuous_scroll_mode and vbar.value() <= vbar.minimum():
                self.key_page_navigation_requested.emit("prev")
                event.accept()
                return
        if key == Qt.Key.Key_Down:
            if not self.continuous_scroll_mode and vbar.value() >= vbar.maximum():
                self.key_page_navigation_requested.emit("next")
                event.accept()
                return

        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    """PDF 편집기 메인 윈도우 (드래그앤드롭 구분선 이동 + 다중 페이지 선택/추출 + 다른 PDF 합병 + 가상화 연속 스크롤 포함)"""

    CANVAS_MARGIN_TOP = 24
    CANVAS_MARGIN_BOTTOM = 24
    CANVAS_PAGE_SPACING = 18

    mode_changed = pyqtSignal(CursorMode)
    continuous_mode_toggled = pyqtSignal(bool)
    page_render_requested = pyqtSignal(int)
    current_page_scrolled = pyqtSignal(int)
    page_canvas_interacted = pyqtSignal(int, QRectF, CursorMode)
    cloud_polygon_completed = pyqtSignal(int, list)  # (page_index, List[QPointF])
    stamp_mark_clicked = pyqtSignal(int)             # (page_index: 우측 상단에 당초/변경 마크 즉시 삽입)
    stamp_batch_dialog_requested = pyqtSignal()      # 페이지별 당초/변경 일괄·개별 설정 대화상자 열기
    tool_style_changed = pyqtSignal(dict)            # 도구 속성 변경 시 방출
    page_move_requested = pyqtSignal(int, int)
    pages_drop_requested = pyqtSignal(list, int)  # (selected_indices, insert_before_slot)
    merge_pages_requested = pyqtSignal(int)       # preset_slot (-1이면 기본 위치)
    external_pdf_dropped = pyqtSignal(str, int)   # (source_pdf_path, insert_before_slot)
    bookmark_selected = pyqtSignal(int)
    bookmark_add_requested = pyqtSignal()
    bookmark_delete_requested = pyqtSignal(int)
    find_query_changed = pyqtSignal(str)
    find_next_requested = pyqtSignal()
    find_prev_requested = pyqtSignal()
    find_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(get_window_title())
        self.resize(1320, 860)

        self.current_mode = CursorMode.VIEW
        self.continuous_scroll: bool = True
        self.current_page = 0
        self.current_page_index: int = 0
        self.total_pages = 0
        self._page_sizes: List[Tuple[int, int]] = []
        self._page_slots: List[InteractivePageLabel] = []
        self._rendered_pages: Set[int] = set()
        self._programmatic_scroll: bool = False
        self._close_confirm_callback: Optional[Callable[[], bool]] = None

        self._find_debounce_timer = QTimer(self)
        self._find_debounce_timer.setSingleShot(True)
        self._find_debounce_timer.setInterval(200)
        self._find_debounce_timer.timeout.connect(self._emit_find_query)

        # 각 검토·주석 도구별 독립적인 스타일 속성 상태
        self.current_zoom: float = 1.0
        self.tool_prop_bar_enabled: bool = True
        self._tool_style: Dict[str, object] = {
            "box_color": (1.0, 0.0, 0.0),
            "box_width": 2.0,
            "cloud_color": (0.93, 0.2, 0.2),
            "cloud_width": 2.2,
            "cloud_scale": 2.5,
            "highlight_color": (1.0, 0.95, 0.0),
            "stamp_text": "당초",
            "stamp_box_w": 72.0,
            "stamp_box_h": 32.0,
            "stamp_color": (0.90, 0.08, 0.08),
            "stamp_border_width": 2.5,
            "stamp_font_key": "malgun",
            "stamp_font_size": 15.0,
            "stamp_is_bold": True,
            "stamp_top_margin": 24.0,
            "stamp_right_margin": 28.0,
        }

        self._init_toolbar()
        self._init_menubar()
        self._init_central_area()
        self._init_statusbar()
        self.setStyleSheet(MODERN_QSS)

        self._sync_tool_style_to_canvases()
        self._setup_empty_state()

    def show_about_dialog(self):
        """도움말/정보(About) 및 버전 변경 이력(Change Log) 팝업 창을 표시합니다."""
        dialog = AboutDialog(parent=self)
        dialog.exec()

    def show_help_dialog(self):
        """도움말(F1): 현재 빌드 버전/변경사항, GitHub README 주요 기능, 단축키 일람 팝업 창을 표시합니다."""
        dialog = HelpDialog(parent=self)
        dialog.exec()

    def set_close_confirm_callback(self, callback: Callable[[], bool]):
        self._close_confirm_callback = callback

    def closeEvent(self, event: QCloseEvent):
        if self._close_confirm_callback is not None:
            if not self._close_confirm_callback():
                event.ignore()
                return
        event.accept()

    # -------------------------------------------------------------------------
    # 1. 상단 1줄 고정 모던 그레이스케일 툴바
    # -------------------------------------------------------------------------
    def _make_tool_btn(
        self,
        action: QAction,
        object_name: str = "ModernToolBtn",
        icon_only: bool = False,
    ) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName(object_name)
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
            if icon_only
            else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        btn.setIconSize(QSize(17, 17) if icon_only else QSize(16, 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setObjectName("ToolbarDivider")
        line.setFrameShape(QFrame.Shape.VLine)
        return line

    def _init_toolbar(self):
        toolbar = QToolBar("상단 메인 툴바", self)
        toolbar.setObjectName("TopMainToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.main_toolbar = toolbar
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        row_widget = QWidget(toolbar)
        row_widget.setObjectName("ToolbarRowContainer")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setSpacing(3)

        self.act_open = QAction(ModernIcons.get_icon("open"), "열기", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.setToolTip("PDF 문서 열기 (Ctrl+O)")

        self.act_save = QAction(ModernIcons.get_icon("save"), "저장", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.setToolTip("변경된 PDF 문서 저장 (Ctrl+S)")

        row_layout.addWidget(self._make_tool_btn(self.act_open, icon_only=True))
        row_layout.addWidget(self._make_tool_btn(self.act_save, icon_only=True))
        row_layout.addWidget(self._make_divider())

        self.act_undo = QAction(ModernIcons.get_icon("undo"), "실행 취소", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.setToolTip("직전 작업 실행 취소 (Ctrl+Z, 최대 10단계)")

        self.act_redo = QAction(ModernIcons.get_icon("redo"), "다시 실행", self)
        self.act_redo.setShortcuts([
            QKeySequence.StandardKey.Redo,
            QKeySequence("Ctrl+Y"),
            QKeySequence("Ctrl+Shift+Z"),
        ])
        self.act_redo.setToolTip("실행 취소한 작업 다시 실행 (Ctrl+Y, 최대 10단계)")

        row_layout.addWidget(self._make_tool_btn(self.act_undo, icon_only=True))
        row_layout.addWidget(self._make_tool_btn(self.act_redo, icon_only=True))
        row_layout.addWidget(self._make_divider())

        self.act_prev_page = QAction(ModernIcons.get_icon("prev"), "이전", self)
        self.act_prev_page.setShortcut(QKeySequence("PgUp"))
        self.act_prev_page.setToolTip("이전 페이지 (PageUp)")

        self.act_next_page = QAction(ModernIcons.get_icon("next"), "다음", self)
        self.act_next_page.setShortcut(QKeySequence("PgDown"))
        self.act_next_page.setToolTip("다음 페이지 (PageDown)")

        row_layout.addWidget(self._make_tool_btn(self.act_prev_page, icon_only=True))
        row_layout.addWidget(self._make_tool_btn(self.act_next_page, icon_only=True))
        row_layout.addWidget(self._make_divider())

        # 아이콘을 지정하지 않아야 QMenu('보기' 메뉴)에서 체크 표시(✓)가 선명하게 나타남
        self.act_continuous_scroll = QAction("연속 스크롤: 켜짐(&C)", self)
        self.act_continuous_scroll.setCheckable(True)
        self.act_continuous_scroll.setChecked(True)
        self.act_continuous_scroll.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.act_continuous_scroll.setToolTip(
            "연속 스크롤 보기 켜기/끄기 (Ctrl+Shift+C, 끄면 이전 버전처럼 1페이지씩 보기 모드로 작동합니다)"
        )
        self.act_continuous_scroll.toggled.connect(self.set_continuous_scroll_mode)

        self.act_zoom_out = QAction(ModernIcons.get_icon("zoom_out"), "축소", self)
        self.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.act_zoom_out.setToolTip("화면 축소 (Ctrl+-)")

        self.act_zoom_in = QAction(ModernIcons.get_icon("zoom_in"), "확대", self)
        self.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.act_zoom_in.setToolTip("화면 확대 (Ctrl++)")

        row_layout.addWidget(self._make_tool_btn(self.act_zoom_out, icon_only=True))
        row_layout.addWidget(self._make_tool_btn(self.act_zoom_in, icon_only=True))
        row_layout.addWidget(self._make_divider())

        segment_frame = QFrame()
        segment_frame.setObjectName("ModeSegmentGroup")
        seg_layout = QHBoxLayout(segment_frame)
        seg_layout.setContentsMargins(2, 1, 2, 1)
        seg_layout.setSpacing(2)

        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)

        self.act_mode_view = QAction(ModernIcons.get_icon("view"), "선택", self)
        self.act_mode_view.setCheckable(True)
        self.act_mode_view.setChecked(True)
        self.act_mode_view.setShortcut(QKeySequence("Esc"))
        self.act_mode_view.setToolTip("일반 선택 및 보기 모드 (Esc)")

        self.act_mode_text = QAction(ModernIcons.get_icon("text"), "텍스트 수정", self)
        self.act_mode_text.setCheckable(True)
        self.act_mode_text.setShortcut(QKeySequence("Ctrl+E"))
        self.act_mode_text.setToolTip("클릭/드래그하여 텍스트 수정 (Ctrl+E)")

        self.act_mode_box = QAction(ModernIcons.get_icon("box"), "박스 검토", self)
        self.act_mode_box.setCheckable(True)
        self.act_mode_box.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.act_mode_box.setToolTip("드래그하여 검토용 사각형 마크업 추가 (Ctrl+Shift+B)")

        self.act_mode_cloud = QAction(
            ModernIcons.get_icon("cloud"), "클라우드 마크", self
        )
        self.act_mode_cloud.setCheckable(True)
        self.act_mode_cloud.setShortcut(QKeySequence("Ctrl+Shift+M"))
        self.act_mode_cloud.setToolTip(
            "다중 클릭으로 영역을 지정(빗금 표시)하고 더블클릭/우클릭/시작점 클릭/Enter로 클라우드 마크 생성 (Ctrl+Shift+M)"
        )

        self.act_mode_highlight = QAction(ModernIcons.get_icon("highlight"), "하이라이트", self)
        self.act_mode_highlight.setCheckable(True)
        self.act_mode_highlight.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self.act_mode_highlight.setToolTip("드래그하여 텍스트 형광펜 하이라이트 추가 (Ctrl+Shift+H)")

        self.act_mode_stamp = QAction(ModernIcons.get_icon("stamp"), "당초/변경 마크", self)
        self.act_mode_stamp.setCheckable(True)
        self.act_mode_stamp.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.act_mode_stamp.setToolTip(
            "페이지 우측 상단에 빨간색 굵은 사각형 테두리의 당초/변경 마크를 추가합니다 (Ctrl+Shift+D)"
        )

        for action in (
            self.act_mode_view,
            self.act_mode_text,
            self.act_mode_box,
            self.act_mode_cloud,
            self.act_mode_highlight,
            self.act_mode_stamp,
        ):
            self.mode_group.addAction(action)
            seg_layout.addWidget(self._make_tool_btn(action, "SegmentToolBtn"))

        row_layout.addWidget(segment_frame)
        row_layout.addStretch(1)

        self.act_toggle_bookmark = QAction(ModernIcons.get_icon("bookmark"), "책갈피", self)
        self.act_toggle_bookmark.setCheckable(True)
        self.act_toggle_bookmark.setChecked(True)
        self.act_toggle_bookmark.setShortcut(QKeySequence("Ctrl+B"))
        self.act_toggle_bookmark.setToolTip("오른쪽 책갈피 창 열기/숨기기 (Ctrl+B)")
        self.act_toggle_bookmark.triggered.connect(self.set_bookmark_panel_visible)
        row_layout.addWidget(self._make_tool_btn(self.act_toggle_bookmark))

        row_layout.addWidget(self._make_divider())

        self.act_about = QAction(ModernIcons.get_icon("info"), f"정보 ({APP_VERSION})", self)
        self.act_about.setToolTip("프로그램 버전 정보 및 변경 이력(Change Log) 보기 (Ctrl+F1)")
        self.act_about.triggered.connect(self.show_about_dialog)
        row_layout.addWidget(self._make_tool_btn(self.act_about))

        toolbar.addWidget(row_widget)

        self.act_mode_view.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.VIEW)
        )
        self.act_mode_text.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.TEXT_EDIT)
        )
        self.act_mode_box.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.BOX_REVIEW)
        )
        self.act_mode_cloud.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.CLOUD_MARK)
        )
        self.act_mode_highlight.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.HIGHLIGHT)
        )
        self.act_mode_stamp.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.STAMP_MARK)
        )

    # -------------------------------------------------------------------------
    # 1-2. 상단 메뉴 표시줄 (파일(F), 편집(E), 보기(V), 작업(W), 도움말(H))
    # -------------------------------------------------------------------------
    def _init_menubar(self):
        menubar = self.menuBar()

        # 1) 파일(F): 열기, 저장, 새이름으로, 인쇄, 인쇄설정, 문서닫기, 종료
        self.menu_file = menubar.addMenu("파일(&F)")

        self.act_save_as = QAction(ModernIcons.get_icon("save"), "새이름으로(&A)...", self)
        self.act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.act_save_as.setToolTip("현재 PDF 문서를 새 이름으로 저장 (Ctrl+Shift+S)")

        self.act_print = QAction("인쇄(&P)...", self)
        self.act_print.setShortcut(QKeySequence.StandardKey.Print)
        self.act_print.setToolTip("문서 인쇄 (Ctrl+P)")

        self.act_print_setup = QAction("인쇄설정(&R)...", self)
        self.act_print_setup.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self.act_print_setup.setToolTip("인쇄 페이지 및 프린터 설정 (Ctrl+Shift+P)")

        self.act_close_doc = QAction("문서닫기(&C)", self)
        self.act_close_doc.setShortcut(QKeySequence("Ctrl+W"))
        self.act_close_doc.setToolTip("현재 열려 있는 PDF 문서 닫기 (Ctrl+W)")

        self.act_exit = QAction("종료(&X)", self)
        self.act_exit.setShortcuts([QKeySequence("Alt+F4"), QKeySequence("Ctrl+Q")])
        self.act_exit.setToolTip("프로그램 종료 (Alt+F4)")
        self.act_exit.triggered.connect(self.close)

        self.menu_file.addAction(self.act_open)
        self.menu_file.addAction(self.act_save)
        self.menu_file.addAction(self.act_save_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_print)
        self.menu_file.addAction(self.act_print_setup)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_close_doc)
        self.menu_file.addAction(self.act_exit)

        # 2) 편집(E): 실행취소, 다시실행, 찾기, 텍스트수정
        self.menu_edit = menubar.addMenu("편집(&E)")

        self.act_find = QAction("찾기(&F)...", self)
        self.act_find.setShortcut(QKeySequence.StandardKey.Find)
        self.act_find.setToolTip("문서 내 텍스트 검색 및 이동 (Ctrl+F)")

        self.menu_edit.addAction(self.act_undo)
        self.menu_edit.addAction(self.act_redo)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_find)
        self.menu_edit.addAction(self.act_mode_text)

        # 3) 보기(V): 확대, 축소, 연속 스크롤, 표시/숨기기
        self.menu_view = menubar.addMenu("보기(&V)")
        self.menu_view.addAction(self.act_zoom_in)
        self.menu_view.addAction(self.act_zoom_out)
        self.menu_view.addAction(self.act_continuous_scroll)
        self.menu_view.addSeparator()

        self.menu_show_hide = self.menu_view.addMenu("표시/숨기기(&S)")

        self.act_toggle_left_sidebar = QAction("좌측 페이지 목록(&L)", self)
        self.act_toggle_left_sidebar.setCheckable(True)
        self.act_toggle_left_sidebar.setChecked(True)
        self.act_toggle_left_sidebar.setShortcut(QKeySequence("F9"))
        self.act_toggle_left_sidebar.triggered.connect(self.set_left_sidebar_visible)

        self.act_toggle_toolbar = QAction("상단 도구 모음(&T)", self)
        self.act_toggle_toolbar.setCheckable(True)
        self.act_toggle_toolbar.setChecked(True)
        self.act_toggle_toolbar.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.act_toggle_toolbar.triggered.connect(self.set_toolbar_visible)

        self.act_toggle_tool_prop_bar = QAction("도구 속성 설정 바(&P)", self)
        self.act_toggle_tool_prop_bar.setCheckable(True)
        self.act_toggle_tool_prop_bar.setChecked(True)
        self.act_toggle_tool_prop_bar.setToolTip(
            "박스 검토·클라우드 마크·하이라이트·당초/변경 마크 선택 시 상단 세부 설정 바 자동 표시"
        )
        self.act_toggle_tool_prop_bar.triggered.connect(self.set_tool_prop_bar_enabled)

        self.menu_show_hide.addAction(self.act_toggle_left_sidebar)
        self.menu_show_hide.addAction(self.act_toggle_bookmark)
        self.menu_show_hide.addAction(self.act_toggle_toolbar)
        self.menu_show_hide.addAction(self.act_toggle_tool_prop_bar)

        # 4) 작업(W): 박스검토, 클라우드마크, 하이라이트, 당초/변경 마크, 쪽번호넣기
        self.menu_work = menubar.addMenu("작업(&W)")

        self.act_stamp_batch_dialog = QAction(
            ModernIcons.get_icon("stamp"), "당초/변경 마크 페이지별 설정(&G)...", self
        )
        self.act_stamp_batch_dialog.setToolTip(
            "페이지별로 당초/변경 마크를 개별 선택하거나 박스·테두리·폰트 스타일을 설정하여 넣습니다"
        )
        self.act_stamp_batch_dialog.triggered.connect(
            self.stamp_batch_dialog_requested.emit
        )

        self.act_insert_page_numbers = QAction("쪽번호넣기(&N)...", self)
        self.act_insert_page_numbers.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.act_insert_page_numbers.setToolTip("문서 페이지에 쪽번호 삽입 (Ctrl+Shift+N)")

        self.menu_work.addAction(self.act_mode_box)
        self.menu_work.addAction(self.act_mode_cloud)
        self.menu_work.addAction(self.act_mode_highlight)
        self.menu_work.addAction(self.act_mode_stamp)
        self.menu_work.addAction(self.act_stamp_batch_dialog)
        self.menu_work.addSeparator()
        self.menu_work.addAction(self.act_insert_page_numbers)

        # 5) 도움말(H): 도움말, 프로그램 정보
        self.menu_help = menubar.addMenu("도움말(&H)")

        self.act_help = QAction(ModernIcons.get_icon("info"), "도움말(&H)", self)
        self.act_help.setShortcut(QKeySequence("F1"))
        self.act_help.setToolTip("기능 안내 및 단축키 도움말 보기 (F1)")
        self.act_help.triggered.connect(self.show_help_dialog)

        self.act_about_menu = QAction(
            ModernIcons.get_icon("info"), "프로그램 정보(&A)", self
        )
        self.act_about_menu.setShortcut(QKeySequence("Ctrl+F1"))
        self.act_about_menu.setToolTip("프로그램 버전 정보 및 변경 이력 보기 (Ctrl+F1)")
        self.act_about_menu.triggered.connect(self.show_about_dialog)

        self.menu_help.addAction(self.act_help)
        self.menu_help.addAction(self.act_about_menu)

        # 메뉴 표시줄 우측 코너에 [연속 스크롤: ON / OFF] 원클릭 토글 스위치 배치
        self.btn_menubar_continuous = QPushButton("연속 스크롤: ON", menubar)
        self.btn_menubar_continuous.setObjectName("MenuBarScrollToggleBtn")
        self.btn_menubar_continuous.setCheckable(True)
        self.btn_menubar_continuous.setChecked(True)
        self.btn_menubar_continuous.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menubar_continuous.setToolTip(
            "클릭하여 연속 스크롤 보기(ON) ↔ 1페이지씩 보기(OFF) 즉시 전환 (Ctrl+Shift+C)"
        )
        self.btn_menubar_continuous.toggled.connect(self.set_continuous_scroll_mode)
        menubar.setCornerWidget(
            self.btn_menubar_continuous, Qt.Corner.TopRightCorner
        )

    # -------------------------------------------------------------------------
    # 2. 중앙 영역 (좌측 드래그앤드롭 썸네일 + 중앙 흰색 캔버스 + 우측 책갈피 창)
    # -------------------------------------------------------------------------
    def _init_central_area(self):
        central_wrapper = QWidget(self)
        root_h_layout = QHBoxLayout(central_wrapper)
        root_h_layout.setContentsMargins(0, 0, 0, 0)
        root_h_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, central_wrapper)
        self.splitter.setChildrenCollapsible(False)

        # --- [1] 좌측 페이지 썸네일 사이드바 ---
        self.left_panel = QFrame()
        self.left_panel.setObjectName("LeftSidebar")
        self.left_panel.setMinimumWidth(190)
        self.left_panel.setMaximumWidth(270)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(8, 10, 8, 10)
        left_layout.setSpacing(6)

        self.sidebar_title = QLabel("페이지 목록")
        self.sidebar_title.setObjectName("SidebarTitle")
        self.sidebar_title.setToolTip(
            "드래그 앤 드롭: 페이지 이동 / Ctrl+클릭: 다중 선택 / Shift+클릭: 구간 선택"
        )
        left_layout.addWidget(self.sidebar_title)

        self.thumbnail_list = DraggableThumbnailList()
        self.thumbnail_list.setObjectName("ThumbnailList")
        self.thumbnail_list.setSpacing(6)
        self.thumbnail_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.thumbnail_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.thumbnail_list.customContextMenuRequested.connect(self._show_thumbnail_context_menu)
        self.thumbnail_list.itemSelectionChanged.connect(self._on_thumbnail_selection_changed)
        self.thumbnail_list.pages_drop_requested.connect(self.pages_drop_requested.emit)
        self.thumbnail_list.external_pdf_dropped.connect(self.external_pdf_dropped.emit)
        left_layout.addWidget(self.thumbnail_list, stretch=1)

        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.setSpacing(6)

        self.btn_rotate = QPushButton("회전")
        self.btn_rotate.setIcon(ModernIcons.get_icon("rotate"))
        self.btn_rotate.setIconSize(QSize(14, 14))
        self.btn_rotate.setObjectName("SmallSidebarBtn")
        self.btn_rotate.setToolTip("선택한 페이지 90도 회전")

        self.btn_delete = QPushButton("삭제")
        self.btn_delete.setIcon(ModernIcons.get_icon("trash"))
        self.btn_delete.setIconSize(QSize(14, 14))
        self.btn_delete.setObjectName("DeleteSidebarBtn")
        self.btn_delete.setToolTip("선택한 페이지 삭제")

        bottom_btn_layout.addWidget(self.btn_rotate)
        bottom_btn_layout.addWidget(self.btn_delete)
        left_layout.addLayout(bottom_btn_layout)

        self.btn_merge = QPushButton("다른 PDF 합병")
        self.btn_merge.setIcon(ModernIcons.get_icon("merge"))
        self.btn_merge.setIconSize(QSize(14, 14))
        self.btn_merge.setObjectName("SmallSidebarBtn")
        self.btn_merge.setToolTip(
            "다른 PDF 파일의 전체 또는 선택한 페이지들을 현재 문서의 원하는 위치에 합병(삽입)합니다"
        )
        self.btn_merge.clicked.connect(lambda: self.merge_pages_requested.emit(-1))
        left_layout.addWidget(self.btn_merge)

        self.btn_extract = QPushButton("선택 페이지 추출 저장")
        self.btn_extract.setIcon(ModernIcons.get_icon("extract"))
        self.btn_extract.setIconSize(QSize(14, 14))
        self.btn_extract.setObjectName("SmallSidebarBtn")
        self.btn_extract.setToolTip(
            "Ctrl 또는 Shift로 선택한 페이지들을 별도의 새 PDF 파일로 추출하여 저장합니다"
        )
        left_layout.addWidget(self.btn_extract)

        # --- [2] 중앙 메인 PDF 뷰어 (상단 컨텍스트 도구 속성 바 + 슬림 찾기 바 + 흰색 바탕 스크롤 영역) ---
        self.center_panel = QWidget()
        center_vbox = QVBoxLayout(self.center_panel)
        center_vbox.setContentsMargins(0, 0, 0, 0)
        center_vbox.setSpacing(0)

        self.tool_prop_frame = self._build_tool_property_bar()

        self.find_bar_frame = QFrame()
        self.find_bar_frame.setObjectName("FindBarFrame")
        self.find_bar_frame.setFixedHeight(42)
        find_layout = QHBoxLayout(self.find_bar_frame)
        find_layout.setContentsMargins(14, 5, 14, 5)
        find_layout.setSpacing(8)

        lbl_find_title = QLabel("찾기:")
        lbl_find_title.setObjectName("FindTitleLabel")

        self.find_input = FindLineEdit()
        self.find_input.setObjectName("FindInputEdit")
        self.find_input.setPlaceholderText(
            "검색어 입력 (Enter: 다음, Shift+Enter: 이전, Esc: 닫기)"
        )
        self.find_input.setMinimumWidth(220)
        self.find_input.setMaximumWidth(340)
        self.find_input.setClearButtonEnabled(True)
        self.find_input.textChanged.connect(lambda _: self._find_debounce_timer.start())
        self.find_input.find_next_requested.connect(self._on_find_next_triggered)
        self.find_input.find_prev_requested.connect(self._on_find_prev_triggered)
        self.find_input.find_close_requested.connect(self.hide_find_bar)

        self.find_count_label = QLabel("0 / 0")
        self.find_count_label.setObjectName("FindCountLabel")
        self.find_count_label.setMinimumWidth(56)
        self.find_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_find_prev = QPushButton("▲ 이전")
        self.btn_find_prev.setObjectName("FindNavBtn")
        self.btn_find_prev.setFixedSize(58, 28)
        self.btn_find_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_find_prev.setToolTip("이전 일치 항목 (Shift+Enter)")
        self.btn_find_prev.clicked.connect(self._on_find_prev_triggered)

        self.btn_find_next = QPushButton("▼ 다음")
        self.btn_find_next.setObjectName("FindNavBtn")
        self.btn_find_next.setFixedSize(58, 28)
        self.btn_find_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_find_next.setToolTip("다음 일치 항목 (Enter / F3)")
        self.btn_find_next.clicked.connect(self._on_find_next_triggered)

        self.btn_find_close = QPushButton("✕")
        self.btn_find_close.setObjectName("FindCloseBtn")
        self.btn_find_close.setFixedSize(28, 28)
        self.btn_find_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_find_close.setToolTip("찾기 바 닫기 및 하이라이트 해제 (Esc)")
        self.btn_find_close.clicked.connect(self.hide_find_bar)

        find_layout.addWidget(lbl_find_title)
        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.find_count_label)
        find_layout.addWidget(self.btn_find_prev)
        find_layout.addWidget(self.btn_find_next)
        find_layout.addStretch(1)
        find_layout.addWidget(self.btn_find_close)
        self.find_bar_frame.setVisible(False)

        self.scroll_area = ZoomScrollArea()
        self.scroll_area.setObjectName("CanvasScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.viewport_changed.connect(self._on_viewport_changed)

        self.canvas_container = QWidget()
        self.canvas_container.setObjectName("CanvasContainer")
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(
            24, self.CANVAS_MARGIN_TOP, 24, self.CANVAS_MARGIN_BOTTOM
        )
        self.canvas_layout.setSpacing(self.CANVAS_PAGE_SPACING)
        self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_canvas_label = InteractivePageLabel(page_index=0)
        self.page_canvas_label.page_canvas_interacted.connect(
            self.page_canvas_interacted.emit
        )
        self.page_canvas_label.cloud_polygon_completed.connect(
            self.cloud_polygon_completed.emit
        )
        self.page_canvas_label.stamp_mark_clicked.connect(
            self.stamp_mark_clicked.emit
        )
        self.page_canvas_label.page_clicked.connect(self._on_page_slot_clicked)
        self.canvas_layout.addWidget(
            self.page_canvas_label, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        self.scroll_area.setWidget(self.canvas_container)

        center_vbox.addWidget(self.tool_prop_frame)
        center_vbox.addWidget(self.find_bar_frame)
        center_vbox.addWidget(self.scroll_area, stretch=1)

        # --- [3] 우측 책갈피(Bookmark) 패널 ---
        self.right_bookmark_panel = QFrame()
        self.right_bookmark_panel.setObjectName("RightBookmarkPanel")
        self.right_bookmark_panel.setMinimumWidth(210)
        self.right_bookmark_panel.setMaximumWidth(300)

        right_layout = QVBoxLayout(self.right_bookmark_panel)
        right_layout.setContentsMargins(8, 10, 8, 10)
        right_layout.setSpacing(8)

        bm_header_layout = QHBoxLayout()
        bm_title = QLabel("책갈피")
        bm_title.setObjectName("SidebarTitle")

        self.btn_close_bookmark = QPushButton("숨기기")
        self.btn_close_bookmark.setIcon(ModernIcons.get_icon("next"))
        self.btn_close_bookmark.setIconSize(QSize(12, 12))
        self.btn_close_bookmark.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.btn_close_bookmark.setObjectName("SmallSidebarBtn")
        self.btn_close_bookmark.setToolTip("책갈피 창을 오른쪽으로 숨깁니다")
        self.btn_close_bookmark.setFixedWidth(68)
        self.btn_close_bookmark.clicked.connect(
            lambda: self.set_bookmark_panel_visible(False)
        )

        bm_header_layout.addWidget(bm_title)
        bm_header_layout.addStretch()
        bm_header_layout.addWidget(self.btn_close_bookmark)
        right_layout.addLayout(bm_header_layout)

        self.bookmark_list = QListWidget()
        self.bookmark_list.setObjectName("BookmarkList")
        self.bookmark_list.itemClicked.connect(self._on_bookmark_item_clicked)
        right_layout.addWidget(self.bookmark_list, stretch=1)

        bm_btn_layout = QHBoxLayout()
        bm_btn_layout.setSpacing(6)

        self.btn_add_bookmark = QPushButton("페이지 추가")
        self.btn_add_bookmark.setIcon(ModernIcons.get_icon("plus"))
        self.btn_add_bookmark.setIconSize(QSize(13, 13))
        self.btn_add_bookmark.setObjectName("SmallSidebarBtn")
        self.btn_add_bookmark.setToolTip("현재 보고 있는 페이지를 책갈피에 추가합니다")
        self.btn_add_bookmark.clicked.connect(self.bookmark_add_requested.emit)

        self.btn_del_bookmark = QPushButton("삭제")
        self.btn_del_bookmark.setIcon(ModernIcons.get_icon("trash"))
        self.btn_del_bookmark.setIconSize(QSize(13, 13))
        self.btn_del_bookmark.setObjectName("DeleteSidebarBtn")
        self.btn_del_bookmark.setToolTip("선택한 책갈피 항목을 삭제합니다")
        self.btn_del_bookmark.clicked.connect(self._on_delete_bookmark_clicked)

        bm_btn_layout.addWidget(self.btn_add_bookmark, stretch=2)
        bm_btn_layout.addWidget(self.btn_del_bookmark, stretch=1)
        right_layout.addLayout(bm_btn_layout)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.center_panel)
        self.splitter.addWidget(self.right_bookmark_panel)
        self.splitter.setSizes([205, 875, 230])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)

        # --- [4] 책갈피 창이 숨겨졌을 때 우측 가장자리에 나타나는 [◀ 책갈피] 열기 탭 ---
        self.right_edge_bar = QFrame()
        self.right_edge_bar.setStyleSheet("background-color: #ffffff; border-left: 1px solid #e4e4e7;")
        edge_layout = QVBoxLayout(self.right_edge_bar)
        edge_layout.setContentsMargins(2, 16, 0, 16)

        self.btn_open_bookmark_tab = QPushButton("◀\n책\n갈\n피")
        self.btn_open_bookmark_tab.setObjectName("BookmarkOpenTabBtn")
        self.btn_open_bookmark_tab.setFixedWidth(26)
        self.btn_open_bookmark_tab.setToolTip("책갈피 창 열기")
        self.btn_open_bookmark_tab.clicked.connect(
            lambda: self.set_bookmark_panel_visible(True)
        )
        edge_layout.addWidget(self.btn_open_bookmark_tab, alignment=Qt.AlignmentFlag.AlignTop)
        edge_layout.addStretch()

        self.right_edge_bar.setVisible(False)

        root_h_layout.addWidget(self.splitter, stretch=1)
        root_h_layout.addWidget(self.right_edge_bar, stretch=0)

        self.setCentralWidget(central_wrapper)

    # -------------------------------------------------------------------------
    # 3. 하단 상태표시줄 (StatusBar) 구성
    # -------------------------------------------------------------------------
    def _init_statusbar(self):
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.status_page_label = QLabel("페이지: 0 / 0")
        self.status_page_label.setObjectName("StatusPageLabel")

        self.status_zoom_label = QLabel("배율: 100%")
        self.status_zoom_label.setObjectName("StatusZoomLabel")

        self.status_mode_title = QLabel("현재 모드:")
        self.status_mode_title.setObjectName("StatusModeLabel")

        self.status_mode_badge = QLabel(self.current_mode.value)
        self.status_mode_badge.setObjectName("StatusModeBadge")

        self.status_bar.addWidget(self.status_page_label)
        self.status_bar.addWidget(self.status_zoom_label)
        self.status_bar.addPermanentWidget(self.status_mode_title)
        self.status_bar.addPermanentWidget(self.status_mode_badge)

    # -------------------------------------------------------------------------
    # 2-2. 상단 컨텍스트 도구 속성 설정 바 (박스 검토 / 클라우드 마크 / 하이라이트 / 당초·변경 마크)
    # -------------------------------------------------------------------------
    def _build_tool_property_bar(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("ToolPropBarFrame")
        frame.setFixedHeight(44)
        root_h = QHBoxLayout(frame)
        root_h.setContentsMargins(12, 4, 12, 4)
        root_h.setSpacing(0)

        self.tool_prop_stack = QStackedWidget(frame)
        root_h.addWidget(self.tool_prop_stack)

        # ---- [Page 0] 박스 검토 (테두리 두께, 색상) ----
        page_box = QWidget()
        hb = QHBoxLayout(page_box)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(8)

        lbl_box_badge = QLabel("박스 검토 설정")
        lbl_box_badge.setObjectName("ToolPropTitleBadge")
        hb.addWidget(lbl_box_badge)

        lbl_box_col = QLabel("테두리 색상:")
        lbl_box_col.setObjectName("ToolPropFieldLabel")
        hb.addWidget(lbl_box_col)

        self.btn_box_color = QPushButton("색상 선택")
        self.btn_box_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_box_color.setFixedHeight(26)
        self.btn_box_color.clicked.connect(lambda: self._pick_tool_color("box_color"))
        hb.addWidget(self.btn_box_color)

        for hex_c, rgb_c, tip in (
            ("#ef4444", (1.0, 0.0, 0.0), "빨강"),
            ("#2563eb", (0.15, 0.39, 0.92), "파랑"),
            ("#16a34a", (0.09, 0.64, 0.29), "초록"),
            ("#18181b", (0.09, 0.09, 0.11), "검정"),
        ):
            sw = self._make_color_preset_btn(
                hex_c, tip, lambda _=False, c=rgb_c: self._set_tool_color("box_color", c)
            )
            hb.addWidget(sw)

        hb.addWidget(self._make_divider())

        lbl_box_w = QLabel("테두리 두께:")
        lbl_box_w.setObjectName("ToolPropFieldLabel")
        hb.addWidget(lbl_box_w)

        self.spin_box_width = QDoubleSpinBox()
        self.spin_box_width.setObjectName("ToolPropSpin")
        self.spin_box_width.setRange(0.5, 12.0)
        self.spin_box_width.setSingleStep(0.5)
        self.spin_box_width.setDecimals(1)
        self.spin_box_width.setValue(float(self._tool_style["box_width"]))
        self.spin_box_width.setSuffix(" pt")
        self.spin_box_width.setFixedWidth(74)
        self.spin_box_width.valueChanged.connect(self._on_tool_prop_ui_changed)
        hb.addWidget(self.spin_box_width)

        hb.addStretch(1)
        lbl_box_hint = QLabel("마우스로 영역을 드래그하여 검토용 사각형 박스를 추가합니다")
        lbl_box_hint.setObjectName("ToolPropHintLabel")
        hb.addWidget(lbl_box_hint)
        self.tool_prop_stack.addWidget(page_box)

        # ---- [Page 1] 클라우드 마크 (선 색상, 선 두께, 구름 크기) ----
        page_cloud = QWidget()
        hc = QHBoxLayout(page_cloud)
        hc.setContentsMargins(0, 0, 0, 0)
        hc.setSpacing(8)

        lbl_cloud_badge = QLabel("클라우드 마크 설정")
        lbl_cloud_badge.setObjectName("ToolPropTitleBadge")
        hc.addWidget(lbl_cloud_badge)

        lbl_cloud_col = QLabel("선 색상:")
        lbl_cloud_col.setObjectName("ToolPropFieldLabel")
        hc.addWidget(lbl_cloud_col)

        self.btn_cloud_color = QPushButton("색상 선택")
        self.btn_cloud_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cloud_color.setFixedHeight(26)
        self.btn_cloud_color.clicked.connect(lambda: self._pick_tool_color("cloud_color"))
        hc.addWidget(self.btn_cloud_color)

        for hex_c, rgb_c, tip in (
            ("#ed3333", (0.93, 0.20, 0.20), "빨강"),
            ("#2563eb", (0.15, 0.39, 0.92), "파랑"),
            ("#ea580c", (0.92, 0.35, 0.05), "주황"),
            ("#7c3aed", (0.49, 0.23, 0.93), "보라"),
        ):
            sw = self._make_color_preset_btn(
                hex_c, tip, lambda _=False, c=rgb_c: self._set_tool_color("cloud_color", c)
            )
            hc.addWidget(sw)

        hc.addWidget(self._make_divider())

        lbl_cloud_w = QLabel("선 두께:")
        lbl_cloud_w.setObjectName("ToolPropFieldLabel")
        hc.addWidget(lbl_cloud_w)

        self.spin_cloud_width = QDoubleSpinBox()
        self.spin_cloud_width.setObjectName("ToolPropSpin")
        self.spin_cloud_width.setRange(0.5, 10.0)
        self.spin_cloud_width.setSingleStep(0.5)
        self.spin_cloud_width.setDecimals(1)
        self.spin_cloud_width.setValue(float(self._tool_style["cloud_width"]))
        self.spin_cloud_width.setSuffix(" pt")
        self.spin_cloud_width.setFixedWidth(72)
        self.spin_cloud_width.valueChanged.connect(self._on_tool_prop_ui_changed)
        hc.addWidget(self.spin_cloud_width)

        lbl_cloud_scale = QLabel("클라우드 크기:")
        lbl_cloud_scale.setObjectName("ToolPropFieldLabel")
        hc.addWidget(lbl_cloud_scale)

        self.spin_cloud_scale = QDoubleSpinBox()
        self.spin_cloud_scale.setObjectName("ToolPropSpin")
        self.spin_cloud_scale.setRange(1.0, 5.0)
        self.spin_cloud_scale.setSingleStep(0.25)
        self.spin_cloud_scale.setDecimals(2)
        self.spin_cloud_scale.setValue(float(self._tool_style["cloud_scale"]))
        self.spin_cloud_scale.setSuffix(" 배")
        self.spin_cloud_scale.setFixedWidth(74)
        self.spin_cloud_scale.valueChanged.connect(self._on_tool_prop_ui_changed)
        hc.addWidget(self.spin_cloud_scale)

        hc.addStretch(1)
        lbl_cloud_hint = QLabel("다중 클릭으로 꼭짓점 지정 후 더블클릭·우클릭·Enter로 완성")
        lbl_cloud_hint.setObjectName("ToolPropHintLabel")
        hc.addWidget(lbl_cloud_hint)
        self.tool_prop_stack.addWidget(page_cloud)

        # ---- [Page 2] 하이라이트 (형광펜 색상) ----
        page_hl = QWidget()
        hh = QHBoxLayout(page_hl)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(8)

        lbl_hl_badge = QLabel("하이라이트 설정")
        lbl_hl_badge.setObjectName("ToolPropTitleBadge")
        hh.addWidget(lbl_hl_badge)

        lbl_hl_col = QLabel("형광펜 색상:")
        lbl_hl_col.setObjectName("ToolPropFieldLabel")
        hh.addWidget(lbl_hl_col)

        self.btn_hl_color = QPushButton("색상 선택")
        self.btn_hl_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hl_color.setFixedHeight(26)
        self.btn_hl_color.clicked.connect(lambda: self._pick_tool_color("highlight_color"))
        hh.addWidget(self.btn_hl_color)

        for hex_c, rgb_c, tip in (
            ("#fff200", (1.0, 0.95, 0.0), "노랑 (기본)"),
            ("#4ade80", (0.29, 0.87, 0.50), "형광 연두"),
            ("#38bdf8", (0.22, 0.74, 0.97), "형광 하늘"),
            ("#f472b6", (0.96, 0.45, 0.71), "형광 분홍"),
            ("#fb923c", (0.98, 0.57, 0.24), "형광 주황"),
        ):
            sw = self._make_color_preset_btn(
                hex_c, tip, lambda _=False, c=rgb_c: self._set_tool_color("highlight_color", c)
            )
            hh.addWidget(sw)

        hh.addStretch(1)
        lbl_hl_hint = QLabel("텍스트 위를 마우스로 드래그하여 형광펜 하이라이트를 적용합니다")
        lbl_hl_hint.setObjectName("ToolPropHintLabel")
        hh.addWidget(lbl_hl_hint)
        self.tool_prop_stack.addWidget(page_hl)

        # ---- [Page 3] 당초/변경 마크 (당초·변경 선택, 박스 크기, 테두리 색상·굵기, 글자 크기·폰트, 즉시/페이지별 넣기) ----
        page_stamp = QWidget()
        hs = QHBoxLayout(page_stamp)
        hs.setContentsMargins(0, 0, 0, 0)
        hs.setSpacing(6)

        lbl_stamp_badge = QLabel("당초/변경 마크")
        lbl_stamp_badge.setObjectName("ToolPropTitleBadge")
        hs.addWidget(lbl_stamp_badge)

        self.btn_stamp_type_orig = QPushButton("당초")
        self.btn_stamp_type_orig.setObjectName("StampTypeToggleBtn")
        self.btn_stamp_type_orig.setCheckable(True)
        self.btn_stamp_type_orig.setChecked(True)
        self.btn_stamp_type_orig.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_stamp_type_rev = QPushButton("변경")
        self.btn_stamp_type_rev.setObjectName("StampTypeToggleBtn")
        self.btn_stamp_type_rev.setCheckable(True)
        self.btn_stamp_type_rev.setCursor(Qt.CursorShape.PointingHandCursor)

        self.stamp_type_group = QButtonGroup(self)
        self.stamp_type_group.setExclusive(True)
        self.stamp_type_group.addButton(self.btn_stamp_type_orig, 0)
        self.stamp_type_group.addButton(self.btn_stamp_type_rev, 1)
        self.stamp_type_group.idClicked.connect(self._on_tool_prop_ui_changed)

        hs.addWidget(self.btn_stamp_type_orig)
        hs.addWidget(self.btn_stamp_type_rev)

        self.btn_stamp_apply_cur = QPushButton("현재 페이지에 넣기")
        self.btn_stamp_apply_cur.setObjectName("ToolPropActionBtn")
        self.btn_stamp_apply_cur.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stamp_apply_cur.setToolTip(
            "현재 보고 있는 페이지 우측 상단에 선택한 [당초] 또는 [변경] 마크를 즉시 넣습니다 (페이지를 직접 클릭해도 삽입됩니다)"
        )
        self.btn_stamp_apply_cur.clicked.connect(
            lambda: self.stamp_mark_clicked.emit(self.current_page_index)
        )
        hs.addWidget(self.btn_stamp_apply_cur)

        self.btn_stamp_open_batch = QPushButton("페이지별 설정...")
        self.btn_stamp_open_batch.setObjectName("ToolPropSecondaryBtn")
        self.btn_stamp_open_batch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stamp_open_batch.setToolTip(
            "전체 페이지 목록에서 페이지별로 [당초]/[변경]을 개별 지정하거나 여백·크기를 미리보기로 조정합니다"
        )
        self.btn_stamp_open_batch.clicked.connect(
            self.stamp_batch_dialog_requested.emit
        )
        hs.addWidget(self.btn_stamp_open_batch)

        hs.addWidget(self._make_divider())

        lbl_st_size = QLabel("박스(폭×높이):")
        lbl_st_size.setObjectName("ToolPropFieldLabel")
        hs.addWidget(lbl_st_size)

        self.spin_stamp_w = QSpinBox()
        self.spin_stamp_w.setObjectName("ToolPropSpin")
        self.spin_stamp_w.setRange(30, 260)
        self.spin_stamp_w.setValue(int(self._tool_style["stamp_box_w"]))
        self.spin_stamp_w.setSuffix("pt")
        self.spin_stamp_w.setFixedWidth(60)
        self.spin_stamp_w.setToolTip("사각형 박스 가로 폭 (pt)")
        self.spin_stamp_w.valueChanged.connect(self._on_tool_prop_ui_changed)
        hs.addWidget(self.spin_stamp_w)

        self.spin_stamp_h = QSpinBox()
        self.spin_stamp_h.setObjectName("ToolPropSpin")
        self.spin_stamp_h.setRange(18, 140)
        self.spin_stamp_h.setValue(int(self._tool_style["stamp_box_h"]))
        self.spin_stamp_h.setSuffix("pt")
        self.spin_stamp_h.setFixedWidth(58)
        self.spin_stamp_h.setToolTip("사각형 박스 세로 높이 (pt)")
        self.spin_stamp_h.valueChanged.connect(self._on_tool_prop_ui_changed)
        hs.addWidget(self.spin_stamp_h)

        lbl_st_border = QLabel("테두리:")
        lbl_st_border.setObjectName("ToolPropFieldLabel")
        hs.addWidget(lbl_st_border)

        self.btn_stamp_color = QPushButton("색상")
        self.btn_stamp_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stamp_color.setFixedHeight(26)
        self.btn_stamp_color.setToolTip("당초/변경 박스 테두리 및 글자 색상 선택")
        self.btn_stamp_color.clicked.connect(lambda: self._pick_tool_color("stamp_color"))
        hs.addWidget(self.btn_stamp_color)

        self.spin_stamp_border_w = QDoubleSpinBox()
        self.spin_stamp_border_w.setObjectName("ToolPropSpin")
        self.spin_stamp_border_w.setRange(0.5, 10.0)
        self.spin_stamp_border_w.setSingleStep(0.5)
        self.spin_stamp_border_w.setDecimals(1)
        self.spin_stamp_border_w.setValue(float(self._tool_style["stamp_border_width"]))
        self.spin_stamp_border_w.setSuffix("pt")
        self.spin_stamp_border_w.setFixedWidth(62)
        self.spin_stamp_border_w.setToolTip("테두리 선 굵기 (pt)")
        self.spin_stamp_border_w.valueChanged.connect(self._on_tool_prop_ui_changed)
        hs.addWidget(self.spin_stamp_border_w)

        lbl_st_font = QLabel("폰트:")
        lbl_st_font.setObjectName("ToolPropFieldLabel")
        hs.addWidget(lbl_st_font)

        self.combo_stamp_font = QComboBox()
        self.combo_stamp_font.setObjectName("ToolPropCombo")
        self.combo_stamp_font.setMinimumWidth(115)
        self.combo_stamp_font.setMaximumWidth(155)
        self.combo_stamp_font.addItem("★ 맑은 고딕 (Malgun Gothic)", "malgun")
        self.combo_stamp_font.currentIndexChanged.connect(self._on_tool_prop_ui_changed)
        hs.addWidget(self.combo_stamp_font)

        self.spin_stamp_fsize = QSpinBox()
        self.spin_stamp_fsize.setObjectName("ToolPropSpin")
        self.spin_stamp_fsize.setRange(8, 48)
        self.spin_stamp_fsize.setValue(int(self._tool_style["stamp_font_size"]))
        self.spin_stamp_fsize.setSuffix("pt")
        self.spin_stamp_fsize.setFixedWidth(58)
        self.spin_stamp_fsize.setToolTip("글자 크기 (pt)")
        self.spin_stamp_fsize.valueChanged.connect(self._on_tool_prop_ui_changed)
        hs.addWidget(self.spin_stamp_fsize)

        self.chk_stamp_bold = QCheckBox("굵게")
        self.chk_stamp_bold.setChecked(True)
        self.chk_stamp_bold.setStyleSheet("font-size: 11px; font-weight: 700; color: #334155;")
        self.chk_stamp_bold.toggled.connect(self._on_tool_prop_ui_changed)
        hs.addWidget(self.chk_stamp_bold)

        hs.addStretch(1)
        self.tool_prop_stack.addWidget(page_stamp)

        self._refresh_tool_color_buttons()
        frame.setVisible(False)
        return frame

    def _make_color_preset_btn(self, hex_color: str, tooltip: str, slot_fn) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(20, 20)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {hex_color}; border: 1.5px solid #94a3b8; border-radius: 4px; }}"
            f"QPushButton:hover {{ border: 2px solid #0f172a; }}"
        )
        btn.clicked.connect(slot_fn)
        return btn

    def _refresh_tool_color_buttons(self):
        for key, btn in (
            ("box_color", getattr(self, "btn_box_color", None)),
            ("cloud_color", getattr(self, "btn_cloud_color", None)),
            ("highlight_color", getattr(self, "btn_hl_color", None)),
            ("stamp_color", getattr(self, "btn_stamp_color", None)),
        ):
            if btn is None:
                continue
            rgb = self._tool_style.get(key, (1.0, 0.0, 0.0))
            r = int(round(rgb[0] * 255))
            g = int(round(rgb[1] * 255))
            b = int(round(rgb[2] * 255))
            hex_c = f"#{r:02X}{g:02X}{b:02X}"
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            fg = "#18181b" if luminance > 155 else "#ffffff"
            btn.setText(hex_c)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_c}; color: {fg}; border: 1px solid #94a3b8; "
                f"border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 700; }}"
            )

    def _set_tool_color(self, style_key: str, rgb_tuple: Tuple[float, float, float]):
        self._tool_style[style_key] = rgb_tuple
        self._refresh_tool_color_buttons()
        self._sync_tool_style_to_canvases()
        self.tool_style_changed.emit(self.get_tool_style())

    def _pick_tool_color(self, style_key: str):
        cur = self._tool_style.get(style_key, (1.0, 0.0, 0.0))
        init_col = QColor(
            int(round(cur[0] * 255)),
            int(round(cur[1] * 255)),
            int(round(cur[2] * 255)),
        )
        col = QColorDialog.getColor(init_col, self, "도구 색상 선택")
        if col.isValid():
            self._set_tool_color(style_key, (col.redF(), col.greenF(), col.blueF()))

    def _on_tool_prop_ui_changed(self, *_args):
        self._tool_style["box_width"] = float(self.spin_box_width.value())
        self._tool_style["cloud_width"] = float(self.spin_cloud_width.value())
        self._tool_style["cloud_scale"] = float(self.spin_cloud_scale.value())
        self._tool_style["stamp_text"] = (
            "변경" if self.btn_stamp_type_rev.isChecked() else "당초"
        )
        self._tool_style["stamp_box_w"] = float(self.spin_stamp_w.value())
        self._tool_style["stamp_box_h"] = float(self.spin_stamp_h.value())
        self._tool_style["stamp_border_width"] = float(self.spin_stamp_border_w.value())
        self._tool_style["stamp_font_key"] = str(
            self.combo_stamp_font.currentData() or "malgun"
        )
        self._tool_style["stamp_font_size"] = float(self.spin_stamp_fsize.value())
        self._tool_style["stamp_is_bold"] = bool(self.chk_stamp_bold.isChecked())
        self._sync_tool_style_to_canvases()
        self.tool_style_changed.emit(self.get_tool_style())

    def _sync_tool_style_to_canvases(self):
        if hasattr(self, "page_canvas_label"):
            self.page_canvas_label.set_tool_style(self._tool_style, self.current_zoom)
        for slot in self._page_slots:
            slot.set_tool_style(self._tool_style, self.current_zoom)

    def get_tool_style(self) -> Dict[str, object]:
        return dict(self._tool_style)

    def populate_stamp_font_choices(self, font_choices: List[Tuple[str, str]]):
        """시스템에서 탐색된 한글/영문 폰트 목록을 당초/변경 마크 속성 바의 폰트 콤보박스에 채웁니다."""
        if not hasattr(self, "combo_stamp_font") or not font_choices:
            return
        cur_key = str(self._tool_style.get("stamp_font_key", "malgun"))
        self.combo_stamp_font.blockSignals(True)
        self.combo_stamp_font.clear()
        matched_idx = 0
        for idx, (fkey, flabel) in enumerate(font_choices):
            self.combo_stamp_font.addItem(flabel, fkey)
            if fkey == cur_key:
                matched_idx = idx
        self.combo_stamp_font.setCurrentIndex(matched_idx)
        self._tool_style["stamp_font_key"] = str(
            self.combo_stamp_font.currentData() or "malgun"
        )
        self.combo_stamp_font.blockSignals(False)

    def sync_stamp_settings(self, settings: Dict[str, object]):
        """페이지별 당초/변경 설정 대화상자에서 변경한 스타일을 상단 속성 바에도 동기화합니다."""
        if "box_width" in settings:
            self._tool_style["stamp_box_w"] = float(settings["box_width"])
            self.spin_stamp_w.blockSignals(True)
            self.spin_stamp_w.setValue(int(round(float(settings["box_width"]))))
            self.spin_stamp_w.blockSignals(False)
        if "box_height" in settings:
            self._tool_style["stamp_box_h"] = float(settings["box_height"])
            self.spin_stamp_h.blockSignals(True)
            self.spin_stamp_h.setValue(int(round(float(settings["box_height"]))))
            self.spin_stamp_h.blockSignals(False)
        if "border_color" in settings:
            self._tool_style["stamp_color"] = settings["border_color"]
            self._refresh_tool_color_buttons()
        if "border_width" in settings:
            self._tool_style["stamp_border_width"] = float(settings["border_width"])
            self.spin_stamp_border_w.blockSignals(True)
            self.spin_stamp_border_w.setValue(float(settings["border_width"]))
            self.spin_stamp_border_w.blockSignals(False)
        if "font_key" in settings:
            fk = str(settings["font_key"])
            self._tool_style["stamp_font_key"] = fk
            self.combo_stamp_font.blockSignals(True)
            for i in range(self.combo_stamp_font.count()):
                if self.combo_stamp_font.itemData(i) == fk:
                    self.combo_stamp_font.setCurrentIndex(i)
                    break
            self.combo_stamp_font.blockSignals(False)
        if "font_size" in settings:
            self._tool_style["stamp_font_size"] = float(settings["font_size"])
            self.spin_stamp_fsize.blockSignals(True)
            self.spin_stamp_fsize.setValue(int(round(float(settings["font_size"]))))
            self.spin_stamp_fsize.blockSignals(False)
        if "is_bold" in settings:
            self._tool_style["stamp_is_bold"] = bool(settings["is_bold"])
            self.chk_stamp_bold.blockSignals(True)
            self.chk_stamp_bold.setChecked(bool(settings["is_bold"]))
            self.chk_stamp_bold.blockSignals(False)
        if "top_margin_pt" in settings:
            self._tool_style["stamp_top_margin"] = float(settings["top_margin_pt"])
        if "right_margin_pt" in settings:
            self._tool_style["stamp_right_margin"] = float(settings["right_margin_pt"])
        self._sync_tool_style_to_canvases()

    def set_tool_prop_bar_enabled(self, enabled: bool):
        self.tool_prop_bar_enabled = bool(enabled)
        if hasattr(self, "act_toggle_tool_prop_bar"):
            self.act_toggle_tool_prop_bar.blockSignals(True)
            self.act_toggle_tool_prop_bar.setChecked(self.tool_prop_bar_enabled)
            self.act_toggle_tool_prop_bar.blockSignals(False)
        self._update_tool_prop_bar_visibility()

    def _update_tool_prop_bar_visibility(self):
        if not hasattr(self, "tool_prop_frame"):
            return
        mode_to_stack = {
            CursorMode.BOX_REVIEW: 0,
            CursorMode.CLOUD_MARK: 1,
            CursorMode.HIGHLIGHT: 2,
            CursorMode.STAMP_MARK: 3,
        }
        if self.tool_prop_bar_enabled and self.current_mode in mode_to_stack:
            self.tool_prop_stack.setCurrentIndex(mode_to_stack[self.current_mode])
            self.tool_prop_frame.setVisible(True)
        else:
            self.tool_prop_frame.setVisible(False)

    # -------------------------------------------------------------------------
    # 패널/툴바 표시·숨기기 및 우측 책갈피(Bookmark) 데이터 표시 메서드
    # -------------------------------------------------------------------------
    def set_left_sidebar_visible(self, visible: bool):
        self.left_panel.setVisible(visible)
        if hasattr(self, "act_toggle_left_sidebar"):
            self.act_toggle_left_sidebar.setChecked(visible)

    def set_toolbar_visible(self, visible: bool):
        self.main_toolbar.setVisible(visible)
        if hasattr(self, "act_toggle_toolbar"):
            self.act_toggle_toolbar.setChecked(visible)

    def set_bookmark_panel_visible(self, visible: bool):
        self.right_bookmark_panel.setVisible(visible)
        self.right_edge_bar.setVisible(not visible)
        self.act_toggle_bookmark.setChecked(visible)

    def populate_bookmarks(self, bookmarks: List[Tuple[int, str, int]]):
        self.bookmark_list.clear()
        if not bookmarks:
            empty_item = QListWidgetItem("등록된 책갈피가 없습니다.")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setForeground(QColor("#a1a1aa"))
            self.bookmark_list.addItem(empty_item)
            return

        bm_icon = ModernIcons.get_icon("bookmark")
        for level, title, page_0 in bookmarks:
            indent = "   " * max(0, level - 1)
            display_text = f"{indent}{title}  (p.{page_0 + 1})"
            item = QListWidgetItem(bm_icon, display_text)
            item.setData(Qt.ItemDataRole.UserRole, page_0)
            self.bookmark_list.addItem(item)

    def _on_bookmark_item_clicked(self, item: QListWidgetItem):
        page_0 = item.data(Qt.ItemDataRole.UserRole)
        if page_0 is not None:
            self.bookmark_selected.emit(int(page_0))

    def _on_delete_bookmark_clicked(self):
        row = self.bookmark_list.currentRow()
        if row >= 0:
            item = self.bookmark_list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) is not None:
                self.bookmark_delete_requested.emit(row)

    # -------------------------------------------------------------------------
    # 좌측 썸네일 렌더링 및 다중 선택(Ctrl / Shift) 하이라이트 제어
    # -------------------------------------------------------------------------
    def populate_thumbnails(
        self,
        pixmaps: List[Optional[QPixmap]],
        selected_indices: Optional[List[int]] = None,
        current_index: int = 0,
    ):
        self.thumbnail_list.clear()
        for idx, pix in enumerate(pixmaps):
            item = QListWidgetItem()
            widget = ThumbnailItemWidget(idx + 1, pix)
            item.setSizeHint(widget.sizeHint())
            self.thumbnail_list.addItem(item)
            self.thumbnail_list.setItemWidget(item, widget)

        if selected_indices:
            self.thumbnail_list.clearSelection()
            for r in selected_indices:
                if 0 <= r < len(pixmaps):
                    self.thumbnail_list.item(r).setSelected(True)
            if 0 <= current_index < len(pixmaps):
                self.thumbnail_list.setCurrentItem(
                    self.thumbnail_list.item(current_index),
                    self.thumbnail_list.selectionModel().SelectionFlag.NoUpdate,
                )
            self._on_thumbnail_selection_changed()
        elif 0 <= current_index < len(pixmaps):
            self.thumbnail_list.setCurrentRow(current_index)
            self._on_thumbnail_selection_changed()
        else:
            self.sidebar_title.setText("페이지 목록")

    def update_single_thumbnail(self, page_index: int, pixmap: Optional[QPixmap]):
        if not (0 <= page_index < self.thumbnail_list.count()):
            return
        item = self.thumbnail_list.item(page_index)
        widget = self.thumbnail_list.itemWidget(item)
        if isinstance(widget, ThumbnailItemWidget):
            widget.set_thumbnail_pixmap(pixmap)
            item.setSizeHint(widget.sizeHint())

    def get_selected_page_indices(self) -> List[int]:
        selected_rows = sorted(
            idx.row() for idx in self.thumbnail_list.selectedIndexes()
        )
        if not selected_rows and 0 <= self.current_page < self.thumbnail_list.count():
            return [self.current_page]
        return selected_rows

    def _on_thumbnail_selection_changed(self):
        selected_rows = set(
            idx.row() for idx in self.thumbnail_list.selectedIndexes()
        )
        for idx in range(self.thumbnail_list.count()):
            item = self.thumbnail_list.item(idx)
            widget = self.thumbnail_list.itemWidget(item)
            if isinstance(widget, ThumbnailItemWidget):
                widget.set_selected(idx in selected_rows)

        count = len(selected_rows)
        if count > 1:
            self.sidebar_title.setText(f"페이지 목록 ({count}개 선택됨)")
            self.btn_extract.setText(f"선택 페이지 추출 저장 ({count}p)")
        else:
            self.sidebar_title.setText("페이지 목록")
            self.btn_extract.setText("선택 페이지 추출 저장")

    def _update_thumbnail_highlight(self, current_row: int):
        self._on_thumbnail_selection_changed()

    # -------------------------------------------------------------------------
    # UI 제어 및 표시 메서드 (가상화 연속 스크롤 + 단일 페이지 모드 완벽 호환)
    # -------------------------------------------------------------------------
    def set_cursor_mode(self, mode: CursorMode):
        self.current_mode = mode
        self.status_mode_badge.setText(mode.value)
        self.page_canvas_label.set_cursor_mode(mode)
        for slot in self._page_slots:
            slot.set_cursor_mode(mode)
        self._update_tool_prop_bar_visibility()
        self.mode_changed.emit(mode)

    def set_continuous_scroll_mode(self, enabled: bool):
        """메뉴 표시줄 우측 [연속 스크롤: ON/OFF] 스위치 및 [보기 -> 연속 스크롤] 메뉴로 즉시 전환"""
        self.continuous_scroll = bool(enabled)
        self.scroll_area.continuous_scroll_mode = self.continuous_scroll

        if self.act_continuous_scroll.isChecked() != self.continuous_scroll:
            self.act_continuous_scroll.blockSignals(True)
            self.act_continuous_scroll.setChecked(self.continuous_scroll)
            self.act_continuous_scroll.blockSignals(False)
        self.act_continuous_scroll.setText(
            "연속 스크롤: 켜짐(&C)"
            if self.continuous_scroll
            else "연속 스크롤: 꺼짐(&C)"
        )

        if hasattr(self, "btn_menubar_continuous"):
            if self.btn_menubar_continuous.isChecked() != self.continuous_scroll:
                self.btn_menubar_continuous.blockSignals(True)
                self.btn_menubar_continuous.setChecked(self.continuous_scroll)
                self.btn_menubar_continuous.blockSignals(False)
            self.btn_menubar_continuous.setText(
                "연속 스크롤: ON"
                if self.continuous_scroll
                else "연속 스크롤: OFF (1쪽 보기)"
            )

        self.continuous_mode_toggled.emit(self.continuous_scroll)

    def _on_page_slot_clicked(self, page_index: int):
        self.scroll_area.setFocus()
        if self.continuous_scroll and 0 <= page_index < len(self._page_sizes):
            if page_index != self.current_page_index:
                self.current_page_index = page_index
                self.current_page_scrolled.emit(page_index)

    def update_page_status(self, current_page: int, total_pages: int, zoom: float = 1.0):
        self.current_page = current_page
        self.current_page_index = max(0, current_page - 1)
        self.total_pages = total_pages
        self.current_zoom = float(zoom)
        self.status_page_label.setText(f"페이지: {current_page} / {total_pages}")
        self.status_zoom_label.setText(f"배율: {int(round(zoom * 100))}%")
        self._sync_tool_style_to_canvases()

    def display_page_pixmap(
        self, pixmap: Optional[QPixmap], page_index: Optional[int] = None
    ):
        """단일 페이지 보기 모드(기존 버전 방식)에서 1페이지를 표시합니다."""
        if pixmap and not pixmap.isNull():
            for slot in self._page_slots:
                slot.clear()
                slot.has_pdf_page = False
                slot.setVisible(False)
            self._page_sizes.clear()
            self._rendered_pages.clear()

            if page_index is not None:
                self.page_canvas_label.page_index = page_index
            self.page_canvas_label.has_pdf_page = True
            self.page_canvas_label.setText("")
            self.page_canvas_label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )
            self.page_canvas_label.setPixmap(pixmap)
            self.page_canvas_label.setFixedSize(pixmap.size())
            self.page_canvas_label.setVisible(True)
            self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.canvas_container.setMinimumSize(
                pixmap.width() + 48,
                pixmap.height() + self.CANVAS_MARGIN_TOP + self.CANVAS_MARGIN_BOTTOM,
            )
        else:
            self._setup_empty_state()

    def setup_continuous_pages(
        self,
        page_sizes: List[Tuple[int, int]],
        current_page: int = 0,
        scroll_to_current: bool = True,
    ):
        """
        가상화(Lazy Rendering) 연속 스크롤 모드를 위해 전체 페이지의 빈 슬롯(Placeholder)만 배치합니다.
        실제 픽스맵은 현재 뷰포트에 보이는 페이지들에 대해서만 온디맨드로 렌더링됩니다.
        """
        if not page_sizes:
            self._setup_empty_state()
            return

        self._programmatic_scroll = True
        self._page_sizes = list(page_sizes)
        self._rendered_pages.clear()
        self.total_pages = len(page_sizes)
        self.current_page_index = max(0, min(current_page, len(page_sizes) - 1))

        self.page_canvas_label.clear()
        self.page_canvas_label.has_pdf_page = False
        self.page_canvas_label.setVisible(False)
        self.canvas_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )

        # 필요한 만큼 슬롯 위젯 생성 (기존 위젯 재사용으로 오버헤드 최소화)
        while len(self._page_slots) < len(page_sizes):
            idx = len(self._page_slots)
            slot = InteractivePageLabel(page_index=idx)
            slot.set_cursor_mode(self.current_mode)
            slot.set_tool_style(self._tool_style, self.current_zoom)
            slot.page_canvas_interacted.connect(self.page_canvas_interacted.emit)
            slot.cloud_polygon_completed.connect(self.cloud_polygon_completed.emit)
            slot.stamp_mark_clicked.connect(self.stamp_mark_clicked.emit)
            slot.page_clicked.connect(self._on_page_slot_clicked)
            self._page_slots.append(slot)
            self.canvas_layout.addWidget(slot, alignment=Qt.AlignmentFlag.AlignHCenter)

        for idx, slot in enumerate(self._page_slots):
            if idx < len(page_sizes):
                w, h = page_sizes[idx]
                slot.page_index = idx
                slot.has_pdf_page = True
                slot.set_cursor_mode(self.current_mode)
                slot.set_tool_style(self._tool_style, self.current_zoom)
                slot.clear()
                slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
                slot.setText(f"Page {idx + 1}")
                slot.setFixedSize(w, h)
                slot.setVisible(True)
            else:
                slot.clear()
                slot.has_pdf_page = False
                slot.setVisible(False)

        total_h = (
            self.CANVAS_MARGIN_TOP
            + self.CANVAS_MARGIN_BOTTOM
            + sum(h for _, h in page_sizes)
            + max(0, len(page_sizes) - 1) * self.CANVAS_PAGE_SPACING
        )
        max_w = max((w for w, _ in page_sizes), default=595) + 48
        self.canvas_container.setMinimumSize(max_w, total_h)
        self.canvas_layout.activate()
        self.canvas_container.adjustSize()

        if scroll_to_current:
            target_y = self._get_page_top_y(self.current_page_index) - 12
            self.scroll_area.verticalScrollBar().setValue(max(0, target_y))

        self._programmatic_scroll = False
        self.refresh_visible_pages()

    def _get_page_top_y(self, page_index: int) -> int:
        if not self._page_sizes or page_index <= 0:
            return self.CANVAS_MARGIN_TOP
        clamped = min(page_index, len(self._page_sizes) - 1)
        y = self.CANVAS_MARGIN_TOP
        for i in range(clamped):
            y += self._page_sizes[i][1] + self.CANVAS_PAGE_SPACING
        return y

    def scroll_to_page(self, page_index: int):
        """연속 스크롤 모드에서 지정한 페이지 위치로 스크롤바를 이동하고 가시 페이지를 렌더링합니다."""
        if not self.continuous_scroll or not (0 <= page_index < len(self._page_sizes)):
            return
        self._programmatic_scroll = True
        self.current_page_index = page_index
        target_y = self._get_page_top_y(page_index) - 12
        self.scroll_area.verticalScrollBar().setValue(max(0, target_y))
        self._programmatic_scroll = False
        self.refresh_visible_pages()

    def set_continuous_page_pixmap(self, page_index: int, pixmap: Optional[QPixmap]):
        """가상화 연속 스크롤의 특정 페이지 슬롯에 렌더링된 QPixmap을 설정합니다."""
        if not (0 <= page_index < len(self._page_slots)):
            return
        slot = self._page_slots[page_index]
        if pixmap and not pixmap.isNull():
            slot.setText("")
            slot.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            slot.setPixmap(pixmap)
            slot.setFixedSize(pixmap.size())
            self._rendered_pages.add(page_index)
        else:
            slot.clear()
            slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slot.setText(f"Page {page_index + 1}")
            self._rendered_pages.discard(page_index)

    def invalidate_continuous_page(self, page_index: int):
        """특정 페이지가 편집되었을 때 해당 페이지 슬롯만 즉시 재렌더링합니다."""
        if not self.continuous_scroll or not (0 <= page_index < len(self._page_sizes)):
            return
        self._rendered_pages.discard(page_index)
        self.page_render_requested.emit(page_index)

    def get_rendered_page_count(self) -> int:
        """현재 메모리에 QPixmap이 로드되어 있는 활성 페이지 수를 반환합니다 (검증/테스트용)."""
        if not self.continuous_scroll:
            return 1 if self.page_canvas_label.has_pdf_page else 0
        return len(self._rendered_pages)

    def _on_viewport_changed(self):
        if not self.continuous_scroll or not self._page_sizes:
            return
        self.refresh_visible_pages()

    def refresh_visible_pages(self):
        """
        현재 스크롤바 위치와 뷰포트 높이를 기준으로:
        1) 화면(버퍼 포함)에 보이는 페이지만 렌더링 요청하고 화면 밖 페이지는 즉시 메모리에서 해제합니다.
        2) 사용자가 스크롤 중이면 화면 중앙에 걸친 페이지를 감지하여 current_page_scrolled 시그널을 방출합니다.
        """
        if not self.continuous_scroll or not self._page_sizes:
            return

        vbar = self.scroll_area.verticalScrollBar()
        view_top = vbar.value()
        viewport_h = max(1, self.scroll_area.viewport().height())
        view_bottom = view_top + viewport_h

        # 위아래 여유 버퍼 (뷰포트 높이의 75%, 최소 500px) 내의 페이지만 메모리에 유지
        buffer_px = max(500, int(viewport_h * 0.75))
        render_top = view_top - buffer_px
        render_bottom = view_bottom + buffer_px

        # 현재 읽고 있는 기준 Y선 (뷰포트 상단에서 38% 지점)
        probe_y = view_top + int(viewport_h * 0.38)
        best_page = self.current_page_index
        best_dist = float("inf")

        visible_indices: Set[int] = set()
        y_cursor = self.CANVAS_MARGIN_TOP

        for idx, (_w, h) in enumerate(self._page_sizes):
            p_top = y_cursor
            p_bottom = p_top + h
            y_cursor = p_bottom + self.CANVAS_PAGE_SPACING

            if p_bottom >= render_top and p_top <= render_bottom:
                visible_indices.add(idx)

            if p_top <= probe_y <= p_bottom:
                best_page = idx
                best_dist = 0.0
            else:
                dist = min(abs(probe_y - p_top), abs(probe_y - p_bottom))
                if dist < best_dist:
                    best_dist = dist
                    best_page = idx

        # 화면 밖으로 벗어난 페이지의 QPixmap 즉시 메모리 해제
        for rendered_idx in list(self._rendered_pages):
            if rendered_idx not in visible_indices:
                if 0 <= rendered_idx < len(self._page_slots):
                    slot = self._page_slots[rendered_idx]
                    slot.clear()
                    slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    slot.setText(f"Page {rendered_idx + 1}")
                self._rendered_pages.discard(rendered_idx)

        # 새로 화면 안에 들어온 페이지 온디맨드 렌더링 요청
        for vis_idx in sorted(visible_indices):
            if vis_idx not in self._rendered_pages:
                self.page_render_requested.emit(vis_idx)

        # 사용자 스크롤에 의해 현재 페이지가 바뀌었으면 컨트롤러에 알림
        if not self._programmatic_scroll and best_page != self.current_page_index:
            self.current_page_index = best_page
            self.current_page_scrolled.emit(best_page)

    # -------------------------------------------------------------------------
    # 상단 슬림 찾기 바 (Find Bar) 및 검색어 하이라이트 오버레이 제어
    # -------------------------------------------------------------------------
    def _emit_find_query(self):
        self.find_query_changed.emit(self.find_input.text())

    def _on_find_next_triggered(self):
        if self._find_debounce_timer.isActive():
            self._find_debounce_timer.stop()
            self._emit_find_query()
        self.find_next_requested.emit()

    def _on_find_prev_triggered(self):
        if self._find_debounce_timer.isActive():
            self._find_debounce_timer.stop()
            self._emit_find_query()
        self.find_prev_requested.emit()

    def show_find_bar(self):
        self.find_bar_frame.setVisible(True)
        self.find_input.setFocus()
        self.find_input.selectAll()
        if self.find_input.text().strip():
            self._emit_find_query()

    def hide_find_bar(self):
        if self._find_debounce_timer.isActive():
            self._find_debounce_timer.stop()
        self.find_bar_frame.setVisible(False)
        self.clear_search_highlights()
        self.find_closed.emit()
        self.scroll_area.setFocus()

    def set_find_status(self, current_one_based: int, total_count: int, has_query: bool = True):
        if not has_query:
            self.find_count_label.setText("0 / 0")
            self.find_count_label.setStyleSheet("color: #475569;")
        elif total_count == 0:
            self.find_count_label.setText("0 / 0 (없음)")
            self.find_count_label.setStyleSheet("color: #dc2626; font-weight: 700;")
        else:
            self.find_count_label.setText(f"{current_one_based} / {total_count}")
            self.find_count_label.setStyleSheet("color: #1d4ed8; font-weight: 700;")

        has_matches = total_count > 0
        self.btn_find_prev.setEnabled(has_matches)
        self.btn_find_next.setEnabled(has_matches)

    def clear_search_highlights(self):
        self.page_canvas_label.set_search_highlights([], None)
        for slot in self._page_slots:
            slot.set_search_highlights([], None)

    def update_search_highlights(
        self,
        page_rects_map: Dict[int, List[QRectF]],
        active_page: int = -1,
        active_rect: Optional[QRectF] = None,
    ):
        """PDF 픽스맵 재렌더링 없이 각 페이지 슬롯의 검색 오버레이 사각형만 갱신합니다."""
        if not self.continuous_scroll:
            cur_idx = self.page_canvas_label.page_index
            rects = page_rects_map.get(cur_idx, [])
            act = active_rect if active_page == cur_idx else None
            self.page_canvas_label.set_search_highlights(rects, act)
        else:
            for idx, slot in enumerate(self._page_slots):
                if idx < len(self._page_sizes):
                    rects = page_rects_map.get(idx, [])
                    act = active_rect if active_page == idx else None
                    slot.set_search_highlights(rects, act)

    def scroll_to_search_rect(self, page_index: int, rect: QRectF):
        """현재 포커스된 검색어 사각형이 뷰포트 중앙에 오도록 스크롤바를 이동합니다."""
        vbar = self.scroll_area.verticalScrollBar()
        viewport_h = max(1, self.scroll_area.viewport().height())

        if self.continuous_scroll and 0 <= page_index < len(self._page_sizes):
            self._programmatic_scroll = True
            self.current_page_index = page_index
            page_top_y = self._get_page_top_y(page_index)
            match_center_y = page_top_y + int(rect.center().y())
            target_y = max(0, match_center_y - viewport_h // 2)
            vbar.setValue(target_y)
            self._programmatic_scroll = False
            self.refresh_visible_pages()
        else:
            if vbar.maximum() > 0:
                target_y = max(0, int(rect.center().y()) - viewport_h // 2)
                vbar.setValue(target_y)

    def _setup_empty_state(self):
        self._page_sizes.clear()
        self._rendered_pages.clear()
        for slot in self._page_slots:
            slot.clear()
            slot.has_pdf_page = False
            slot.setVisible(False)

        self.page_canvas_label.page_index = 0
        self.page_canvas_label.has_pdf_page = False
        self.page_canvas_label.clear()
        self.page_canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_canvas_label.setFixedSize(595, 842)
        self.page_canvas_label.setText(
            "PDF 페이지 캔버스 영역\n\n상단 [열기] 버튼을 눌러 PDF 문서를 불러오세요."
        )
        self.page_canvas_label.setVisible(True)
        self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_container.setMinimumSize(640, 890)
        self.populate_bookmarks([])

    def _show_thumbnail_context_menu(self, pos):
        item = self.thumbnail_list.itemAt(pos)
        menu = QMenu(self)

        if not item:
            act_merge_here = QAction(
                ModernIcons.get_icon("merge"), "다른 PDF 합병...", self
            )
            act_merge_here.triggered.connect(
                lambda: self.merge_pages_requested.emit(-1)
            )
            menu.addAction(act_merge_here)
            menu.exec(self.thumbnail_list.mapToGlobal(pos))
            return

        row = self.thumbnail_list.row(item)
        count = self.thumbnail_list.count()
        selected_pages = self.get_selected_page_indices()
        sel_count = len(selected_pages)

        act_merge_before = QAction(
            ModernIcons.get_icon("merge"),
            f"{row + 1}페이지 앞에 다른 PDF 합병...",
            self,
        )
        act_merge_after = QAction(
            ModernIcons.get_icon("merge"),
            f"{row + 1}페이지 뒤에 다른 PDF 합병...",
            self,
        )
        act_extract = QAction(
            ModernIcons.get_icon("extract"),
            f"선택 페이지 추출 저장 ({sel_count}페이지)...",
            self,
        )
        act_up = QAction("위로 이동", self)
        act_down = QAction("아래로 이동", self)
        act_rot = QAction(ModernIcons.get_icon("rotate"), f"90도 회전 ({sel_count}페이지)", self)
        act_del = QAction(ModernIcons.get_icon("trash"), f"페이지 삭제 ({sel_count}페이지)", self)

        act_up.setEnabled(sel_count == 1 and row > 0)
        act_down.setEnabled(sel_count == 1 and row < count - 1)
        act_del.setEnabled(count - sel_count >= 1)

        act_merge_before.triggered.connect(
            lambda: self.merge_pages_requested.emit(row)
        )
        act_merge_after.triggered.connect(
            lambda: self.merge_pages_requested.emit(row + 1)
        )
        act_extract.triggered.connect(self.btn_extract.click)
        act_up.triggered.connect(lambda: self.page_move_requested.emit(row, row - 1))
        act_down.triggered.connect(lambda: self.page_move_requested.emit(row, row + 1))
        act_rot.triggered.connect(self.btn_rotate.click)
        act_del.triggered.connect(self.btn_delete.click)

        menu.addAction(act_merge_before)
        menu.addAction(act_merge_after)
        menu.addSeparator()
        menu.addAction(act_extract)
        menu.addSeparator()
        menu.addAction(act_up)
        menu.addAction(act_down)
        menu.addSeparator()
        menu.addAction(act_rot)
        menu.addAction(act_del)
        menu.exec(self.thumbnail_list.mapToGlobal(pos))


if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from src.controllers.main_controller import MainController

    app = QApplication(sys.argv)
    window = MainWindow()
    controller = MainController(window)
    window.show()
    sys.exit(app.exec())
