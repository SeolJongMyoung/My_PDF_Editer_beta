import fitz
from src.models.pdf_document import PDFDocument


class AnnotationTool:
    """마우스 드래그 영역에 사각형 마크업(Red Box) 및 텍스트 하이라이트 주석을 추가하는 클래스"""

    def __init__(self, pdf_doc: PDFDocument):
        self.pdf_doc = pdf_doc

    def add_red_box(self, page_index: int, rect: fitz.Rect, border_width: float = 2.0) -> bool:
        """
        지정한 페이지의 rect 영역에 빨간색 사각형 마크업(Square Annotation)을 추가합니다.
        """
        page = self.pdf_doc.get_page(page_index)
        if not page or rect.is_empty or rect.is_infinite:
            return False

        annot = page.add_rect_annot(rect)
        annot.set_colors(stroke=(1.0, 0.0, 0.0))  # 빨간색 테두리
        annot.set_border(width=border_width)
        annot.update()

        self.pdf_doc.is_modified = True
        return True

    def add_highlight(self, page_index: int, rect: fitz.Rect) -> bool:
        """
        지정한 페이지의 드래그 영역(rect) 내에 포함된 텍스트를 찾아 하이라이트를 추가하고,
        텍스트가 없는 영역일 경우 영역 자체에 노란색 반투명 하이라이트 주석을 추가합니다.
        """
        page = self.pdf_doc.get_page(page_index)
        if not page or rect.is_empty or rect.is_infinite:
            return False

        # 드래그한 영역 안의 단어들을 추출하여 텍스트 기반 하이라이트 적용 시도
        words = page.get_text("words", clip=rect)
        if words:
            quads = [fitz.Rect(w[:4]).quad for w in words]
            annot = page.add_highlight_annot(quads)
            annot.set_colors(stroke=(1.0, 0.95, 0.0))
            annot.update()
        else:
            # 이미지 스캔본이거나 텍스트가 안 잡히면 드래그한 사각형 영역 자체에 하이라이트 추가
            annot = page.add_highlight_annot(rect)
            annot.set_colors(stroke=(1.0, 0.95, 0.0))
            annot.update()

        self.pdf_doc.is_modified = True
        return True
