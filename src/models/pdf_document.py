from typing import Optional
import fitz
from PyQt6.QtGui import QImage, QPixmap


class PDFDocument:
    """PDF 파일 열기, 저장, 렌더링 및 기본 문서 상태를 관리하는 모델 클래스"""

    def __init__(self):
        self.doc: Optional[fitz.Document] = None
        self.file_path: Optional[str] = None
        self.is_modified: bool = False

    def open(self, file_path: str) -> bool:
        """PDF 파일을 엽니다."""
        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(file_path)
            self.file_path = file_path
            self.is_modified = False
            return True
        except Exception as e:
            print(f"PDF 열기 실패: {e}")
            return False

    def save_as(self, save_path: str) -> bool:
        """현재 PDF 문서를 다른 이름으로 저장합니다."""
        if not self.doc:
            return False
        try:
            # garbage=4, deflate=True로 용량 최적화 및 삭제된 객체 정리
            self.doc.save(save_path, garbage=4, deflate=True)
            self.file_path = save_path
            self.is_modified = False
            return True
        except Exception as e:
            print(f"PDF 저장 실패: {e}")
            return False

    def close(self):
        """열려 있는 문서를 닫습니다."""
        if self.doc:
            self.doc.close()
            self.doc = None
            self.file_path = None
            self.is_modified = False

    @property
    def page_count(self) -> int:
        return len(self.doc) if self.doc else 0

    def get_page(self, page_index: int) -> Optional[fitz.Page]:
        if not self.doc or not (0 <= page_index < len(self.doc)):
            return None
        return self.doc[page_index]

    def render_page(self, page_index: int, zoom: float = 1.0) -> Optional[QPixmap]:
        """지정한 페이지를 주어진 배율(zoom)로 렌더링하여 QPixmap으로 반환합니다."""
        page = self.get_page(page_index)
        if not page:
            return None

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_format = QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        # QImage가 버퍼 메모리에 의존하지 않도록 복사본 생성 후 QPixmap 변환
        return QPixmap.fromImage(qimg.copy())

    def render_thumbnail(self, page_index: int, max_width: int = 120) -> Optional[QPixmap]:
        """사이드바 표시용 저해상도 썸네일 QPixmap을 반환합니다."""
        page = self.get_page(page_index)
        if not page:
            return None
        rect = page.rect
        zoom = max_width / rect.width if rect.width > 0 else 0.2
        return self.render_page(page_index, zoom=zoom)
