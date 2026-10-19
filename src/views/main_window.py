import sys
from enum import Enum
from typing import Callable, List, Optional, Tuple
from PyQt6.QtCore import Qt, QSize, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QKeySequence,
    QPixmap,
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
    QMouseEvent,
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
    QStatusBar,
    QFrame,
    QMenu,
)
from src.__version__ import APP_VERSION, get_window_title
from src.utils.modern_icons import ModernIcons
from src.views.dialogs.about_dialog import AboutDialog


class CursorMode(Enum):
    """마우스 커서 및 편집 도구 모드 정의"""
    VIEW = "선택/보기 모드"
    TEXT_EDIT = "텍스트 수정 모드"
    BOX_REVIEW = "박스 검토 모드"
    HIGHLIGHT = "하이라이트 모드"


MODERN_QSS = """
/* 전체 기본 폰트 및 흰색 바탕 */
QMainWindow {
    background-color: #ffffff;
    font-family: "Malgun Gothic", "Segoe UI", sans-serif;
    font-size: 12px;
    color: #18181b;
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
    PDF 페이지 Pixmap을 표시하고, 마우스 드래그(또는 클릭) 영역을 실시간으로 그리며
    완료 시 화면 좌표(QRectF)와 현재 모드를 방출하는 캔버스 라벨 위젯
    """

    canvas_interacted = pyqtSignal(QRectF, CursorMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PageCanvasLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.cursor_mode: CursorMode = CursorMode.VIEW
        self.has_pdf_page: bool = False

        self._dragging: bool = False
        self._start_pos: Optional[QPointF] = None
        self._current_pos: Optional[QPointF] = None

    def set_cursor_mode(self, mode: CursorMode):
        self.cursor_mode = mode
        if mode == CursorMode.VIEW:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == CursorMode.TEXT_EDIT:
            self.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if (
            self.has_pdf_page
            and self.cursor_mode != CursorMode.VIEW
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._dragging = True
            self._start_pos = event.position()
            self._current_pos = event.position()
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self._current_pos = event.position()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._current_pos = event.position()

            if self._start_pos is not None and self._current_pos is not None:
                rect = QRectF(self._start_pos, self._current_pos).normalized()
                if self.cursor_mode == CursorMode.TEXT_EDIT:
                    self.canvas_interacted.emit(rect, self.cursor_mode)
                else:
                    if rect.width() >= 5.0 and rect.height() >= 5.0:
                        self.canvas_interacted.emit(rect, self.cursor_mode)

            self._start_pos = None
            self._current_pos = None
            self.update()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._dragging and self._start_pos is not None and self._current_pos is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(self._start_pos, self._current_pos).normalized()

            if self.cursor_mode == CursorMode.BOX_REVIEW:
                pen = QPen(QColor(239, 68, 68, 230), 2, Qt.PenStyle.SolidLine)
                brush = QBrush(QColor(239, 68, 68, 35))
            elif self.cursor_mode == CursorMode.HIGHLIGHT:
                pen = QPen(QColor(234, 179, 8, 220), 1.5, Qt.PenStyle.DashLine)
                brush = QBrush(QColor(250, 204, 21, 95))
            else:
                pen = QPen(QColor(39, 39, 42, 220), 1.5, Qt.PenStyle.DashLine)
                brush = QBrush(QColor(39, 39, 42, 30))

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(rect)
            painter.end()


class ZoomScrollArea(QScrollArea):
    """Ctrl + 마우스 휠 확대/축소를 지원하는 스크롤 영역"""

    wheel_zoom_requested = pyqtSignal(float)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.wheel_zoom_requested.emit(0.15)
            elif delta < 0:
                self.wheel_zoom_requested.emit(-0.15)
            event.accept()
        else:
            super().wheelEvent(event)


class MainWindow(QMainWindow):
    """PDF 편집기 메인 윈도우 (드래그앤드롭 구분선 이동 + 다중 페이지 선택/추출 + 다른 PDF 합병 포함)"""

    mode_changed = pyqtSignal(CursorMode)
    page_move_requested = pyqtSignal(int, int)
    pages_drop_requested = pyqtSignal(list, int)  # (selected_indices, insert_before_slot)
    merge_pages_requested = pyqtSignal(int)       # preset_slot (-1이면 기본 위치)
    external_pdf_dropped = pyqtSignal(str, int)   # (source_pdf_path, insert_before_slot)
    bookmark_selected = pyqtSignal(int)
    bookmark_add_requested = pyqtSignal()
    bookmark_delete_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(get_window_title())
        self.resize(1320, 860)

        self.current_mode = CursorMode.VIEW
        self.current_page = 0
        self.total_pages = 0
        self._close_confirm_callback: Optional[Callable[[], bool]] = None

        self._init_toolbar()
        self._init_central_area()
        self._init_statusbar()
        self.setStyleSheet(MODERN_QSS)

        self._setup_empty_state()

    def show_about_dialog(self):
        """도움말/정보(About) 및 버전 변경 이력(Change Log) 팝업 창을 표시합니다."""
        dialog = AboutDialog(parent=self)
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
        self, action: QAction, object_name: str = "ModernToolBtn"
    ) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName(object_name)
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setIconSize(QSize(16, 16))
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

        row_layout.addWidget(self._make_tool_btn(self.act_open))
        row_layout.addWidget(self._make_tool_btn(self.act_save))
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

        row_layout.addWidget(self._make_tool_btn(self.act_undo))
        row_layout.addWidget(self._make_tool_btn(self.act_redo))
        row_layout.addWidget(self._make_divider())

        self.act_prev_page = QAction(ModernIcons.get_icon("prev"), "이전", self)
        self.act_prev_page.setShortcut(QKeySequence("PgUp"))
        self.act_prev_page.setToolTip("이전 페이지 (PageUp)")

        self.act_next_page = QAction(ModernIcons.get_icon("next"), "다음", self)
        self.act_next_page.setShortcut(QKeySequence("PgDown"))
        self.act_next_page.setToolTip("다음 페이지 (PageDown)")

        row_layout.addWidget(self._make_tool_btn(self.act_prev_page))
        row_layout.addWidget(self._make_tool_btn(self.act_next_page))
        row_layout.addWidget(self._make_divider())

        self.act_zoom_out = QAction(ModernIcons.get_icon("zoom_out"), "축소", self)
        self.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.act_zoom_out.setToolTip("화면 축소 (Ctrl+-)")

        self.act_zoom_in = QAction(ModernIcons.get_icon("zoom_in"), "확대", self)
        self.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.act_zoom_in.setToolTip("화면 확대 (Ctrl++)")

        row_layout.addWidget(self._make_tool_btn(self.act_zoom_out))
        row_layout.addWidget(self._make_tool_btn(self.act_zoom_in))
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
        self.act_mode_view.setToolTip("일반 선택 및 보기 모드")

        self.act_mode_text = QAction(ModernIcons.get_icon("text"), "텍스트 수정", self)
        self.act_mode_text.setCheckable(True)
        self.act_mode_text.setToolTip("클릭/드래그하여 텍스트 수정")

        self.act_mode_box = QAction(ModernIcons.get_icon("box"), "박스 검토", self)
        self.act_mode_box.setCheckable(True)
        self.act_mode_box.setToolTip("드래그하여 검토용 사각형 마크업 추가")

        self.act_mode_highlight = QAction(ModernIcons.get_icon("highlight"), "하이라이트", self)
        self.act_mode_highlight.setCheckable(True)
        self.act_mode_highlight.setToolTip("드래그하여 텍스트 형광펜 하이라이트 추가")

        for action in (
            self.act_mode_view,
            self.act_mode_text,
            self.act_mode_box,
            self.act_mode_highlight,
        ):
            self.mode_group.addAction(action)
            seg_layout.addWidget(self._make_tool_btn(action, "SegmentToolBtn"))

        row_layout.addWidget(segment_frame)
        row_layout.addStretch(1)

        self.act_toggle_bookmark = QAction(ModernIcons.get_icon("bookmark"), "책갈피", self)
        self.act_toggle_bookmark.setCheckable(True)
        self.act_toggle_bookmark.setChecked(True)
        self.act_toggle_bookmark.setToolTip("오른쪽 책갈피 창 열기/숨기기")
        self.act_toggle_bookmark.triggered.connect(self.set_bookmark_panel_visible)
        row_layout.addWidget(self._make_tool_btn(self.act_toggle_bookmark))

        row_layout.addWidget(self._make_divider())

        self.act_about = QAction(ModernIcons.get_icon("info"), f"정보 ({APP_VERSION})", self)
        self.act_about.setShortcut(QKeySequence("F1"))
        self.act_about.setToolTip("프로그램 버전 정보 및 변경 이력(Change Log) 보기 (F1)")
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
        self.act_mode_highlight.triggered.connect(
            lambda: self.set_cursor_mode(CursorMode.HIGHLIGHT)
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

        # --- [2] 중앙 메인 PDF 뷰어 (흰색 바탕) ---
        self.scroll_area = ZoomScrollArea()
        self.scroll_area.setObjectName("CanvasScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas_container = QWidget()
        self.canvas_container.setObjectName("CanvasContainer")
        canvas_layout = QVBoxLayout(self.canvas_container)
        canvas_layout.setContentsMargins(24, 24, 24, 24)
        canvas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_canvas_label = InteractivePageLabel()
        canvas_layout.addWidget(self.page_canvas_label)
        self.scroll_area.setWidget(self.canvas_container)

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
        self.splitter.addWidget(self.scroll_area)
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
    # 우측 책갈피(Bookmark) 창 열기/숨기기 및 데이터 표시 메서드
    # -------------------------------------------------------------------------
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
    # UI 제어 및 표시 메서드
    # -------------------------------------------------------------------------
    def set_cursor_mode(self, mode: CursorMode):
        self.current_mode = mode
        self.status_mode_badge.setText(mode.value)
        self.page_canvas_label.set_cursor_mode(mode)
        self.mode_changed.emit(mode)

    def update_page_status(self, current_page: int, total_pages: int, zoom: float = 1.0):
        self.current_page = current_page
        self.total_pages = total_pages
        self.status_page_label.setText(f"페이지: {current_page} / {total_pages}")
        self.status_zoom_label.setText(f"배율: {int(round(zoom * 100))}%")

    def display_page_pixmap(self, pixmap: Optional[QPixmap]):
        if pixmap and not pixmap.isNull():
            self.page_canvas_label.has_pdf_page = True
            self.page_canvas_label.setText("")
            self.page_canvas_label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )
            self.page_canvas_label.setPixmap(pixmap)
            self.page_canvas_label.setFixedSize(pixmap.size())
        else:
            self._setup_empty_state()

    def _setup_empty_state(self):
        self.page_canvas_label.has_pdf_page = False
        self.page_canvas_label.clear()
        self.page_canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_canvas_label.setFixedSize(595, 842)
        self.page_canvas_label.setText(
            "PDF 페이지 캔버스 영역\n\n상단 [열기] 버튼을 눌러 PDF 문서를 불러오세요."
        )
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
