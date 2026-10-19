import os
from typing import List, Optional, Tuple
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from src.models.pdf_handler import PdfHandler


class PreviewThumbWidget(QWidget):
    """
    합병 다이얼로그 내 미리보기 썸네일 아이템 위젯.
    메인 윈도우와 동일하게 아래쪽 '1p' 텍스트는 하이라이트에서 제외하고
    상단 썸네일 이미지 박스에만 선택 테두리를 표시합니다.
    """

    def __init__(self, page_number: int, pixmap: Optional[QPixmap], parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_box = QLabel()
        self.image_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_box.setFixedSize(96, 128)
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                84,
                116,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_box.setPixmap(scaled)
        else:
            self.image_box.setText("미리보기 없음")

        self.page_label = QLabel(f"{page_number}p")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet(
            "color: #52525b; font-size: 11px; font-weight: 600; background: transparent; border: none;"
        )

        layout.addWidget(self.image_box, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.page_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.set_selected(False)

    def set_selected(self, selected: bool):
        if selected:
            self.image_box.setStyleSheet(
                """
                QLabel {
                    background-color: #f4f4f5;
                    border: 2.5px solid #18181b;
                    border-radius: 5px;
                    padding: 3px;
                }
                """
            )
            self.page_label.setStyleSheet(
                "color: #18181b; font-size: 11px; font-weight: 700; background: transparent; border: none;"
            )
        else:
            self.image_box.setStyleSheet(
                """
                QLabel {
                    background-color: #ffffff;
                    border: 1px solid #e4e4e7;
                    border-radius: 5px;
                    padding: 4px;
                }
                """
            )
            self.page_label.setStyleSheet(
                "color: #52525b; font-size: 11px; font-weight: 600; background: transparent; border: none;"
            )


class MergePagesDialog(QDialog):
    """
    다른 PDF 파일의 페이지를 미리보고, 가져올 페이지 범위와 현재 문서 내 삽입 위치를
    선택하여 합병(삽입)하는 모던 그레이스케일 설정 대화상자
    """

    def __init__(
        self,
        source_pdf_path: str,
        doc_page_count: int,
        current_page_index: int = 0,
        preset_slot: Optional[int] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("다른 PDF 파일 합병 (페이지 삽입)")
        self.resize(620, 560)

        self.source_pdf_path: str = source_pdf_path
        self.doc_page_count: int = max(0, doc_page_count)
        self.current_page_index: int = max(0, current_page_index)
        self.preset_slot: Optional[int] = preset_slot

        self.source_total_pages: int = 0
        self._syncing_selection: bool = False

        self._init_ui()
        self._apply_styles()
        self._load_source_pdf(self.source_pdf_path)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(12)

        # -----------------------------------------------------------------
        # 1. 합병할 PDF 파일 정보 및 [파일 변경] 버튼
        # -----------------------------------------------------------------
        grp_file = QGroupBox("1. 합병할 PDF 파일")
        file_layout = QHBoxLayout(grp_file)
        file_layout.setContentsMargins(12, 14, 12, 10)
        file_layout.setSpacing(8)

        self.lbl_file_info = QLabel("파일을 불러오는 중...")
        self.lbl_file_info.setObjectName("FileInfoLabel")

        self.btn_change_file = QPushButton("파일 변경...")
        self.btn_change_file.setObjectName("SecondaryBtn")
        self.btn_change_file.setFixedWidth(96)
        self.btn_change_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_change_file.clicked.connect(self._on_change_file_clicked)

        file_layout.addWidget(self.lbl_file_info, stretch=1)
        file_layout.addWidget(self.btn_change_file)
        root_layout.addWidget(grp_file)

        # -----------------------------------------------------------------
        # 2. 가져올 페이지 선택 (썸네일 미리보기 + 전체/지정 범위 라디오)
        # -----------------------------------------------------------------
        grp_pages = QGroupBox("2. 가져올 페이지 선택 (미리보기 클릭 / Ctrl·Shift 다중 선택 가능)")
        pages_layout = QVBoxLayout(grp_pages)
        pages_layout.setContentsMargins(12, 14, 12, 12)
        pages_layout.setSpacing(8)

        self.preview_list = QListWidget()
        self.preview_list.setObjectName("PreviewThumbList")
        self.preview_list.setFlow(QListWidget.Flow.LeftToRight)
        self.preview_list.setWrapping(False)
        self.preview_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.preview_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.preview_list.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.preview_list.setFixedHeight(175)
        self.preview_list.setSpacing(6)
        self.preview_list.itemSelectionChanged.connect(
            self._on_preview_selection_changed
        )
        pages_layout.addWidget(self.preview_list)

        self.src_mode_group = QButtonGroup(self)
        self.rb_all_pages = QRadioButton("전체 페이지 가져오기")
        self.rb_custom_pages = QRadioButton("선택/지정 페이지만 가져오기:")
        self.rb_all_pages.setChecked(True)

        self.src_mode_group.addButton(self.rb_all_pages, 0)
        self.src_mode_group.addButton(self.rb_custom_pages, 1)

        self.edit_page_range = QLineEdit()
        self.edit_page_range.setPlaceholderText("예: 1, 3, 5-8")
        self.edit_page_range.textEdited.connect(self._on_range_text_edited)

        self.rb_all_pages.toggled.connect(self._on_src_mode_toggled)

        pages_layout.addWidget(self.rb_all_pages)

        custom_row = QHBoxLayout()
        custom_row.setSpacing(8)
        custom_row.addWidget(self.rb_custom_pages)
        custom_row.addWidget(self.edit_page_range, stretch=1)
        pages_layout.addLayout(custom_row)

        root_layout.addWidget(grp_pages)

        # -----------------------------------------------------------------
        # 3. 현재 문서에 삽입할 위치
        # -----------------------------------------------------------------
        grp_pos = QGroupBox("3. 현재 문서에 삽입할 위치")
        pos_layout = QVBoxLayout(grp_pos)
        pos_layout.setContentsMargins(12, 14, 12, 12)
        pos_layout.setSpacing(6)

        self.pos_group = QButtonGroup(self)

        cur_p_display = self.current_page_index + 1
        total_display = self.doc_page_count

        self.rb_pos_start = QRadioButton("문서 맨 앞 (1페이지 앞)")
        self.rb_pos_before_cur = QRadioButton(
            f"현재 선택된 페이지 앞 ({cur_p_display}페이지 앞)"
        )
        self.rb_pos_after_cur = QRadioButton(
            f"현재 선택된 페이지 뒤 ({cur_p_display}페이지 뒤)"
        )
        self.rb_pos_end = QRadioButton(
            f"문서 맨 끝 (마지막 {total_display}페이지 뒤)"
            if total_display > 0
            else "새 문서로 열기 (현재 열려있는 문서 없음)"
        )

        self.pos_group.addButton(self.rb_pos_start, 0)
        self.pos_group.addButton(self.rb_pos_before_cur, 1)
        self.pos_group.addButton(self.rb_pos_after_cur, 2)
        self.pos_group.addButton(self.rb_pos_end, 3)

        pos_layout.addWidget(self.rb_pos_start)
        pos_layout.addWidget(self.rb_pos_before_cur)
        pos_layout.addWidget(self.rb_pos_after_cur)
        pos_layout.addWidget(self.rb_pos_end)

        # 드래그 앤 드롭이나 우클릭 메뉴로 특정 슬롯 위치가 전달된 경우 라디오 버튼에 반영
        self.rb_pos_preset: Optional[QRadioButton] = None
        if self.doc_page_count == 0:
            self.rb_pos_start.setEnabled(False)
            self.rb_pos_before_cur.setEnabled(False)
            self.rb_pos_after_cur.setEnabled(False)
            self.rb_pos_end.setChecked(True)
        else:
            if self.preset_slot is not None:
                slot = max(0, min(self.doc_page_count, self.preset_slot))
                if slot == 0:
                    self.rb_pos_start.setChecked(True)
                elif slot == self.current_page_index:
                    self.rb_pos_before_cur.setChecked(True)
                elif slot == self.current_page_index + 1:
                    self.rb_pos_after_cur.setChecked(True)
                elif slot == self.doc_page_count:
                    self.rb_pos_end.setChecked(True)
                else:
                    self.rb_pos_preset = QRadioButton(
                        f"지정한 위치 ({slot}페이지와 {slot + 1}페이지 사이)"
                    )
                    self.pos_group.addButton(self.rb_pos_preset, 4)
                    pos_layout.addWidget(self.rb_pos_preset)
                    self.rb_pos_preset.setChecked(True)
            else:
                self.rb_pos_after_cur.setChecked(True)

        root_layout.addWidget(grp_pos)

        # -----------------------------------------------------------------
        # 4. 하단 [취소] / [합병 실행] 버튼
        # -----------------------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("SecondaryBtn")
        self.btn_cancel.setFixedWidth(88)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_merge = QPushButton("합병 실행")
        self.btn_merge.setObjectName("PrimaryBtn")
        self.btn_merge.setFixedWidth(110)
        self.btn_merge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_merge.clicked.connect(self._on_accept_clicked)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_merge)
        root_layout.addLayout(btn_row)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #ffffff;
                color: #18181b;
                font-family: "Malgun Gothic", "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                background-color: #fafafa;
                border: 1px solid #e4e4e7;
                border-radius: 7px;
                margin-top: 8px;
                font-weight: 700;
                color: #27272a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLabel#FileInfoLabel {
                background-color: #ffffff;
                border: 1px solid #d4d4d8;
                border-radius: 5px;
                padding: 6px 10px;
                color: #18181b;
                font-weight: 600;
            }
            QListWidget#PreviewThumbList {
                background-color: #ffffff;
                border: 1px solid #e4e4e7;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget#PreviewThumbList::item {
                background: transparent;
                border: none;
            }
            QListWidget#PreviewThumbList::item:selected {
                background: transparent;
                border: none;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d4d4d8;
                border-radius: 5px;
                padding: 5px 8px;
                color: #18181b;
            }
            QLineEdit:focus {
                border: 1.5px solid #18181b;
            }
            QPushButton#SecondaryBtn {
                background-color: #ffffff;
                color: #3f3f46;
                border: 1px solid #d4d4d8;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton#SecondaryBtn:hover {
                background-color: #f4f4f5;
                color: #18181b;
                border-color: #a1a1aa;
            }
            QPushButton#PrimaryBtn {
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #18181b;
                border-radius: 5px;
                padding: 6px 14px;
                font-weight: 700;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #27272a;
            }
            """
        )

    # -------------------------------------------------------------------------
    # 원본 PDF 로드 및 썸네일/페이지 범위 동기화
    # -------------------------------------------------------------------------
    def _load_source_pdf(self, file_path: str) -> bool:
        total, thumbs = PdfHandler.inspect_external_pdf(file_path, thumb_zoom=0.2)
        if total <= 0:
            self.lbl_file_info.setText("파일을 열 수 없거나 유효한 페이지가 없습니다.")
            self.source_total_pages = 0
            self.preview_list.clear()
            self.btn_merge.setEnabled(False)
            return False

        self.source_pdf_path = file_path
        self.source_total_pages = total
        self.btn_merge.setEnabled(True)

        name = os.path.basename(file_path)
        self.lbl_file_info.setText(f"{name}  (총 {total} 페이지)")
        self.rb_all_pages.setText(f"전체 페이지 가져오기 (1 ~ {total}p)")

        self._syncing_selection = True
        self.preview_list.clear()
        for idx, pix in enumerate(thumbs):
            item = QListWidgetItem()
            widget = PreviewThumbWidget(idx + 1, pix)
            item.setSizeHint(QSize(106, 156))
            self.preview_list.addItem(item)
            self.preview_list.setItemWidget(item, widget)
            item.setSelected(True)

        self.rb_all_pages.setChecked(True)
        self.edit_page_range.setText(f"1-{total}" if total > 1 else "1")
        self._update_preview_highlights()
        self._syncing_selection = False
        return True

    def _on_change_file_clicked(self):
        new_path, _ = QFileDialog.getOpenFileName(
            self,
            "합병할 PDF 파일 선택",
            os.path.dirname(self.source_pdf_path) if self.source_pdf_path else "",
            "PDF Files (*.pdf)",
        )
        if new_path:
            if not self._load_source_pdf(new_path):
                QMessageBox.warning(
                    self,
                    "파일 열기 실패",
                    "선택한 PDF 파일을 열 수 없거나 암호로 보호되어 있습니다.",
                )

    def _update_preview_highlights(self):
        selected_rows = set(idx.row() for idx in self.preview_list.selectedIndexes())
        for i in range(self.preview_list.count()):
            item = self.preview_list.item(i)
            widget = self.preview_list.itemWidget(item)
            if isinstance(widget, PreviewThumbWidget):
                widget.set_selected(i in selected_rows)

    def _on_preview_selection_changed(self):
        self._update_preview_highlights()
        if self._syncing_selection or self.source_total_pages <= 0:
            return

        selected_rows = sorted(idx.row() for idx in self.preview_list.selectedIndexes())
        self._syncing_selection = True
        if len(selected_rows) == self.source_total_pages:
            self.rb_all_pages.setChecked(True)
        else:
            self.rb_custom_pages.setChecked(True)

        self.edit_page_range.setText(self._indices_to_range_str(selected_rows))
        self._syncing_selection = False

    def _on_src_mode_toggled(self, all_checked: bool):
        if self._syncing_selection or self.source_total_pages <= 0:
            return
        if all_checked:
            self._syncing_selection = True
            self.preview_list.selectAll()
            self._update_preview_highlights()
            self.edit_page_range.setText(
                f"1-{self.source_total_pages}"
                if self.source_total_pages > 1
                else "1"
            )
            self._syncing_selection = False
        else:
            self.edit_page_range.setFocus()

    def _on_range_text_edited(self, text: str):
        if self._syncing_selection or self.source_total_pages <= 0:
            return

        self._syncing_selection = True
        if self.edit_page_range.text() != text:
            self.edit_page_range.setText(text)
        self.rb_custom_pages.setChecked(True)
        parsed = self._parse_range_str(text, self.source_total_pages)
        self.preview_list.clearSelection()
        for r in parsed:
            if 0 <= r < self.preview_list.count():
                self.preview_list.item(r).setSelected(True)
        self._update_preview_highlights()
        self._syncing_selection = False

    @staticmethod
    def _indices_to_range_str(indices: List[int]) -> str:
        if not indices:
            return ""
        pages = [i + 1 for i in sorted(set(indices))]
        ranges: List[str] = []
        start = prev = pages[0]
        for p in pages[1:]:
            if p == prev + 1:
                prev = p
            else:
                ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
                start = prev = p
        ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
        return ", ".join(ranges)

    @staticmethod
    def _parse_range_str(text: str, max_pages: int) -> List[int]:
        """'1, 3, 5-8' 같은 문자열을 0-based 페이지 인덱스 리스트로 파싱합니다."""
        result: List[int] = []
        seen = set()
        for part in text.replace("p", "").replace("P", "").split(","):
            token = part.strip()
            if not token:
                continue
            if "-" in token:
                bounds = token.split("-", 1)
                if bounds[0].strip().isdigit() and bounds[1].strip().isdigit():
                    a = int(bounds[0].strip())
                    b = int(bounds[1].strip())
                    step = 1 if a <= b else -1
                    for p in range(a, b + step, step):
                        if 1 <= p <= max_pages and (p - 1) not in seen:
                            seen.add(p - 1)
                            result.append(p - 1)
            elif token.isdigit():
                p = int(token)
                if 1 <= p <= max_pages and (p - 1) not in seen:
                    seen.add(p - 1)
                    result.append(p - 1)
        return result

    def _on_accept_clicked(self):
        pages = self.get_selected_source_pages()
        if not pages:
            QMessageBox.warning(
                self,
                "페이지 선택 오류",
                f"가져올 페이지를 1개 이상 선택하거나 유효한 페이지 범위(1 ~ {self.source_total_pages})를 입력해 주세요.",
            )
            return
        self.accept()

    # -------------------------------------------------------------------------
    # 결과 반환 메서드
    # -------------------------------------------------------------------------
    def get_selected_source_pages(self) -> List[int]:
        if self.source_total_pages <= 0:
            return []
        if self.rb_all_pages.isChecked():
            return list(range(self.source_total_pages))
        parsed = self._parse_range_str(
            self.edit_page_range.text(), self.source_total_pages
        )
        if parsed:
            return parsed
        return sorted(idx.row() for idx in self.preview_list.selectedIndexes())

    def get_insert_slot(self) -> int:
        if self.doc_page_count == 0:
            return 0
        checked_id = self.pos_group.checkedId()
        if checked_id == 0:
            return 0
        elif checked_id == 1:
            return self.current_page_index
        elif checked_id == 2:
            return self.current_page_index + 1
        elif checked_id == 3:
            return self.doc_page_count
        elif checked_id == 4 and self.preset_slot is not None:
            return max(0, min(self.doc_page_count, self.preset_slot))
        return self.doc_page_count

    def get_merge_Result(self) -> Tuple[str, List[int], int]:
        return (
            self.source_pdf_path,
            self.get_selected_source_pages(),
            self.get_insert_slot(),
        )
