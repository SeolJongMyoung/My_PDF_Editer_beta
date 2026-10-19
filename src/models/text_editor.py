import os
from typing import List, Tuple
import fitz
from src.models.pdf_document import PDFDocument


class TextEditor:
    """특정 텍스트 검색 후 삭제(Redact) 및 새 텍스트 삽입(Replace)을 담당하는 클래스"""

    def __init__(self, pdf_doc: PDFDocument):
        self.pdf_doc = pdf_doc
        self.korean_font_path = self._find_korean_font()

    def _find_korean_font(self) -> str:
        """시스템 또는 assets 폴더에서 한글 지원 폰트 파일 경로를 탐색합니다."""
        candidates = [
            os.path.join("assets", "fonts", "NanumGothic.ttf"),
            os.path.join("assets", "fonts", "malgun.ttf"),
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/gulim.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return ""

    def search_text(self, page_index: int, query: str) -> List[fitz.Rect]:
        """지정한 페이지에서 검색어(query)가 위치한 영역 리스트를 반환합니다."""
        page = self.pdf_doc.get_page(page_index)
        if not page or not query.strip():
            return []
        return page.search_for(query)

    def redact_and_replace(
        self,
        page_index: int,
        target_text: str,
        replacement_text: str,
        font_size: float = 10.0,
        text_color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> int:
        """
        지정한 페이지에서 target_text를 찾아 Redaction(영구 삭제) 처리하고,
        동일한 위치에 replacement_text를 새로 삽입합니다.
        반환값: 수정된 텍스트 영역의 개수
        """
        page = self.pdf_doc.get_page(page_index)
        if not page or not target_text:
            return 0

        rects = page.search_for(target_text)
        if not rects:
            return 0

        # 1. 기존 텍스트 영역에 Redaction 주석 추가
        for rect in rects:
            page.add_redact_annot(rect, fill=(1, 1, 1))

        # 2. Redaction 적용하여 원본 텍스트 실제 제거
        page.apply_redactions()

        # 3. 새 텍스트가 있으면 해당 좌표에 텍스트 삽입 (한글 폰트 지원)
        if replacement_text:
            fontname = "helv"
            fontfile = None
            if self.korean_font_path:
                fontname = "kor_font"
                fontfile = self.korean_font_path

            for rect in rects:
                # 높이에 맞춰 폰트 크기를 자동 조정하거나 입력된 크기 사용
                adjusted_size = min(font_size, max(rect.height * 0.8, 6.0))
                # baseline 위치(좌측 하단에서 살짝 위) 계산
                insert_point = fitz.Point(rect.x0, rect.y1 - (rect.height * 0.15))
                page.insert_text(
                    insert_point,
                    replacement_text,
                    fontsize=adjusted_size,
                    fontname=fontname,
                    fontfile=fontfile,
                    color=text_color,
                )

        self.pdf_doc.is_modified = True
        return len(rects)

    def redact_rect(self, page_index: int, rect: fitz.Rect, replacement_text: str = "") -> bool:
        """드래그한 특정 사각형 영역을 Redact 처리하고 선택적으로 새 텍스트를 삽입합니다."""
        page = self.pdf_doc.get_page(page_index)
        if not page:
            return False

        page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()

        if replacement_text:
            fontname = "kor_font" if self.korean_font_path else "helv"
            fontfile = self.korean_font_path if self.korean_font_path else None
            font_size = min(11.0, max(rect.height * 0.7, 6.0))
            insert_point = fitz.Point(rect.x0 + 2, rect.y0 + font_size + 2)
            page.insert_text(
                insert_point,
                replacement_text,
                fontsize=font_size,
                fontname=fontname,
                fontfile=fontfile,
                color=(0, 0, 0),
            )

        self.pdf_doc.is_modified = True
        return True
