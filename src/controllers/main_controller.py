import os
from typing import Dict, List, Optional, Tuple
import fitz
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
from src.views.dialogs.print_dialog import PrintDialog
from src.views.dialogs.page_number_dialog import PageNumberDialog
from src.views.dialogs.stamp_mark_dialog import StampMarkDialog
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
        self._search_keyword: str = ""
        self._search_matches: List[Tuple[int, fitz.Rect]] = []
        self._search_current_idx: int = -1

        # 창 닫기(closeEvent) 시 미저장 변경사항 확인 콜백 연결
        self.view.set_close_confirm_callback(self.confirm_unsaved_changes)
        self.view.populate_stamp_font_choices(self.pdf.get_available_font_choices())

        self._connect_signals()
        self._update_action_states()

    def _connect_signals(self):
        # 1. 상단 메뉴 & 툴바: 파일 열기 / 저장 / 새이름으로 / 문서닫기 / 인쇄 / Undo / Redo / 찾기 / 이전·다음 페이지 / 확대·축소 / 쪽번호넣기
        self.view.act_open.triggered.connect(self.open_file)
        self.view.act_save.triggered.connect(self.save_file)
        self.view.act_save_as.triggered.connect(self.save_file_as)
        self.view.act_close_doc.triggered.connect(self.close_document)
        self.view.act_print.triggered.connect(self.on_print_requested)
        self.view.act_print_setup.triggered.connect(self.on_print_setup_requested)
        self.view.act_undo.triggered.connect(self.undo_action)
        self.view.act_redo.triggered.connect(self.redo_action)
        self.view.act_find.triggered.connect(self.find_text_in_document)
        self.view.act_prev_page.triggered.connect(self.prev_page)
        self.view.act_next_page.triggered.connect(self.next_page)
        self.view.act_zoom_in.triggered.connect(lambda: self.change_zoom(0.2))
        self.view.act_zoom_out.triggered.connect(lambda: self.change_zoom(-0.2))
        self.view.scroll_area.wheel_zoom_requested.connect(self.change_zoom)
        self.view.act_insert_page_numbers.triggered.connect(
            self.on_insert_page_numbers_requested
        )

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

        # 4. 중앙 캔버스: 마우스 드래그/클릭 인터랙션 및 가상화 연속 스크롤/키보드 이동
        self.view.page_canvas_interacted.connect(self.on_page_canvas_interacted)
        self.view.cloud_polygon_completed.connect(self.on_cloud_polygon_completed)
        self.view.stamp_mark_clicked.connect(self.on_stamp_mark_clicked)
        self.view.stamp_batch_dialog_requested.connect(
            self.on_stamp_batch_dialog_requested
        )
        self.view.continuous_mode_toggled.connect(self.on_continuous_mode_toggled)
        self.view.page_render_requested.connect(self.on_page_render_requested)
        self.view.current_page_scrolled.connect(self.on_canvas_page_scrolled)
        self.view.scroll_area.boundary_page_step_requested.connect(
            self.on_boundary_page_step
        )
        self.view.scroll_area.key_page_navigation_requested.connect(
            self.on_key_page_navigation
        )

        # 5. 상단 슬림 찾기 바 (Find Bar) 시그널 연결
        self.view.find_query_changed.connect(self.on_find_query_changed)
        self.view.find_next_requested.connect(self.on_find_next_requested)
        self.view.find_prev_requested.connect(self.on_find_prev_requested)
        self.view.find_closed.connect(self.on_find_closed)

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
            self.render_current_page(rebuild_layout=True)

    def redo_action(self):
        if not self.pdf.can_redo:
            return
        if self.pdf.redo():
            if self.current_page >= self.pdf.page_count:
                self.current_page = max(0, self.pdf.page_count - 1)
            self.refresh_thumbnails()
            self.refresh_bookmarks()
            self.render_current_page(rebuild_layout=True)

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
        self.view.hide_find_bar()
        self.refresh_thumbnails()
        self.refresh_bookmarks()
        self.render_current_page(rebuild_layout=True, scroll_to_current=True)
        self._update_action_states()

    def render_current_page(
        self,
        sync_selection: bool = False,
        rebuild_layout: bool = False,
        scroll_to_current: bool = True,
    ):
        if self.pdf.page_count == 0:
            self.view.display_page_pixmap(None)
            self.view.update_page_status(0, 0, self.zoom)
            return

        if self.view.continuous_scroll:
            if (
                rebuild_layout
                or len(self.view._page_sizes) != self.pdf.page_count
            ):
                page_sizes = self.pdf.get_all_page_display_sizes(zoom=self.zoom)
                self.view.setup_continuous_pages(
                    page_sizes,
                    current_page=self.current_page,
                    scroll_to_current=scroll_to_current,
                )
            else:
                if scroll_to_current:
                    self.view.scroll_to_page(self.current_page)
                else:
                    self.view.invalidate_continuous_page(self.current_page)
        else:
            pixmap = self.pdf.get_page_pixmap(
                self.current_page, zoom=self.zoom, as_qpixmap=True
            )
            self.view.display_page_pixmap(pixmap, page_index=self.current_page)
            if scroll_to_current:
                self.view.scroll_area.verticalScrollBar().setValue(0)

        if self.view.find_bar_frame.isVisible() and self._search_matches:
            self._sync_search_highlights_to_view()

        if sync_selection:
            self._sync_left_thumbnail_selection(self.current_page, force_single=True)

        self.view.update_page_status(
            self.current_page + 1, self.pdf.page_count, self.zoom
        )
        self._update_window_title()
        self._update_action_states()

    def _sync_left_thumbnail_selection(
        self, page_index: int, force_single: bool = False
    ):
        if not (0 <= page_index < self.view.thumbnail_list.count()):
            return
        self._syncing_thumbnails = True
        if force_single or len(self.view.thumbnail_list.selectedIndexes()) <= 1:
            self.view.thumbnail_list.setCurrentRow(page_index)
            self.view._on_thumbnail_selection_changed()
        item = self.view.thumbnail_list.item(page_index)
        if item is not None:
            self.view.thumbnail_list.scrollToItem(item)
        self._syncing_thumbnails = False

    def on_continuous_mode_toggled(self, _enabled: bool):
        """상단 툴바 [연속 스크롤] 버튼 전환 시 즉시 뷰어 구성을 전환합니다."""
        if self.pdf.page_count == 0:
            return
        self.render_current_page(
            sync_selection=False, rebuild_layout=True, scroll_to_current=True
        )

    def on_page_render_requested(self, page_index: int):
        """가상화 연속 스크롤에서 화면에 보이는 페이지의 QPixmap만 온디맨드로 렌더링하여 공급합니다."""
        if not (0 <= page_index < self.pdf.page_count):
            return
        pixmap = self.pdf.get_page_pixmap(
            page_index, zoom=self.zoom, as_qpixmap=True
        )
        if isinstance(pixmap, QPixmap):
            self.view.set_continuous_page_pixmap(page_index, pixmap)

    def on_canvas_page_scrolled(self, page_index: int):
        """오른쪽 연속 스크롤 뷰어에서 스크롤로 페이지가 바뀌었을 때 왼쪽 썸네일 및 상태바를 동기화합니다."""
        if not (0 <= page_index < self.pdf.page_count):
            return
        if page_index != self.current_page:
            self.current_page = page_index
            self._sync_left_thumbnail_selection(page_index, force_single=False)
            self.view.update_page_status(
                self.current_page + 1, self.pdf.page_count, self.zoom
            )
            self._update_action_states()

    def on_boundary_page_step(self, step: int):
        """단일 페이지 모드에서 스크롤 상/하단 끝 도달 후 마우스 휠을 굴렸을 때 페이지 이동"""
        if step > 0:
            self.next_page()
        elif step < 0:
            self.prev_page()

    def on_key_page_navigation(self, action: str):
        """오른쪽 뷰어에서 키보드(PgUp/PgDn/방향키/Home/End/Space)로 페이지 이동"""
        if self.pdf.page_count == 0:
            return
        if action == "prev":
            self.prev_page()
        elif action == "next":
            self.next_page()
        elif action == "first":
            self.go_to_page(0, sync_selection=True)
        elif action == "last":
            self.go_to_page(self.pdf.page_count - 1, sync_selection=True)

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
    # 2. 캔버스 마우스 인터랙션 (연속 스크롤 페이지별 좌표 및 단일 페이지 모두 지원)
    # -------------------------------------------------------------------------
    def on_canvas_interacted(self, screen_rect: QRectF, mode: CursorMode):
        self.on_page_canvas_interacted(self.current_page, screen_rect, mode)

    def on_page_canvas_interacted(
        self, page_index: int, screen_rect: QRectF, mode: CursorMode
    ):
        if self.pdf.page_count == 0:
            return
        target_page = (
            page_index
            if 0 <= page_index < self.pdf.page_count
            else self.current_page
        )
        if target_page != self.current_page:
            self.current_page = target_page
            self._sync_left_thumbnail_selection(target_page, force_single=False)
            self.view.update_page_status(
                self.current_page + 1, self.pdf.page_count, self.zoom
            )

        page_origin = self.pdf.get_page_origin(target_page)
        pdf_rect = CoordConverter.screen_rect_to_pdf_rect(
            screen_rect, self.zoom, page_origin
        )
        tool_style = self.view.get_tool_style()

        if mode == CursorMode.BOX_REVIEW:
            box_color = tool_style.get("box_color", (1.0, 0.0, 0.0))
            box_width = float(tool_style.get("box_width", 2.0))
            if self.pdf.add_box_annotation(
                target_page, pdf_rect, color=box_color, width=box_width
            ):
                self.refresh_single_thumbnail(target_page)
                self._refresh_edited_page(target_page)

        elif mode == CursorMode.HIGHLIGHT:
            hl_color = tool_style.get("highlight_color", (1.0, 0.95, 0.0))
            if self.pdf.add_highlight(target_page, pdf_rect, color=hl_color):
                self.refresh_single_thumbnail(target_page)
                self._refresh_edited_page(target_page)

        elif mode == CursorMode.TEXT_EDIT:
            style_info = self.pdf.inspect_text_at_rect(target_page, pdf_rect)
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
                    page_num=target_page,
                    style_info=style_info,
                    new_text=new_text,
                    font_key=font_key,
                    font_size=font_size,
                    is_bold=is_bold,
                    is_italic=is_italic,
                    text_color=text_color,
                    y_offset=y_offset,
                ):
                    self.refresh_single_thumbnail(target_page)
                    self._refresh_edited_page(target_page)

    def on_cloud_polygon_completed(self, page_index: int, screen_points: list):
        """다중 클릭으로 지정된 빗금 다각형 영역을 클라우드 마크(Revision Cloud) 주석으로 변환합니다."""
        if self.pdf.page_count == 0 or len(screen_points) < 3:
            return
        target_page = (
            page_index
            if 0 <= page_index < self.pdf.page_count
            else self.current_page
        )
        if target_page != self.current_page:
            self.current_page = target_page
            self._sync_left_thumbnail_selection(target_page, force_single=False)
            self.view.update_page_status(
                self.current_page + 1, self.pdf.page_count, self.zoom
            )

        page_origin = self.pdf.get_page_origin(target_page)
        pdf_points = [
            CoordConverter.screen_point_to_pdf_point(pt, self.zoom, page_origin)
            for pt in screen_points
        ]
        tool_style = self.view.get_tool_style()
        cloud_color = tool_style.get("cloud_color", (0.93, 0.2, 0.2))
        cloud_width = float(tool_style.get("cloud_width", 2.2))
        cloud_scale = float(tool_style.get("cloud_scale", 2.5))

        if self.pdf.add_cloud_polygon_annotation(
            target_page,
            pdf_points,
            color=cloud_color,
            width=cloud_width,
            cloud_scale=cloud_scale,
        ):
            self.refresh_single_thumbnail(target_page)
            self._refresh_edited_page(target_page)

    def on_stamp_mark_clicked(self, page_index: int):
        """당초/변경 마크 모드에서 페이지 클릭 또는 [현재 페이지에 넣기] 버튼 클릭 시 우측 상단에 마크를 넣습니다."""
        if self.pdf.page_count == 0:
            return
        target_page = (
            page_index
            if 0 <= page_index < self.pdf.page_count
            else self.current_page
        )
        if target_page != self.current_page:
            self.current_page = target_page
            self._sync_left_thumbnail_selection(target_page, force_single=False)
            self.view.update_page_status(
                self.current_page + 1, self.pdf.page_count, self.zoom
            )

        st = self.view.get_tool_style()
        if self.pdf.add_stamp_mark_annotation(
            page_num=target_page,
            stamp_text=str(st.get("stamp_text", "당초")),
            box_width=float(st.get("stamp_box_w", 72.0)),
            box_height=float(st.get("stamp_box_h", 32.0)),
            border_color=st.get("stamp_color", (0.90, 0.08, 0.08)),
            border_width=float(st.get("stamp_border_width", 2.5)),
            font_key=str(st.get("stamp_font_key", "malgun")),
            font_size=float(st.get("stamp_font_size", 15.0)),
            is_bold=bool(st.get("stamp_is_bold", True)),
            top_margin_pt=float(st.get("stamp_top_margin", 24.0)),
            right_margin_pt=float(st.get("stamp_right_margin", 28.0)),
        ):
            self.refresh_single_thumbnail(target_page)
            self._refresh_edited_page(target_page)

    def on_stamp_batch_dialog_requested(self):
        """[페이지별 설정...] 버튼 또는 [작업] -> [당초/변경 마크 페이지별 설정...] 대화상자를 엽니다."""
        if self.pdf.page_count == 0 or self.pdf.doc is None:
            return

        st = self.view.get_tool_style()
        font_choices = self.pdf.get_available_font_choices()
        dlg = StampMarkDialog(
            doc=self.pdf.doc,
            font_choices=font_choices,
            current_page_index=self.current_page,
            default_stamp_text=str(st.get("stamp_text", "당초")),
            box_width=float(st.get("stamp_box_w", 72.0)),
            box_height=float(st.get("stamp_box_h", 32.0)),
            border_color=st.get("stamp_color", (0.90, 0.08, 0.08)),
            border_width=float(st.get("stamp_border_width", 2.5)),
            font_key=str(st.get("stamp_font_key", "malgun")),
            font_size=float(st.get("stamp_font_size", 15.0)),
            is_bold=bool(st.get("stamp_is_bold", True)),
            top_margin_pt=float(st.get("stamp_top_margin", 24.0)),
            right_margin_pt=float(st.get("stamp_right_margin", 28.0)),
            parent=self.view,
        )
        if dlg.exec():
            settings = dlg.get_settings()
            self.view.sync_stamp_settings(settings)
            page_stamp_map = settings.get("page_stamp_map", {})
            if page_stamp_map:
                modified = self.pdf.apply_stamp_marks_by_page(
                    page_stamp_map=page_stamp_map,
                    box_width=float(settings["box_width"]),
                    box_height=float(settings["box_height"]),
                    border_color=settings["border_color"],
                    border_width=float(settings["border_width"]),
                    font_key=str(settings["font_key"]),
                    font_size=float(settings["font_size"]),
                    is_bold=bool(settings["is_bold"]),
                    top_margin_pt=float(settings["top_margin_pt"]),
                    right_margin_pt=float(settings["right_margin_pt"]),
                )
                if modified:
                    for p_idx in modified:
                        self.refresh_single_thumbnail(p_idx)
                    self.render_current_page(
                        sync_selection=False,
                        rebuild_layout=True,
                        scroll_to_current=False,
                    )
                    self._update_window_title()
                    self._update_action_states()

    def _refresh_edited_page(self, page_index: int):
        """편집 완료 후 현재 스크롤 위치를 유지한 채 수정된 페이지만 즉시 갱신합니다."""
        if self.view.continuous_scroll:
            self.view.invalidate_continuous_page(page_index)
            self._update_window_title()
            self._update_action_states()
        else:
            self.render_current_page(sync_selection=False, scroll_to_current=False)

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
                self.render_current_page(
                    sync_selection=False, rebuild_layout=True, scroll_to_current=True
                )

    # -------------------------------------------------------------------------
    # 4. 썸네일/책갈피 클릭 및 다중 페이지 조작 (추출 저장 / 회전 / 삭제)
    # -------------------------------------------------------------------------
    def go_to_page(self, page_index: int, sync_selection: bool = True):
        if 0 <= page_index < self.pdf.page_count:
            self.current_page = page_index
            self.render_current_page(
                sync_selection=sync_selection,
                rebuild_layout=False,
                scroll_to_current=True,
            )

    def on_thumbnail_clicked(self, row: int):
        if self._syncing_thumbnails:
            return
        if 0 <= row < self.pdf.page_count:
            self.current_page = row
            self.render_current_page(
                sync_selection=False, rebuild_layout=False, scroll_to_current=True
            )

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_current_page(
                sync_selection=True, rebuild_layout=False, scroll_to_current=True
            )

    def next_page(self):
        if self.current_page < self.pdf.page_count - 1:
            self.current_page += 1
            self.render_current_page(
                sync_selection=True, rebuild_layout=False, scroll_to_current=True
            )

    def change_zoom(self, delta: float):
        if self.pdf.page_count == 0:
            return
        new_zoom = round(max(0.4, min(4.0, self.zoom + delta)), 2)
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self.render_current_page(
                sync_selection=False, rebuild_layout=True, scroll_to_current=True
            )

    def rotate_selected_pages(self):
        if self.pdf.page_count == 0:
            return
        selected = self.view.get_selected_page_indices()
        if self.pdf.rotate_pages(selected, angle=90):
            for p in selected:
                self.refresh_single_thumbnail(p)
            self.render_current_page(
                sync_selection=False, rebuild_layout=True, scroll_to_current=False
            )

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
                self.render_current_page(
                    sync_selection=True, rebuild_layout=True, scroll_to_current=True
                )

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
            self.render_current_page(
                sync_selection=True, rebuild_layout=True, scroll_to_current=True
            )

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
                self.render_current_page(
                    sync_selection=False, rebuild_layout=True, scroll_to_current=True
                )
            else:
                QMessageBox.critical(
                    self.view,
                    "페이지 합병 실패",
                    "선택한 PDF 페이지를 합병하는 중 오류가 발생했습니다.",
                )

    # -------------------------------------------------------------------------
    # 5. 파일 저장 / 새이름으로 / 문서닫기 / 인쇄 / 찾기 / 쪽번호넣기
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

    def save_file_as(self) -> bool:
        """[파일] -> [새이름으로] (Ctrl+Shift+S): 새 이름으로 PDF 파일 저장"""
        return self.save_file()

    def close_document(self):
        """[파일] -> [문서닫기] (Ctrl+W): 미저장 변경사항 확인 후 현재 문서를 닫고 초기 화면으로 복귀"""
        if self.pdf.page_count == 0:
            return
        if not self.confirm_unsaved_changes():
            return

        self.pdf.close_document()
        self.current_page = 0
        self.view.hide_find_bar()
        self.refresh_thumbnails()
        self.refresh_bookmarks()
        self.render_current_page()
        self._update_window_title()
        self._update_action_states()

    # -------------------------------------------------------------------------
    # 상단 슬림 찾기 바 (Ctrl+F) 및 초경량 검색 하이라이트 오버레이 제어
    # -------------------------------------------------------------------------
    def find_text_in_document(self):
        """[편집] -> [찾기] (Ctrl+F): 상단 인라인 찾기 바를 표시하고 입력창에 포커스"""
        if self.pdf.page_count == 0 or self.pdf.doc is None:
            return
        self.view.show_find_bar()

    def on_find_query_changed(self, raw_query: str):
        keyword = raw_query.strip()
        self._search_keyword = keyword
        self._search_matches.clear()
        self._search_current_idx = -1

        if not keyword or self.pdf.page_count == 0 or self.pdf.doc is None:
            self.view.set_find_status(0, 0, has_query=False)
            self.view.clear_search_highlights()
            return

        # C-엔진(MuPDF) page.search_for()로 순수 좌표(fitz.Rect)만 고속 수집
        for page_idx in range(self.pdf.page_count):
            for rect in self.pdf.doc[page_idx].search_for(keyword):
                self._search_matches.append((page_idx, rect))

        total = len(self._search_matches)
        if total == 0:
            self.view.set_find_status(0, 0, has_query=True)
            self.view.clear_search_highlights()
            return

        # 현재 보고 있는 페이지 이후의 첫 번째 일치 항목 선택 (없으면 첫 번째 항목)
        chosen_idx = 0
        for idx, (p_idx, _r) in enumerate(self._search_matches):
            if p_idx >= self.current_page:
                chosen_idx = idx
                break

        self._search_current_idx = chosen_idx
        self._focus_current_search_match(jump_to_match=True)

    def on_find_next_requested(self):
        if not self._search_matches:
            if self.view.find_input.text().strip():
                self.on_find_query_changed(self.view.find_input.text())
            return
        self._search_current_idx = (self._search_current_idx + 1) % len(
            self._search_matches
        )
        self._focus_current_search_match(jump_to_match=True)

    def on_find_prev_requested(self):
        if not self._search_matches:
            if self.view.find_input.text().strip():
                self.on_find_query_changed(self.view.find_input.text())
            return
        self._search_current_idx = (self._search_current_idx - 1) % len(
            self._search_matches
        )
        self._focus_current_search_match(jump_to_match=True)

    def on_find_closed(self):
        self._search_keyword = ""
        self._search_matches.clear()
        self._search_current_idx = -1
        self.view.set_find_status(0, 0, has_query=False)
        self.view.clear_search_highlights()

    def _sync_search_highlights_to_view(self) -> Optional[QRectF]:
        """현재 확대/축소(zoom) 배율에 맞춰 검색 결과 좌표를 화면 픽셀 QRectF로 변환해 오버레이에 전달합니다."""
        if not self._search_matches or self.pdf.page_count == 0:
            self.view.clear_search_highlights()
            return None

        page_rects_map: Dict[int, List[QRectF]] = {}
        active_page = -1
        active_screen_rect: Optional[QRectF] = None

        for idx, (p_idx, pdf_rect) in enumerate(self._search_matches):
            if not (0 <= p_idx < self.pdf.page_count):
                continue
            origin = self.pdf.get_page_origin(p_idx)
            s_rect = CoordConverter.pdf_rect_to_screen_rect(
                pdf_rect, self.zoom, origin
            )
            page_rects_map.setdefault(p_idx, []).append(s_rect)
            if idx == self._search_current_idx:
                active_page = p_idx
                active_screen_rect = s_rect

        self.view.update_search_highlights(
            page_rects_map, active_page=active_page, active_rect=active_screen_rect
        )
        return active_screen_rect

    def _focus_current_search_match(self, jump_to_match: bool = True):
        total = len(self._search_matches)
        if total == 0 or not (0 <= self._search_current_idx < total):
            self.view.set_find_status(0, 0, has_query=bool(self._search_keyword))
            self.view.clear_search_highlights()
            return

        self.view.set_find_status(
            self._search_current_idx + 1, total, has_query=True
        )
        target_page, _pdf_rect = self._search_matches[self._search_current_idx]

        if jump_to_match and target_page != self.current_page:
            self.go_to_page(target_page, sync_selection=True)

        active_screen_rect = self._sync_search_highlights_to_view()
        if jump_to_match and active_screen_rect is not None:
            self.view.scroll_to_search_rect(target_page, active_screen_rect)

    def on_print_requested(self):
        """[파일] -> [인쇄] (Ctrl+P)"""
        if self.pdf.page_count == 0 or self.pdf.doc is None:
            return
        dlg = PrintDialog(self.pdf.doc, parent=self.view)
        dlg.exec()

    def on_print_setup_requested(self):
        """[파일] -> [인쇄설정] (Ctrl+Shift+P) - 시스템 인쇄 대화상자"""
        if self.pdf.page_count == 0 or self.pdf.doc is None:
            return
        dlg = PrintDialog(self.pdf.doc, parent=self.view)
        dlg.open_system_print_dialog()

    def on_insert_page_numbers_requested(self):
        """[작업] -> [쪽번호넣기] (Ctrl+Shift+N)"""
        if self.pdf.page_count == 0 or self.pdf.doc is None:
            return
        dlg = PageNumberDialog(
            self.pdf.doc,
            current_page_index=self.current_page,
            parent=self.view,
        )
        if dlg.exec():
            opts = dlg.get_options()
            modified = self.pdf.insert_page_numbers(
                start_page_index=int(opts["start_page_index"]),
                end_page_index=int(opts["end_page_index"]),
                start_number=int(opts["start_number"]),
                alignment=str(opts["alignment"]),
                bottom_offset_pt=float(opts["bottom_offset_pt"]),
                horizontal_margin_pt=float(opts["horizontal_margin_pt"]),
                font_size=float(opts["font_size"]),
                format_template=str(opts["format_template"]),
            )
            if modified:
                for p_idx in modified:
                    self.refresh_single_thumbnail(p_idx)
                self.render_current_page(
                    sync_selection=False,
                    rebuild_layout=True,
                    scroll_to_current=False,
                )
                self._update_window_title()
                self._update_action_states()

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
        if hasattr(self.view, "act_save_as"):
            self.view.act_save_as.setEnabled(has_doc)
        if hasattr(self.view, "act_close_doc"):
            self.view.act_close_doc.setEnabled(has_doc)
        if hasattr(self.view, "act_print"):
            self.view.act_print.setEnabled(has_doc)
        if hasattr(self.view, "act_print_setup"):
            self.view.act_print_setup.setEnabled(has_doc)
        if hasattr(self.view, "act_find"):
            self.view.act_find.setEnabled(has_doc)
        if hasattr(self.view, "act_insert_page_numbers"):
            self.view.act_insert_page_numbers.setEnabled(has_doc)
        if hasattr(self.view, "act_stamp_batch_dialog"):
            self.view.act_stamp_batch_dialog.setEnabled(has_doc)
        if hasattr(self.view, "btn_stamp_apply_cur"):
            self.view.btn_stamp_apply_cur.setEnabled(has_doc)
        if hasattr(self.view, "btn_stamp_open_batch"):
            self.view.btn_stamp_open_batch.setEnabled(has_doc)

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
