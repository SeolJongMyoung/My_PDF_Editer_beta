import fitz
from PyQt6.QtCore import QRectF, QPointF


class CoordConverter:
    """
    화면 확대/축소(Zoom) 배율이 적용된 PyQt 위젯(QLabel) 마우스 좌표와
    PyMuPDF(fitz) 실제 페이지 원본 좌표계를 정확히 매핑하는 유틸리티
    """

    @staticmethod
    def screen_rect_to_pdf_rect(
        qt_rect: QRectF,
        zoom: float,
        page_origin: fitz.Point = fitz.Point(0, 0),
    ) -> fitz.Rect:
        """
        화면(QLabel 내부) 드래그 사각형(QRectF)을 PDF 원본 좌표(fitz.Rect)로 변환합니다.

        [좌표 변환 공식]
        x_pdf = (x_screen / zoom) + page.rect.x0
        y_pdf = (y_screen / zoom) + page.rect.y0
        """
        if zoom <= 0:
            zoom = 1.0

        norm_rect = qt_rect.normalized()
        ox = float(page_origin.x)
        oy = float(page_origin.y)

        x0 = (norm_rect.left() / zoom) + ox
        y0 = (norm_rect.top() / zoom) + oy
        x1 = (norm_rect.right() / zoom) + ox
        y1 = (norm_rect.bottom() / zoom) + oy

        return fitz.Rect(x0, y0, x1, y1).normalize()

    @staticmethod
    def screen_point_to_pdf_point(
        qt_point: QPointF,
        zoom: float,
        page_origin: fitz.Point = fitz.Point(0, 0),
    ) -> fitz.Point:
        """
        화면(QLabel 내부) 클릭 좌표(QPointF)를 PDF 원본 좌표(fitz.Point)로 변환합니다.
        """
        if zoom <= 0:
            zoom = 1.0

        x = (qt_point.x() / zoom) + float(page_origin.x)
        y = (qt_point.y() / zoom) + float(page_origin.y)
        return fitz.Point(x, y)
