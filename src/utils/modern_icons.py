from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QPen,
    QColor,
    QPainterPath,
)


class ModernIcons:
    """
    모던 그레이스케일(Monochrome) 미니멀 라인 벡터 아이콘 생성 유틸리티
    (컬러 이모지 대신 세련된 1.5px 스트로크 벡터 아이콘을 고해상도로 렌더링)
    """

    COLOR_NORMAL = "#3f3f46"    # 기본 차콜 그레이
    COLOR_ACTIVE = "#18181b"    # 선택/활성 딥 블랙
    COLOR_DISABLED = "#cbd5e1"  # 비활성 라이트 그레이

    @classmethod
    def get_icon(cls, name: str) -> QIcon:
        """Normal / Disabled / Active 상태별 픽스맵이 모두 포함된 QIcon 반환"""
        icon = QIcon()
        pix_normal = cls._render_pixmap(name, cls.COLOR_NORMAL)
        pix_disabled = cls._render_pixmap(name, cls.COLOR_DISABLED)
        pix_active = cls._render_pixmap(name, cls.COLOR_ACTIVE)

        icon.addPixmap(pix_normal, QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(pix_active, QIcon.Mode.Normal, QIcon.State.On)
        icon.addPixmap(pix_active, QIcon.Mode.Active, QIcon.State.Off)
        icon.addPixmap(pix_active, QIcon.Mode.Active, QIcon.State.On)
        icon.addPixmap(pix_disabled, QIcon.Mode.Disabled, QIcon.State.Off)
        return icon

    @classmethod
    def _render_pixmap(cls, name: str, hex_color: str, size: int = 16) -> QPixmap:
        scale = 2
        px_size = size * scale
        pixmap = QPixmap(px_size, px_size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.scale(scale, scale)

        pen = QPen(QColor(hex_color), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if name == "open":
            path = QPainterPath()
            path.moveTo(2.0, 4.5)
            path.lineTo(6.0, 4.5)
            path.lineTo(7.5, 6.2)
            path.lineTo(14.0, 6.2)
            path.lineTo(14.0, 12.5)
            path.lineTo(2.0, 12.5)
            path.closeSubpath()
            painter.drawPath(path)

        elif name == "save":
            path = QPainterPath()
            path.addRoundedRect(QRectF(2.5, 2.5, 11.0, 11.0), 1.5, 1.5)
            painter.drawPath(path)
            painter.drawRect(QRectF(5.0, 2.5, 5.5, 3.8))
            painter.drawRect(QRectF(4.5, 9.0, 7.0, 4.5))

        elif name == "undo":
            painter.drawLine(QPointF(3.0, 6.0), QPointF(6.0, 3.0))
            painter.drawLine(QPointF(3.0, 6.0), QPointF(6.0, 9.0))
            path = QPainterPath()
            path.moveTo(3.2, 6.0)
            path.lineTo(9.5, 6.0)
            path.cubicTo(12.5, 6.0, 13.5, 8.0, 13.5, 10.0)
            path.cubicTo(13.5, 12.0, 12.0, 13.0, 9.5, 13.0)
            path.lineTo(6.5, 13.0)
            painter.drawPath(path)

        elif name == "redo":
            painter.drawLine(QPointF(13.0, 6.0), QPointF(10.0, 3.0))
            painter.drawLine(QPointF(13.0, 6.0), QPointF(10.0, 9.0))
            path = QPainterPath()
            path.moveTo(12.8, 6.0)
            path.lineTo(6.5, 6.0)
            path.cubicTo(3.5, 6.0, 2.5, 8.0, 2.5, 10.0)
            path.cubicTo(2.5, 12.0, 4.0, 13.0, 6.5, 13.0)
            path.lineTo(9.5, 13.0)
            painter.drawPath(path)

        elif name == "prev":
            painter.drawLine(QPointF(10.0, 3.5), QPointF(5.5, 8.0))
            painter.drawLine(QPointF(5.5, 8.0), QPointF(10.0, 12.5))

        elif name == "next":
            painter.drawLine(QPointF(6.0, 3.5), QPointF(10.5, 8.0))
            painter.drawLine(QPointF(10.5, 8.0), QPointF(6.0, 12.5))

        elif name == "zoom_out":
            painter.drawEllipse(QRectF(2.5, 2.5, 8.5, 8.5))
            painter.drawLine(QPointF(9.8, 9.8), QPointF(13.5, 13.5))
            painter.drawLine(QPointF(4.8, 6.75), QPointF(8.7, 6.75))

        elif name == "zoom_in":
            painter.drawEllipse(QRectF(2.5, 2.5, 8.5, 8.5))
            painter.drawLine(QPointF(9.8, 9.8), QPointF(13.5, 13.5))
            painter.drawLine(QPointF(4.8, 6.75), QPointF(8.7, 6.75))
            painter.drawLine(QPointF(6.75, 4.8), QPointF(6.75, 8.7))

        elif name == "view":
            path = QPainterPath()
            path.moveTo(4.0, 2.5)
            path.lineTo(4.0, 12.5)
            path.lineTo(6.8, 9.8)
            path.lineTo(9.0, 13.5)
            path.lineTo(10.6, 12.7)
            path.lineTo(8.4, 9.0)
            path.lineTo(12.0, 9.0)
            path.closeSubpath()
            painter.drawPath(path)

        elif name == "text":
            painter.drawLine(QPointF(3.5, 3.5), QPointF(12.5, 3.5))
            painter.drawLine(QPointF(3.5, 3.5), QPointF(3.5, 5.2))
            painter.drawLine(QPointF(12.5, 3.5), QPointF(12.5, 5.2))
            painter.drawLine(QPointF(8.0, 3.5), QPointF(8.0, 12.5))
            painter.drawLine(QPointF(6.0, 12.5), QPointF(10.0, 12.5))

        elif name == "box":
            painter.drawRect(QRectF(3.0, 3.5, 10.0, 9.0))
            painter.fillRect(QRectF(2.0, 2.5, 2.2, 2.2), QColor(hex_color))
            painter.fillRect(QRectF(11.8, 2.5, 2.2, 2.2), QColor(hex_color))
            painter.fillRect(QRectF(2.0, 11.3, 2.2, 2.2), QColor(hex_color))
            painter.fillRect(QRectF(11.8, 11.3, 2.2, 2.2), QColor(hex_color))

        elif name == "highlight":
            path = QPainterPath()
            path.moveTo(9.5, 2.5)
            path.lineTo(13.0, 6.0)
            path.lineTo(7.5, 11.5)
            path.lineTo(4.0, 11.5)
            path.lineTo(4.0, 8.0)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(2.5, 13.5), QPointF(13.5, 13.5))

        elif name == "bookmark":
            path = QPainterPath()
            path.moveTo(4.0, 2.5)
            path.lineTo(12.0, 2.5)
            path.lineTo(12.0, 13.5)
            path.lineTo(8.0, 10.2)
            path.lineTo(4.0, 13.5)
            path.closeSubpath()
            painter.drawPath(path)

        elif name == "rotate":
            painter.drawArc(QRectF(3.0, 3.0, 10.0, 10.0), 30 * 16, 270 * 16)
            painter.drawLine(QPointF(12.2, 2.8), QPointF(12.8, 6.0))
            painter.drawLine(QPointF(9.6, 5.4), QPointF(12.8, 6.0))

        elif name == "trash":
            painter.drawLine(QPointF(3.0, 4.5), QPointF(13.0, 4.5))
            painter.drawLine(QPointF(6.0, 2.8), QPointF(10.0, 2.8))
            painter.drawRoundedRect(QRectF(4.2, 4.5, 7.6, 9.0), 1.0, 1.0)
            painter.drawLine(QPointF(6.8, 6.8), QPointF(6.8, 11.2))
            painter.drawLine(QPointF(9.2, 6.8), QPointF(9.2, 11.2))

        elif name == "extract":
            # 문서에서 외부로 추출/내보내기 화살표 아이콘
            path = QPainterPath()
            path.moveTo(9.0, 2.5)
            path.lineTo(4.0, 2.5)
            path.lineTo(4.0, 13.5)
            path.lineTo(11.0, 13.5)
            path.lineTo(11.0, 10.5)
            painter.drawPath(path)
            painter.drawLine(QPointF(7.5, 8.0), QPointF(14.0, 8.0))
            painter.drawLine(QPointF(11.5, 5.5), QPointF(14.0, 8.0))
            painter.drawLine(QPointF(11.5, 10.5), QPointF(14.0, 8.0))

        elif name == "merge":
            # 외부 문서를 현재 문서 안으로 병합/삽입하는 아이콘
            path = QPainterPath()
            path.moveTo(6.0, 2.5)
            path.lineTo(12.5, 2.5)
            path.lineTo(12.5, 13.5)
            path.lineTo(6.0, 13.5)
            path.lineTo(6.0, 11.0)
            painter.drawPath(path)
            painter.drawLine(QPointF(2.0, 8.0), QPointF(9.5, 8.0))
            painter.drawLine(QPointF(7.0, 5.5), QPointF(9.5, 8.0))
            painter.drawLine(QPointF(7.0, 10.5), QPointF(9.5, 8.0))

        elif name == "plus":
            painter.drawLine(QPointF(8.0, 3.2), QPointF(8.0, 12.8))
            painter.drawLine(QPointF(3.2, 8.0), QPointF(12.8, 8.0))

        elif name == "info":
            painter.drawEllipse(QRectF(2.5, 2.5, 11.0, 11.0))
            painter.drawLine(QPointF(8.0, 7.3), QPointF(8.0, 11.2))
            painter.drawPoint(QPointF(8.0, 5.0))

        painter.end()
        pixmap.setDevicePixelRatio(scale)
        return pixmap
