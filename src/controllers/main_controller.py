import os
from typing import List, Optional
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QInputDialog,
)

from src.__version__ import get_window_title
from src.models.pdf_handler import PdfHandler
from src.views.main_window import MainWindow, CursorMode
from src.views.dialogs.text_replace_dialog import TextEditDialog
from src.views.dialogs.merge_pages_dialog import MergePagesDialog
from src.utils.coord_converter import CoordConverter


class MainController:
    """
    PdfHandler(Model)와 MainWindow(View)를 결합하여
    파일 열기/저장, 종료 시 미저장 확인, 10단계 Undo/Redo,
    Ctrl/Shift 다중 페이지 선택, 드래그앤드롭 구분선 페이지 이동(확인 창 포함),
    다른 PDF 파일 합병(삽입), 페이지 추출 저장, 썸네일/책갈피 동기화,
    마우스 드래그 기반 주석/텍스트 치환을 제어하는 컨트롤러
    """

    def __init__(self, window: MainWindow):
        self.view = window
        self.pdf = PdfHandler()

        self.current_page: int = 0
        self.zoom: float = 1.2  # 초기 렌더링 배율 (120%)
        self._syncing_thumbnails: bool = False

        # 창 닫기(closeEvent) 시 미저장 변경사항 확인 콜백 연결
        self.view.set_close_confirm_callback(self.confirm_unsaved_changes)

        self._connect_signals()
        self._update_action_states()

    def _connect_signals(self):
        # 1. 상단 툴바: 파일 열기 / 저장 / Undo / Redo / 이전·다음 페이지 / 확대·축소
        self.view.act_open.triggered.connect(self.open_file)
        self.view.act_save.triggered.connect(self.save_file)
        self.view.act_undo.triggered.connect(self.undo_action)
        self.view.act_redo.triggered.connect(self.redo_action)
        self.view.act_prev_page.triggered.connect(self.prev_page)
        self.view.act_next_page.triggered.connect(self.next_page)
        self.view.act_zoom_in.triggered.connect(lambda: self.change_zoom(0.2))
        self.view.act_zoom_out.triggered.connect(lambda: self.change_zoom(-0.2))
        self.view.scroll_area.wheel_zoom_requested.connect(self.change_zoom)

        # 2. 좌측 사이드바: 썸네일 클릭/다중선택, 드래그앤드롭 이동, 다른 PDF 합병, 회전, 삭제, 추출 저장
        self.view.thumbnail_list.currentRowChanged.connect(self.on_thumbnail_clicked)
        self.view.thumbnail_list.itemSelectionChanged.connect(self._update_action_states)
        self.view.pages_drop_requested.connect(self.on_pages_drop_requested)
        self.view.merge_pages_requested.connect(self.open_merge_dialog)
        self.view.external_pdf_dropped.connect(self.on_external_pdf_dropped)
        self.view.btn_rotate.clicked.connect(self.rotate_selected_pages)
        self.view.btn_delete.clicked.connect(self.delete_selected_pages)
        self.view.btn_extract.clicked.connect(self.extract_selected_pages)
        self.view.page_move_requested.connect(self.move_page)

        # 3. 우측 책갈피(Bookmark) 패널: 책갈피 클릭 이동, 추가, 삭제
        self.view.bookmark_selected.connect(self.go_to_page)
        self.view.bookmark_add_requested.connect(self.add_bookmark_for_current_page)
        self.view.bookmark_delete_requested.connect(self.delete_bookmark)

        # 4. 중앙 캔버스: 마우스 드래그/클릭 인터랙션
        self.view.page_canvas_label.canvas_interacted.connect(self.on_canvas_interacted)

    # -------------------------------------------------------------------------
    # 미저장 변경 사항 확인 대화상자 (프로그램 종료 / 새 파일 열기 시 호출)
    # -------------------------------------------------------------------------
    def confirm_unsaved_changes(self) -> bool:
        if not self.pdf.is_modified:
            return True

        file_name = (
            os.path.basename(self.pdf.file_path)
            if self.pdf.file_path
            else "현재 문서"
        )
        msg_box = QMessageBox(self.view)
        msg_box.setWindowTitle("변경 내용 저장 확인")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"'{file_name}' 파일에 수정된 내용이 있습니다.")
        msg_box.setInformativeText("변경된 내용을 저장하시겠습니까?")

        btn_save = msg_box.addButton("저장", QMessageBox.ButtonRole.AcceptRole)
        btn_discard = msg_box.addButton("저장 안 함", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancel = msg_box.addButton("취소", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(btn_save)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_save:
            return self.save_file()
        elif clicked == btn_discard:
            return True
        elif clicked == btn_cancel:
            return False
        return False

    # -------------------------------------------------------------------------
    # 실행 취소 (Undo) / 다시 실행 (Redo) - 최대 10단계
    # -------------------------------------------------------------------------
    def undo_action(self):
        if not self.pdf.can_undo:
            return
        if self.pdf.undo():
            if self.current_page >= self.pdf.page_count:
                self.current_page = max(0, self.pdf.page_count - 1)
            self.refresh_thumbnails()
            self.refresh_bookmarks()
            self.render_current_page()

    def redo_action(self):
        if not self.pdf.can_redo:
            return
        if self.pdf.redo():
            if self.current_page >= self.pdf.page_count:
                self.current_page = max(0, self.pdf.page_count - 1)
            self.refresh_thumbnails()
            self.refresh_bookmarks()
            self.render_current_page()

    # -------------------------------------------------------------------------
    # 1. 파일 열기 및 썸네일/책갈피/뷰어 렌더링
    # -------------------------------------------------------------------------
    def open_file(self):
        if not self.confirm_unsaved_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "PDF 파일 열기", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        total_pages = self.pdf.load_document(file_path)
        if total_pages <= 0:
            QMessageBox.critical(
                self.view, "열기 실패", "PDF 파일을 열 수 없거나 암호로 보호되어 있습니다."
            )
            return

        self.current_page = 0
        self.refresh_thumbnails()
        self.refresh_bookmarks()
        self.render_current_page()
        self._update_action_states()

    def render_current_page(self, sync_selection: bool = False):
        if self.pdf.page_count == 0:
            self.view.display_page_pixmap(None)
            self.view.update_page_status(0, 0, self.zoom)
            return

        pixmap = self.pdf.get_page_pixmap(
            self.current_page, zoom=self.zoom, as_qpixmap=True
        )
        self.view.display_page_pixmap(pixmap)

        if sync_selection:
            self._syncing_thumbnails = True
            self.view.thumbnail_list.setCurrentRow(self.current_page)
            self.view._on_thumbnail_selection_changed()
            self._syncing_thumbnails = False

        self.view.update_page_status(
            self.current_page + 1, self.pdf.page_count, self.zoom
        )
        self._update_window_title()
        self._update_action_states()

    def refresh_thumbnails(self, selected_indices: Optional[List[int]] = None):
        self._syncing_thumbnails = True
        pixmaps = [
            self.pdf.get_page_pixmap(idx, zoom=0.25, as_qpixmap=True)
            for idx in range(self.pdf.page_count)
        ]
        self.view.populate_thumbnails(
            pixmaps,
            selected_indices=selected_indices,
            current_index=self.current_page,
        )
        self._syncing_thumbnails = False

    def refresh_single_thumbnail(self, page_num: int):
        thumb_pix = self.pdf.get_page_pixmap(page_num, zoom=0.25, as_qpixmap=True)
        if isinstance(thumb_pix, QPixmap):
            self.view.update_single_thumbnail(page_num, thumb_pix)

    # -------------------------------------------------------------------------
    # 우측 책갈피(Bookmark) 관리
    # -------------------------------------------------------------------------
    def refresh_bookmarks(self):
        bookmarks = self.pdf.get_bookmarks()
        self.view.populate_bookmarks(bookmarks)

    def add_bookmark_for_current_page(self):
        if self.pdf.page_count == 0:
            return

        default_title = f"{self.current_page + 1}페이지 책갈피"
        title, ok = QInputDialog.getText(
            self.view,
            "책갈피 추가",
            f"현재 페이지({self.current_page + 1}p)에 추가할 책갈피 이름을 입력하세요:",
            text=default_title,
        )
        if ok and title.strip():
            if self.pdf.add_bookmark(title.strip(), self.current_page):
                self.refresh_bookmarks()
                self._update_window_title()
                self._update_action_states()

    def delete_bookmark(self, bookmark_index: int):
        if self.pdf.page_count == 0:
            return
        if self.pdf.remove_bookmark(bookmark_index):
            self.refresh_bookmarks()
            self._update_window_title()
            self._update_action_states()

    # -------------------------------------------------------------------------
    # 2. 캔버스 마우스 인터랙션
    # -------------------------------------------------------------------------
    def on_canvas_interacted(self, screen_rect: QRectF, mode: CursorMode):
        if self.pdf.page_count == 0:
            return

        page_origin = self.pdf.get_page_origin(self.current_page)
        pdf_rect = CoordConverter.screen_rect_to_pdf_rect(
            screen_rect, self.zoom, page_origin
        )

        if mode == CursorMode.BOX_REVIEW:
            if self.pdf.add_box_annotation(self.current_page, pdf_rect, color=(1, 0, 0)):
                self.refresh_single_thumbnail(self.current_page)
                self.render_current_page()

        elif mode == CursorMode.HIGHLIGHT:
            if self.pdf.add_highlight(self.current_page, pdf_rect):
                self.refresh_single_thumbnail(self.current_page)
                self.render_current_page()

        elif mode == CursorMode.TEXT_EDIT:
            style_info = self.pdf.inspect_text_at_rect(self.current_page, pdf_rect)
            font_choices = self.pdf.get_available_font_choices()

            dialog = TextEditDialog(style_info, font_choices, parent=self.view)
            if dialog.exec():
                (
                    new_text,
                    font_key,
                    font_size,
                    is_bold,
                    is_italic,
                    text_color,
                    y_offset,
                ) = dialog.get_edit_values()

                if self.pdf.replace_rect_area_styled(
                    page_num=self.current_page,
                    style_info=style_info,
                    new_text=new_text,
                    font_key=font_key,
                    font_size=font_size,
                    is_bold=is_bold,
                    is_italic=is_italic,
                    text_color=text_color,
                    y_offset=y_offset,
                ):
                    self.refresh_single_thumbnail(self.current_page)
                    self.render_current_page()

    # -------------------------------------------------------------------------
    # 3. 썸네일 드래그 앤 드롭 페이지 이동 (구분선 위치 확인 후 완료)
    # -------------------------------------------------------------------------
    def on_pages_drop_requested(self, selected_indices: List[int], insert_before_slot: int):
        """
        마우스로 페이지를 드래그하다가 뗐을 때 호출됩니다.
        실제 페이지 순서가 바뀌는 위치인 경우 이동 여부를 묻는 대화창을 띄우고 완료합니다.
        """
        if self.pdf.page_count <= 1 or not selected_indices:
            return

        # 제자리에 그대로 놓은 경우에는 아무 작업도 하지 않음
        if not self.pdf.would_move_change_order(selected_indices, insert_before_slot):
            return

        src_label = self._format_page_numbers(selected_indices)
        total = self.pdf.page_count
        if insert_before_slot <= 0:
            dest_desc = "맨 앞(1페이지 위)"
        elif insert_before_slot >= total:
            dest_desc = f"맨 끝({total}페이지 뒤)"
        else:
            dest_desc = f"{insert_before_slot}페이지와 {insert_before_slot + 1}페이지 사이"

        reply = QMessageBox.question(
            self.view,
            "페이지 위치 이동 확인",
            f"선택한 페이지({src_label})를 [{dest_desc}] 위치로 이동하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            new_positions = self.pdf.move_pages_to_slot(
                selected_indices, insert_before_slot
            )
            if new_positions:
                self.current_page = new_positions[0]
                self.refresh_thumbnails(selected_indices=new_positions)
                self.refresh_bookmarks()
                self.render_current_page(sync_selection=False)

    # -------------------------------------------------------------------------
    # 4. 썸네일/책갈피 클릭 및 다중 페이지 조작 (추출 저장 / 회전 / 삭제)
    # -------------------------------------------------------------------------
    def go_to_page(self, page_index: int, sync_selection: bool = True):
        if 0 <= page_index < self.pdf.page_count and page_index != self.current_page:
            self.current_page = page_index
            self.render_current_page(sync_selection=sync_selection)

    def on_thumbnail_clicked(self, row: int):
        if self._syncing_thumbnails:
            return
        if 0 <= row < self.pdf.page_count and row != self.current_page:
            self.current_page = row
            self.render_current_page(sync_selection=False)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_current_page(sync_selection=True)

    def next_page(self):
        if self.current_page < self.pdf.page_count - 1:
            self.current_page += 1
            self.render_current_page(sync_selection=True)

    def change_zoom(self, delta: float):
        if self.pdf.page_count == 0:
            return
        new_zoom = round(max(0.4, min(4.0, self.zoom + delta)), 2)
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self.render_current_page(sync_selection=False)

    def rotate_selected_pages(self):
        if self.pdf.page_count == 0:
            return
        selected = self.view.get_selected_page_indices()
        if self.pdf.rotate_pages(selected, angle=90):
            for p in selected:
                self.refresh_single_thumbnail(p)
            self.render_current_page(sync_selection=False)

    def delete_selected_pages(self):
        if self.pdf.page_count == 0:
            return
        selected = self.view.get_selected_page_indices()
        if not selected:
            return

        if self.pdf.page_count - len(selected) < 1:
            QMessageBox.warning(
                self.view,
                "삭제 불가",
                "문서의 모든 페이지를 삭제할 수는 없습니다. 최소 1개의 페이지는 남겨야 합니다.",
            )
            return

        page_label = self._format_page_numbers(selected)
        reply = QMessageBox.question(
            self.view,
            "페이지 삭제",
            f"선택한 {len(selected)}개 페이지({page_label})를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.pdf.delete_pages(selected):
                if self.current_page >= self.pdf.page_count:
                    self.current_page = self.pdf.page_count - 1
                self.refresh_thumbnails()
                self.refresh_bookmarks()
                self.render_current_page(sync_selection=True)

    def extract_selected_pages(self):
        if self.pdf.page_count == 0:
            return

        selected = self.view.get_selected_page_indices()
        if not selected:
            QMessageBox.information(self.view, "페이지 선택", "추출할 페이지를 먼저 선택해주세요.")
            return

        page_tag = self._format_page_numbers(selected)
        default_name = f"extracted_{page_tag}.pdf"
        if self.pdf.file_path:
            base, ext = os.path.splitext(self.pdf.file_path)
            default_name = f"{base}_추출_{page_tag}{ext}"

        save_path, _ = QFileDialog.getSaveFileName(
            self.view,
            f"선택 페이지 추출 저장 ({len(selected)}페이지: {page_tag})",
            default_name,
            "PDF Files (*.pdf)",
        )
        if not save_path:
            return

        if self.pdf.extract_pages(selected, save_path):
            QMessageBox.information(
                self.view,
                "페이지 추출 완료",
                f"선택한 {len(selected)}개 페이지({page_tag})가 새 PDF 파일로 저장되었습니다:\n{save_path}",
            )
        else:
            QMessageBox.critical(
                self.view, "추출 실패", "선택한 페이지를 추출하여 저장하는 중 오류가 발생했습니다."
            )

    @staticmethod
    def _format_page_numbers(indices: List[int]) -> str:
        if not indices:
            return ""
        pages = [i + 1 for i in sorted(set(indices))]
        if len(pages) == 1:
            return f"{pages[0]}p"
        if pages[-1] - pages[0] == len(pages) - 1:
            return f"{pages[0]}-{pages[-1]}p"
        if len(pages) <= 5:
            return ",".join(str(p) for p in pages) + "p"
        return f"{pages[0]}..{pages[-1]}p({len(pages)}개)"

    def move_page(self, from_index: int, to_index: int):
        if self.pdf.manage_page("move", from_index, to_page=to_index):
            self.current_page = to_index
            self.refresh_thumbnails()
            self.refresh_bookmarks()
            self.render_current_page(sync_selection=True)

    # -------------------------------------------------------------------------
    # 5. 다른 PDF 파일 합병 (버튼 / 우클릭 메뉴 / 탐색기 드래그 앤 드롭)
    # -------------------------------------------------------------------------
    def open_merge_dialog(self, preset_slot: int = -1):
        """[다른 PDF 합병] 버튼 또는 우클릭 컨텍스트 메뉴에서 호출됩니다."""
        initial_dir = (
            os.path.dirname(self.pdf.file_path) if self.pdf.file_path else ""
        )
        source_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "합병할 PDF 파일 선택",
            initial_dir,
            "PDF Files (*.pdf)",
        )
        if not source_path:
            return

        slot = preset_slot if preset_slot >= 0 else None
        self._run_merge_dialog(source_path, preset_slot=slot)

    def on_external_pdf_dropped(self, source_pdf_path: str, insert_before_slot: int):
        """윈도우 탐색기에서 외부 .pdf 파일을 왼쪽 페이지 목록의 구분선 위치에 드롭했을 때 호출됩니다."""
        if not source_pdf_path or not os.path.exists(source_pdf_path):
            return
        self._run_merge_dialog(source_pdf_path, preset_slot=insert_before_slot)

    def _run_merge_dialog(
        self, source_pdf_path: str, preset_slot: Optional[int] = None
    ):
        dialog = MergePagesDialog(
            source_pdf_path=source_pdf_path,
            doc_page_count=self.pdf.page_count,
            current_page_index=self.current_page,
            preset_slot=preset_slot,
            parent=self.view,
        )
        if dialog.source_total_pages <= 0:
            QMessageBox.critical(
                self.view,
                "파일 열기 실패",
                "선택한 PDF 파일을 열 수 없거나 암호로 보호되어 있습니다.",
            )
            return

        if dialog.exec():
            src_path, src_pages, target_slot = dialog.get_merge_Result()
            inserted_indices = self.pdf.merge_pages_from_file(
                source_pdf_path=src_path,
                source_page_indices=src_pages,
                insert_before_index=target_slot,
            )
            if inserted_indices:
                self.current_page = inserted_indices[0]
                self.refresh_thumbnails(selected_indices=inserted_indices)
                self.refresh_bookmarks()
                self.render_current_page(sync_selection=False)
            else:
                QMessageBox.critical(
                    self.view,
                    "페이지 합병 실패",
                    "선택한 PDF 페이지를 합병하는 중 오류가 발생했습니다.",
                )

    # -------------------------------------------------------------------------
    # 5. 파일 저장 (QFileDialog)
    # -------------------------------------------------------------------------
    def save_file(self) -> bool:
        if self.pdf.page_count == 0:
            return False

        default_path = "edited_output.pdf"
        if self.pdf.file_path:
            base, ext = os.path.splitext(self.pdf.file_path)
            default_path = f"{base}_edited{ext}"

        save_path, _ = QFileDialog.getSaveFileName(
            self.view, "PDF 파일 저장", default_path, "PDF Files (*.pdf)"
        )
        if not save_path:
            return False

        if self.pdf.save_document(save_path):
            self._update_window_title()
            self._update_action_states()
            QMessageBox.information(
                self.view, "저장 완료", f"PDF 문서가 성공적으로 저장되었습니다:\n{save_path}"
            )
            return True
        else:
            QMessageBox.critical(
                self.view, "저장 실패", "PDF 파일을 저장하는 중 오류가 발생했습니다."
            )
            return False

    # -------------------------------------------------------------------------
    # UI 활성화 상태 동기화
    # -------------------------------------------------------------------------
    def _update_window_title(self):
        if self.pdf.file_path:
            name = os.path.basename(self.pdf.file_path)
            self.view.setWindowTitle(
                get_window_title(name, self.pdf.is_modified)
            )
        else:
            self.view.setWindowTitle(get_window_title())

    def _update_action_states(self):
        has_doc = self.pdf.page_count > 0
        selected_count = len(self.view.get_selected_page_indices()) if has_doc else 0

        self.view.act_save.setEnabled(has_doc)
        self.view.act_undo.setEnabled(self.pdf.can_undo)
        self.view.act_redo.setEnabled(self.pdf.can_redo)
        self.view.act_undo.setToolTip(
            f"실행 취소 가능: {self.pdf.undo_count}단계 (Ctrl+Z)"
            if self.pdf.can_undo
            else "실행 취소할 작업이 없습니다 (Ctrl+Z)"
        )
        self.view.act_redo.setToolTip(
            f"다시 실행 가능: {self.pdf.redo_count}단계 (Ctrl+Y)"
            if self.pdf.can_redo
            else "다시 실행할 작업이 없습니다 (Ctrl+Y)"
        )
        self.view.act_prev_page.setEnabled(has_doc and self.current_page > 0)
        self.view.act_next_page.setEnabled(
            has_doc and self.current_page < self.pdf.page_count - 1
        )
        self.view.act_zoom_in.setEnabled(has_doc)
        self.view.act_zoom_out.setEnabled(has_doc)
        self.view.btn_rotate.setEnabled(has_doc)
        self.view.btn_delete.setEnabled(
            has_doc and (self.pdf.page_count - selected_count >= 1)
        )
        self.view.btn_extract.setEnabled(has_doc and selected_count >= 1)
        self.view.btn_add_bookmark.setEnabled(has_doc)
        self.view.btn_del_bookmark.setEnabled(has_doc)
