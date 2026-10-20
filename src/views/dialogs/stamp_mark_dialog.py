from typing import Dict, List, Optional, Tuple
import fitz
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
)
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QSplitter,
    QScrollArea,
    QDoubleSpinBox,
    QColorDialog,
)
from src.views.dialogs.print_dialog import ModernSpinBox


class StampMarkDialog(QDialog):
    """
    페이지별 당초/변경 마크 설정 및 일괄·개별 삽입 대화상자
    - 각 페이지별로 [미적용] / [당초] / [변경]을 개별 선택하거나 구간 일괄 지정
    - 박스 가로·세로 크기, 테두리 색상·굵기, 글자 크기·폰트, 우측 상단 여백 조정
    - 좌측 미리보기 창에서 페이지 우측 상단에 배치될 당초/변경 마크를 실시간으로 확인
    """

    def __init__(
        self,
        doc: fitz.Document,
        font_choices: List[Tuple[str, str]],
        current_page_index: int = 0,
        default_stamp_text: str = "당초",
        box_width: float = 72.0,
        box_height: float = 32.0,
        border_color: Tuple[float, float, float] = (0.90, 0.08, 0.08),
        border_width: float = 2.5,
        font_key: str = "malgun",
        font_size: float = 15.0,
        is_bold: bool = True,
        top_margin_pt: float = 24.0,
        right_margin_pt: float = 28.0,
        parent=None,
    ):
        super().__init__(parent)
        self.doc = doc
        self.font_choices = font_choices or [("malgun", "맑은 고딕 (Malgun Gothic)")]
        self.total_pages = len(doc) if doc is not None else 0
        self.preview_page_index = max(0, min(self.total_pages - 1, current_page_index))

        self._default_stamp_text = default_stamp_text if default_stamp_text in ("당초", "변경") else "당초"
        self._box_width = float(box_width)
        self._box_height = float(box_height)
        self._border_color = border_color
        self._border_width = float(border_width)
        self._font_key = font_key
        self._font_size = float(font_size)
        self._is_bold = bool(is_bold)
        self._top_margin_pt = float(top_margin_pt)
        self._right_margin_pt = float(right_margin_pt)

        # 페이지별 상태 저장: {page_idx: "" | "당초" | "변경"}
        self._page_states: Dict[int, str] = {i: "" for i in range(self.total_pages)}
        if 0 <= current_page_index < self.total_pages:
            self._page_states[current_page_index] = self._default_stamp_text

        self._row_btn_groups: Dict[int, QButtonGroup] = {}

        self.setWindowTitle("당초 / 변경 마크 페이지별 설정 및 넣기")
        self.setMinimumSize(940, 640)
        self.resize(1020, 700)

        self._init_ui()
        self._apply_styles()
        self._connect_signals()
        self._update_color_btn_style()
        self._update_preview()

    def _init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setObjectName("StampSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(5)

        # =====================================================================
        # 1. 좌측 실시간 페이지 우측 상단 미리보기 영역
        # =====================================================================
        left_widget = QFrame(self)
        left_widget.setObjectName("StampPreviewPane")
        left_widget.setMinimumWidth(420)
        left_vbox = QVBoxLayout(left_widget)
        left_vbox.setContentsMargins(18, 16, 18, 16)
        left_vbox.setSpacing(10)

        nav_bar = QHBoxLayout()
        lbl_prev_title = QLabel("실시간 우측 상단 미리보기")
        lbl_prev_title.setObjectName("PreviewHeaderTitle")

        self.chk_zoom_corner = QCheckBox("우측 상단 확대 보기")
        self.chk_zoom_corner.setObjectName("ZoomCornerCheck")
        self.chk_zoom_corner.setChecked(True)
        self.chk_zoom_corner.setToolTip(
            "체크하면 페이지 우측 상단 영역을 확대하여 당초/변경 마크 크기와 여백을 정밀하게 확인합니다"
        )

        self.btn_prev_page = QPushButton("◀")
        self.btn_prev_page.setObjectName("PreviewNavBtn")
        self.btn_prev_page.setFixedSize(28, 26)
        self.btn_prev_page.setCursor(Qt.CursorShape.PointingHandCursor)

        self.lbl_preview_page = QLabel("1 / 1 페이지")
        self.lbl_preview_page.setObjectName("PreviewPageLabel")
        self.lbl_preview_page.setMinimumWidth(90)
        self.lbl_preview_page.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_next_page = QPushButton("▶")
        self.btn_next_page.setObjectName("PreviewNavBtn")
        self.btn_next_page.setFixedSize(28, 26)
        self.btn_next_page.setCursor(Qt.CursorShape.PointingHandCursor)

        nav_bar.addWidget(lbl_prev_title)
        nav_bar.addStretch(1)
        nav_bar.addWidget(self.chk_zoom_corner)
        nav_bar.addSpacing(8)
        nav_bar.addWidget(self.btn_prev_page)
        nav_bar.addWidget(self.lbl_preview_page)
        nav_bar.addWidget(self.btn_next_page)
        left_vbox.addLayout(nav_bar)

        self.preview_canvas = QLabel(self)
        self.preview_canvas.setObjectName("PreviewCanvasLabel")
        self.preview_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_canvas.setMinimumSize(380, 480)
        left_vbox.addWidget(self.preview_canvas, stretch=1)

        self.lbl_preview_status = QLabel("")
        self.lbl_preview_status.setObjectName("PreviewStatusBanner")
        self.lbl_preview_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_vbox.addWidget(self.lbl_preview_status)

        # =====================================================================
        # 2. 우측 설정 영역 (페이지별 당초/변경 지정 + 박스/테두리/폰트/여백 설정)
        # =====================================================================
        right_widget = QFrame(self)
        right_widget.setObjectName("StampSettingsPane")
        right_widget.setMinimumWidth(470)
        right_vbox = QVBoxLayout(right_widget)
        right_vbox.setContentsMargins(20, 16, 20, 16)
        right_vbox.setSpacing(12)

        # [섹션 1] 페이지별 당초 / 변경 개별 및 일괄 선택
        sec1 = self._make_section_card("1. 페이지별 당초 / 변경 지정")
        s1_layout = QVBoxLayout()
        s1_layout.setSpacing(8)

        batch_row = QHBoxLayout()
        batch_row.setSpacing(6)
        lbl_range = QLabel("구간:")
        lbl_range.setObjectName("FieldLabel")
        self.spin_range_start = ModernSpinBox(self)
        self.spin_range_start.setRange(1, max(1, self.total_pages))
        self.spin_range_start.setValue(1)
        self.spin_range_start.setSuffix(" p")
        self.spin_range_start.setFixedWidth(74)

        lbl_tilde = QLabel("~")
        self.spin_range_end = ModernSpinBox(self)
        self.spin_range_end.setRange(1, max(1, self.total_pages))
        self.spin_range_end.setValue(max(1, self.total_pages))
        self.spin_range_end.setSuffix(" p")
        self.spin_range_end.setFixedWidth(74)

        self.btn_batch_orig = QPushButton("구간 '당초'")
        self.btn_batch_orig.setObjectName("QuickActionBtn")
        self.btn_batch_orig.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_batch_rev = QPushButton("구간 '변경'")
        self.btn_batch_rev.setObjectName("QuickActionBtn")
        self.btn_batch_rev.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_batch_clear = QPushButton("전체 해제")
        self.btn_batch_clear.setObjectName("QuickActionBtn")
        self.btn_batch_clear.setCursor(Qt.CursorShape.PointingHandCursor)

        batch_row.addWidget(lbl_range)
        batch_row.addWidget(self.spin_range_start)
        batch_row.addWidget(lbl_tilde)
        batch_row.addWidget(self.spin_range_end)
        batch_row.addWidget(self.btn_batch_orig)
        batch_row.addWidget(self.btn_batch_rev)
        batch_row.addWidget(self.btn_batch_clear)
        batch_row.addStretch(1)
        s1_layout.addLayout(batch_row)

        # 페이지별 스크롤 리스트
        self.page_scroll = QScrollArea(self)
        self.page_scroll.setObjectName("PageAssignScroll")
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setMinimumHeight(175)
        self.page_scroll.setMaximumHeight(220)

        scroll_content = QWidget()
        scroll_content.setObjectName("PageAssignContainer")
        self.page_rows_layout = QVBoxLayout(scroll_content)
        self.page_rows_layout.setContentsMargins(8, 6, 8, 6)
        self.page_rows_layout.setSpacing(4)

        for idx in range(self.total_pages):
            row_frame = QFrame(scroll_content)
            row_frame.setObjectName("PageAssignRow")
            r_layout = QHBoxLayout(row_frame)
            r_layout.setContentsMargins(8, 3, 8, 3)
            r_layout.setSpacing(6)

            lbl_p = QPushButton(f"{idx + 1} 페이지")
            lbl_p.setObjectName("PageJumpBtn")
            lbl_p.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl_p.setToolTip("클릭하여 좌측에서 이 페이지 미리보기")
            lbl_p.clicked.connect(lambda _, p=idx: self._jump_preview_page(p))

            grp = QButtonGroup(self)
            grp.setExclusive(True)

            btn_none = QPushButton("미적용")
            btn_none.setObjectName("StateSegBtn")
            btn_none.setCheckable(True)
            btn_none.setFixedWidth(64)

            btn_orig = QPushButton("당초")
            btn_orig.setObjectName("StateSegOrigBtn")
            btn_orig.setCheckable(True)
            btn_orig.setFixedWidth(64)

            btn_rev = QPushButton("변경")
            btn_rev.setObjectName("StateSegRevBtn")
            btn_rev.setCheckable(True)
            btn_rev.setFixedWidth(64)

            cur_val = self._page_states.get(idx, "")
            if cur_val == "당초":
                btn_orig.setChecked(True)
            elif cur_val == "변경":
                btn_rev.setChecked(True)
            else:
                btn_none.setChecked(True)

            grp.addButton(btn_none, 0)
            grp.addButton(btn_orig, 1)
            grp.addButton(btn_rev, 2)
            grp.idClicked.connect(lambda btn_id, p=idx: self._on_row_state_changed(p, btn_id))
            self._row_btn_groups[idx] = grp

            r_layout.addWidget(lbl_p)
            r_layout.addStretch(1)
            r_layout.addWidget(btn_none)
            r_layout.addWidget(btn_orig)
            r_layout.addWidget(btn_rev)
            self.page_rows_layout.addWidget(row_frame)

        self.page_rows_layout.addStretch(1)
        self.page_scroll.setWidget(scroll_content)
        s1_layout.addWidget(self.page_scroll)
        sec1.layout().addLayout(s1_layout)
        right_vbox.addWidget(sec1)

        # [섹션 2] 박스 크기 및 테두리 스타일 (색상 / 굵기)
        sec2 = self._make_section_card("2. 박스 크기 및 테두리 설정")
        g2 = QGridLayout()
        g2.setHorizontalSpacing(12)
        g2.setVerticalSpacing(8)

        lbl_bw = QLabel("박스 가로 폭:")
        lbl_bw.setObjectName("FieldLabel")
        self.spin_box_w = ModernSpinBox(self)
        self.spin_box_w.setRange(30, 260)
        self.spin_box_w.setValue(int(round(self._box_width)))
        self.spin_box_w.setSuffix(" pt")

        lbl_bh = QLabel("박스 세로 높이:")
        lbl_bh.setObjectName("FieldLabel")
        self.spin_box_h = ModernSpinBox(self)
        self.spin_box_h.setRange(18, 140)
        self.spin_box_h.setValue(int(round(self._box_height)))
        self.spin_box_h.setSuffix(" pt")

        lbl_color = QLabel("테두리/글자 색상:")
        lbl_color.setObjectName("FieldLabel")
        self.btn_pick_color = QPushButton("색상 선택")
        self.btn_pick_color.setFixedHeight(30)
        self.btn_pick_color.setCursor(Qt.CursorShape.PointingHandCursor)

        lbl_thick = QLabel("테두리 굵기:")
        lbl_thick.setObjectName("FieldLabel")
        self.spin_border_w = QDoubleSpinBox(self)
        self.spin_border_w.setObjectName("ModernDoubleSpin")
        self.spin_border_w.setRange(0.5, 10.0)
        self.spin_border_w.setSingleStep(0.5)
        self.spin_border_w.setDecimals(1)
        self.spin_border_w.setValue(self._border_width)
        self.spin_border_w.setSuffix(" pt")
        self.spin_border_w.setFixedHeight(30)

        g2.addWidget(lbl_bw, 0, 0)
        g2.addWidget(self.spin_box_w, 0, 1)
        g2.addWidget(lbl_bh, 0, 2)
        g2.addWidget(self.spin_box_h, 0, 3)
        g2.addWidget(lbl_color, 1, 0)
        g2.addWidget(self.btn_pick_color, 1, 1)
        g2.addWidget(lbl_thick, 1, 2)
        g2.addWidget(self.spin_border_w, 1, 3)
        sec2.layout().addLayout(g2)
        right_vbox.addWidget(sec2)

        # [섹션 3] 글자 폰트·크기 및 우측 상단 여백 위치 조정
        sec3 = self._make_section_card("3. 글자 폰트·크기 및 우측 상단 위치 조정")
        g3 = QGridLayout()
        g3.setHorizontalSpacing(12)
        g3.setVerticalSpacing(8)

        lbl_font = QLabel("글자 폰트:")
        lbl_font.setObjectName("FieldLabel")
        self.combo_font = QComboBox(self)
        self.combo_font.setObjectName("ModernCombo")
        self.combo_font.setFixedHeight(30)
        selected_font_idx = 0
        for idx, (fkey, flabel) in enumerate(self.font_choices):
            self.combo_font.addItem(flabel, fkey)
            if fkey == self._font_key:
                selected_font_idx = idx
        self.combo_font.setCurrentIndex(selected_font_idx)

        lbl_fsize = QLabel("글자 크기:")
        lbl_fsize.setObjectName("FieldLabel")
        fsize_row = QHBoxLayout()
        fsize_row.setSpacing(8)
        self.spin_font_size = ModernSpinBox(self)
        self.spin_font_size.setRange(8, 48)
        self.spin_font_size.setValue(int(round(self._font_size)))
        self.spin_font_size.setSuffix(" pt")

        self.chk_bold = QCheckBox("굵게(Bold)")
        self.chk_bold.setChecked(self._is_bold)
        fsize_row.addWidget(self.spin_font_size)
        fsize_row.addWidget(self.chk_bold)
        fsize_row.addStretch(1)

        lbl_top_m = QLabel("상단 여백:")
        lbl_top_m.setObjectName("FieldLabel")
        self.spin_top_margin = ModernSpinBox(self)
        self.spin_top_margin.setRange(4, 250)
        self.spin_top_margin.setValue(int(round(self._top_margin_pt)))
        self.spin_top_margin.setSuffix(" pt")

        lbl_right_m = QLabel("우측 여백:")
        lbl_right_m.setObjectName("FieldLabel")
        self.spin_right_margin = ModernSpinBox(self)
        self.spin_right_margin.setRange(4, 250)
        self.spin_right_margin.setValue(int(round(self._right_margin_pt)))
        self.spin_right_margin.setSuffix(" pt")

        g3.addWidget(lbl_font, 0, 0)
        g3.addWidget(self.combo_font, 0, 1, 1, 3)
        g3.addWidget(lbl_fsize, 1, 0)
        g3.addLayout(fsize_row, 1, 1, 1, 3)
        g3.addWidget(lbl_top_m, 2, 0)
        g3.addWidget(self.spin_top_margin, 2, 1)
        g3.addWidget(lbl_right_m, 2, 2)
        g3.addWidget(self.spin_right_margin, 2, 3)
        sec3.layout().addLayout(g3)
        right_vbox.addWidget(sec3)

        right_vbox.addStretch(1)

        # 하단 확인/취소 버튼
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)
        self.lbl_summary_count = QLabel("적용 대상: 1개 페이지")
        self.lbl_summary_count.setObjectName("FieldLabel")

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("DialogCancelBtn")
        self.btn_cancel.setFixedSize(96, 36)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_apply = QPushButton("선택한 페이지에 마크 넣기")
        self.btn_apply.setObjectName("DialogPrimaryBtn")
        self.btn_apply.setFixedSize(185, 36)
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_bar.addWidget(self.lbl_summary_count)
        btn_bar.addStretch(1)
        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_apply)
        right_vbox.addLayout(btn_bar)

        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([450, 550])
        root_layout.addWidget(self.splitter)
        self._update_summary_count()

    def _make_section_card(self, title: str) -> QFrame:
        card = QFrame(self)
        card.setObjectName("SectionCard")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(14, 10, 14, 12)
        vbox.setSpacing(8)
        lbl = QLabel(title)
        lbl.setObjectName("SectionTitle")
        vbox.addWidget(lbl)
        return card

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f8fafc;
            }
            QFrame#StampPreviewPane {
                background-color: #f1f5f9;
                border-right: 1px solid #e2e8f0;
            }
            QFrame#StampSettingsPane {
                background-color: #ffffff;
            }
            QLabel#PreviewHeaderTitle {
                color: #1e293b;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#PreviewPageLabel {
                color: #334155;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#PreviewNavBtn, QPushButton#QuickActionBtn {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#PreviewNavBtn:hover, QPushButton#QuickActionBtn:hover {
                background-color: #e2e8f0;
                color: #0f172a;
            }
            QLabel#PreviewCanvasLabel {
                background-color: #e2e8f0;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            QLabel#PreviewStatusBanner {
                background-color: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QFrame#SectionCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QLabel#SectionTitle {
                color: #0f172a;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#FieldLabel {
                color: #334155;
                font-size: 12px;
                font-weight: 600;
            }
            QScrollArea#PageAssignScroll {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QWidget#PageAssignContainer {
                background-color: #ffffff;
            }
            QFrame#PageAssignRow {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
            }
            QPushButton#PageJumpBtn {
                background-color: transparent;
                color: #1e293b;
                border: none;
                text-align: left;
                font-size: 12px;
                font-weight: 700;
                padding: 2px 4px;
            }
            QPushButton#PageJumpBtn:hover {
                color: #2563eb;
            }
            QPushButton#StateSegBtn, QPushButton#StateSegOrigBtn, QPushButton#StateSegRevBtn {
                background-color: #ffffff;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#StateSegBtn:checked {
                background-color: #64748b;
                color: #ffffff;
                border-color: #475569;
            }
            QPushButton#StateSegOrigBtn:checked {
                background-color: #dc2626;
                color: #ffffff;
                border-color: #b91c1c;
            }
            QPushButton#StateSegRevBtn:checked {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #1d4ed8;
            }
            QComboBox#ModernCombo, QDoubleSpinBox#ModernDoubleSpin {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QPushButton#DialogCancelBtn {
                background-color: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#DialogCancelBtn:hover {
                background-color: #e2e8f0;
            }
            QPushButton#DialogPrimaryBtn {
                background-color: #dc2626;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#DialogPrimaryBtn:hover {
                background-color: #b91c1c;
            }
            """
        )

    def _connect_signals(self):
        self.btn_prev_page.clicked.connect(self._on_prev_preview_page)
        self.btn_next_page.clicked.connect(self._on_next_preview_page)
        self.chk_zoom_corner.toggled.connect(self._update_preview)

        self.btn_batch_orig.clicked.connect(lambda: self._apply_batch_range("당초"))
        self.btn_batch_rev.clicked.connect(lambda: self._apply_batch_range("변경"))
        self.btn_batch_clear.clicked.connect(self._clear_all_pages)

        self.spin_box_w.valueChanged.connect(self._update_preview)
        self.spin_box_h.valueChanged.connect(self._update_preview)
        self.btn_pick_color.clicked.connect(self._on_pick_color)
        self.spin_border_w.valueChanged.connect(self._update_preview)
        self.combo_font.currentIndexChanged.connect(self._update_preview)
        self.spin_font_size.valueChanged.connect(self._update_preview)
        self.chk_bold.toggled.connect(self._update_preview)
        self.spin_top_margin.valueChanged.connect(self._update_preview)
        self.spin_right_margin.valueChanged.connect(self._update_preview)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.accept)

    def _update_color_btn_style(self):
        r = int(round(self._border_color[0] * 255))
        g = int(round(self._border_color[1] * 255))
        b = int(round(self._border_color[2] * 255))
        hex_c = f"#{r:02x}{g:02x}{b:02x}"
        self.btn_pick_color.setText(f"■ {hex_c.upper()}")
        self.btn_pick_color.setStyleSheet(
            f"background-color: #ffffff; color: {hex_c}; border: 1.5px solid {hex_c}; "
            f"border-radius: 5px; font-weight: 700; font-size: 12px;"
        )

    def _on_pick_color(self):
        r = int(round(self._border_color[0] * 255))
        g = int(round(self._border_color[1] * 255))
        b = int(round(self._border_color[2] * 255))
        initial = QColor(r, g, b)
        chosen = QColorDialog.getColor(initial, self, "당초/변경 마크 테두리 및 글자 색상 선택")
        if chosen.isValid():
            self._border_color = (chosen.redF(), chosen.greenF(), chosen.blueF())
            self._update_color_btn_style()
            self._update_preview()

    def _jump_preview_page(self, page_idx: int):
        if 0 <= page_idx < self.total_pages:
            self.preview_page_index = page_idx
            self._update_preview()

    def _on_row_state_changed(self, page_idx: int, btn_id: int):
        if btn_id == 1:
            self._page_states[page_idx] = "당초"
        elif btn_id == 2:
            self._page_states[page_idx] = "변경"
        else:
            self._page_states[page_idx] = ""
        self.preview_page_index = page_idx
        self._update_summary_count()
        self._update_preview()

    def _apply_batch_range(self, label_text: str):
        s_p = max(1, min(self.total_pages, self.spin_range_start.value()))
        e_p = max(s_p, min(self.total_pages, self.spin_range_end.value()))
        btn_id = 1 if label_text == "당초" else 2
        for p_idx in range(s_p - 1, e_p):
            self._page_states[p_idx] = label_text
            grp = self._row_btn_groups.get(p_idx)
            if grp and grp.button(btn_id):
                grp.button(btn_id).setChecked(True)
        self._update_summary_count()
        self._update_preview()

    def _clear_all_pages(self):
        for p_idx in range(self.total_pages):
            self._page_states[p_idx] = ""
            grp = self._row_btn_groups.get(p_idx)
            if grp and grp.button(0):
                grp.button(0).setChecked(True)
        self._update_summary_count()
        self._update_preview()

    def _update_summary_count(self):
        orig_cnt = sum(1 for v in self._page_states.values() if v == "당초")
        rev_cnt = sum(1 for v in self._page_states.values() if v == "변경")
        total_sel = orig_cnt + rev_cnt
        self.lbl_summary_count.setText(
            f"적용 대상: 총 {total_sel}p (당초 {orig_cnt}p / 변경 {rev_cnt}p)"
        )
        self.btn_apply.setEnabled(total_sel > 0)

    def _on_prev_preview_page(self):
        if self.preview_page_index > 0:
            self.preview_page_index -= 1
            self._update_preview()

    def _on_next_preview_page(self):
        if self.preview_page_index < self.total_pages - 1:
            self.preview_page_index += 1
            self._update_preview()

    def _update_preview(self):
        if self.doc is None or self.total_pages == 0:
            return

        self.lbl_preview_page.setText(
            f"{self.preview_page_index + 1} / {self.total_pages} 페이지"
        )
        self.btn_prev_page.setEnabled(self.preview_page_index > 0)
        self.btn_next_page.setEnabled(self.preview_page_index < self.total_pages - 1)

        page = self.doc[self.preview_page_index]
        p_rect = page.rect
        zoom_corner = self.chk_zoom_corner.isChecked()

        if zoom_corner:
            clip_w = min(p_rect.width, max(240.0, p_rect.width * 0.55))
            clip_h = min(p_rect.height, max(180.0, p_rect.height * 0.35))
            clip_rect = fitz.Rect(
                p_rect.x1 - clip_w,
                p_rect.y0,
                p_rect.x1,
                p_rect.y0 + clip_h,
            )
            render_scale = 1.8
            pix = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale), clip=clip_rect, alpha=False)
        else:
            clip_rect = p_rect
            render_scale = 1.0
            pix = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale), alpha=False)

        qimg = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        ).copy()
        canvas_pix = QPixmap.fromImage(qimg)

        state_txt = self._page_states.get(self.preview_page_index, "")
        preview_txt = state_txt if state_txt else f"{self._default_stamp_text} (미리보기)"
        actual_txt = state_txt if state_txt else self._default_stamp_text

        bw = float(self.spin_box_w.value())
        bh = float(self.spin_box_h.value())
        top_m = float(self.spin_top_margin.value())
        right_m = float(self.spin_right_margin.value())
        border_w = float(self.spin_border_w.value())
        fsize = float(self.spin_font_size.value())

        x1_pdf = p_rect.x1 - right_m
        x0_pdf = x1_pdf - bw
        y0_pdf = p_rect.y0 + top_m

        rx = (x0_pdf - clip_rect.x0) * render_scale
        ry = (y0_pdf - clip_rect.y0) * render_scale
        rw = bw * render_scale
        rh = bh * render_scale

        painter = QPainter(canvas_pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        r = int(round(self._border_color[0] * 255))
        g = int(round(self._border_color[1] * 255))
        b = int(round(self._border_color[2] * 255))
        alpha = 255 if state_txt else 135
        qcolor = QColor(r, g, b, alpha)

        pen = QPen(qcolor, max(1.0, border_w * render_scale))
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        target_qrect = QRectF(rx, ry, rw, rh)
        painter.drawRect(target_qrect)

        font = QFont("Malgun Gothic")
        font.setPixelSize(max(8, int(round(fsize * render_scale))))
        font.setBold(self.chk_bold.isChecked())
        painter.setFont(font)
        painter.drawText(target_qrect, Qt.AlignmentFlag.AlignCenter, actual_txt)
        painter.end()

        scaled_pix = canvas_pix.scaled(
            self.preview_canvas.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_canvas.setPixmap(scaled_pix)

        if state_txt:
            self.lbl_preview_status.setText(
                f"현재 {self.preview_page_index + 1}페이지 우측 상단에 [{state_txt}] 마크가 삽입됩니다."
            )
        else:
            self.lbl_preview_status.setText(
                f"현재 {self.preview_page_index + 1}페이지는 [미적용] 상태입니다. (반투명 점선 미리보기 표시 중)"
            )

    def get_settings(self) -> Dict[str, object]:
        return {
            "page_stamp_map": {
                k: v for k, v in self._page_states.items() if v in ("당초", "변경")
            },
            "box_width": float(self.spin_box_w.value()),
            "box_height": float(self.spin_box_h.value()),
            "border_color": self._border_color,
            "border_width": float(self.spin_border_w.value()),
            "font_key": str(self.combo_font.currentData() or "malgun"),
            "font_size": float(self.spin_font_size.value()),
            "is_bold": bool(self.chk_bold.isChecked()),
            "top_margin_pt": float(self.spin_top_margin.value()),
            "right_margin_pt": float(self.spin_right_margin.value()),
        }
