from enum import Enum
from typing import Optional
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QMouseEvent
from PyQt6.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout


class ToolMode(Enum):
    NONE = "none"              # 일반 보기/스크롤 모드
    RED_BOX = "red_box"        # 빨간 사각형 마크업 추가 모드
    HIGHLIGHT = "highlight"    # 형광펜 하이라이트 추가 모드
    REDACT_AREA = "redact"     # 드래그 영역 텍스트 삭제/교체 모드


class PageCanvasLabel(QLabel):
    """실제 PDF 페이지 Pixmap을 표시하고 마우스 드래그 이벤트를 캡처하는 위젯"""

    # 드래그 완료 시 (화면 상의 QRectF, 현재 ToolMode) 시그널 방출
    area_selected = pyqtSignal(QRectF, ToolMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.tool_mode: ToolMode = ToolMode.NONE
        self._dragging: bool = False
        self._start_pos: Optional[QPointF] = None
        self._current_pos: Optional[QPointF] = None

    def set_tool_mode(self, mode: ToolMode):
        self.tool_mode = mode
        if mode == ToolMode.NONE:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if (
            self.tool_mode != ToolMode.NONE
            and event.button() == Qt.MouseButton.LeftButton
            and self.pixmap() is not None
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
            if self._start_pos and self._current_pos:
                rect = QRectF(self._start_pos, self._current_pos).normalized()
                # 너무 작은 클릭 실수는 무시 (최소 5x5 픽셀 이상)
                if rect.width() >= 5 and rect.height() >= 5:
                    self.area_selected.emit(rect, self.tool_mode)
            self._start_pos = None
            self._current_pos = None
            self.update()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._dragging and self._start_pos and self._current_pos:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = QRectF(self._start_pos, self._current_pos).normalized()

            if self.tool_mode == ToolMode.RED_BOX:
                pen = QPen(QColor(255, 0, 0, 220), 2, Qt.PenStyle.SolidLine)
                brush = QBrush(QColor(255, 0, 0, 30))
            elif self.tool_mode == ToolMode.HIGHLIGHT:
                pen = QPen(QColor(240, 200, 0, 200), 1, Qt.PenStyle.DashLine)
                brush = QBrush(QColor(255, 245, 0, 90))
            else:
                pen = QPen(QColor(0, 120, 215, 220), 2, Qt.PenStyle.DashLine)
                brush = QBrush(QColor(0, 120, 215, 40))

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(rect)
            painter.end()


class PDFCanvas(QScrollArea):
    """PDF 페이지를 감싸는 스크롤 가능 캔버스 뷰"""

    area_selected = pyqtSignal(QRectF, ToolMode)
    zoom_requested = pyqtSignal(float)  # Ctrl + 휠 줌 요청 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_label = PageCanvasLabel()
        self.page_label.area_selected.connect(self.area_selected.emit)
        self.container_layout.addWidget(self.page_label)

        self.setWidget(self.container)

    def display_pixmap(self, pixmap: Optional[QPixmap]):
        if pixmap:
            self.page_label.setPixmap(pixmap)
            self.page_label.setFixedSize(pixmap.size())
        else:
            self.page_label.clear()
            self.page_label.setFixedSize(0, 0)

    def set_tool_mode(self, mode: ToolMode):
        self.page_label.set_tool_mode(mode)

    def wheelEvent(self, event):
        """Ctrl 키를 누른 채 마우스 휠을 굴리면 확대/축소 시그널을 보냅니다."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_requested.emit(0.15)
            elif delta < 0:
                self.zoom_requested.emit(-0.15)
            event.accept()
        else:
            super().wheelEvent(event)
