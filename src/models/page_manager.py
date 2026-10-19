from src.models.pdf_document import PDFDocument


class PageManager:
    """페이지 삭제, 순서 이동, 90도 회전 기능을 수행하는 모델 클래스"""

    def __init__(self, pdf_doc: PDFDocument):
        self.pdf_doc = pdf_doc

    def delete_page(self, page_index: int) -> bool:
        """지정한 인덱스의 페이지를 삭제합니다 (최소 1페이지는 유지)."""
        doc = self.pdf_doc.doc
        if not doc or len(doc) <= 1:
            return False
        if not (0 <= page_index < len(doc)):
            return False

        doc.delete_page(page_index)
        self.pdf_doc.is_modified = True
        return True

    def move_page(self, from_index: int, to_index: int) -> bool:
        """페이지를 from_index에서 to_index 위치로 이동합니다."""
        doc = self.pdf_doc.doc
        if not doc:
            return False
        count = len(doc)
        if not (0 <= from_index < count and 0 <= to_index < count):
            return False
        if from_index == to_index:
            return False

        # PyMuPDF move_page(pno, to): pno를 to 인덱스 앞으로 이동
        if from_index < to_index:
            # 뒤로 이동할 때는 대상 인덱스 다음 위치로 지정해야 원하는 인덱스에 안착
            if to_index + 1 < count:
                doc.move_page(from_index, to_index + 1)
            else:
                doc.move_page(from_index, -1)
        else:
            doc.move_page(from_index, to_index)

        self.pdf_doc.is_modified = True
        return True

    def rotate_page(self, page_index: int, angle: int = 90) -> bool:
        """지정한 페이지를 시계 방향으로 90도(또는 지정 각도) 회전합니다."""
        page = self.pdf_doc.get_page(page_index)
        if not page:
            return False

        current_rot = page.rotation
        new_rot = (current_rot + angle) % 360
        page.set_rotation(new_rot)
        self.pdf_doc.is_modified = True
        return True
