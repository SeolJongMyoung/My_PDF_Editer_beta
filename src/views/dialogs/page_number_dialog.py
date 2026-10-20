from typing import Dict, Optional
import fitz
from PyQt6.QtCore import Qt, QRectF, QPointF
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
    QRadioButton,
    QButtonGroup,
    QSlider,
    QCheckBox,
    QFrame,
    QSplitter,
)
from src.views.dialogs.print_dialog import ModernSpinBox


class PageNumberDialog(QDialog):
    """
    쪽번호 넣기 대화상자 (Ctrl+Shift+N)
    - 형식: '-1-' (기본값), '- 1 -', '1' 지원
    - 쪽번호를 시작할 문서 페이지(1 ~ N) 및 끝 페이지, 시작 번호 지정
    - 하단 위치: 좌측 / 중앙(기본) / 우측 선택
    - 기존 문서 글자와 겹치지 않도록 [▲ 위로] / [▼ 아래로] 버튼 및 슬라이더로 수직 위치 실시간 조정
    - 좌측 미리보기 창에서 실제 페이지 위에 배치될 '-1-' 위치를 실시간으로 확인
    """

    def __init__(
        self,
        doc: fitz.Document,
        current_page_index: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.doc = doc
        self.total_pages = len(doc) if doc is not None else 0
        self.preview_page_index = max(0, min(self.total_pages - 1, current_page_index))

        self.setWindowTitle("쪽번호 넣기")
        self.setMinimumSize(880, 620)
        self.resize(980, 680)

        self._init_ui()
        self._apply_styles()
        self._connect_signals()
        self._update_preview()

    def _init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setObjectName("PageNumSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(5)

        # =====================================================================
        # 1. 좌측 실시간 페이지 미리보기 영역
        # =====================================================================
        left_widget = QFrame(self)
        left_widget.setObjectName("PageNumPreviewPane")
        left_widget.setMinimumWidth(420)
        left_vbox = QVBoxLayout(left_widget)
        left_vbox.setContentsMargins(18, 16, 18, 16)
        left_vbox.setSpacing(10)

        # 상단 미리보기 페이지 이동 바 + [하단부 확대 보기] 체크박스
        nav_bar = QHBoxLayout()
        lbl_prev_title = QLabel("실시간 위치 미리보기")
        lbl_prev_title.setObjectName("PreviewHeaderTitle")

        self.chk_zoom_bottom = QCheckBox("하단 영역 확대 보기")
        self.chk_zoom_bottom.setObjectName("ZoomBottomCheck")
        self.chk_zoom_bottom.setChecked(False)
        self.chk_zoom_bottom.setToolTip(
            "체크하면 페이지 하단 영역을 크게 확대하여 기존 글자와 쪽번호가 겹치는지 정밀하게 확인합니다"
        )

        self.btn_prev_page = QPushButton("◀")
        self.btn_prev_page.setObjectName("PreviewNavBtn")
        self.btn_prev_page.setFixedSize(28, 26)
        self.btn_prev_page.setCursor(Qt.CursorShape.PointingHandCursor)

        self.lbl_preview_page = QLabel("1 / 1 페이지")
        self.lbl_preview_page.setObjectName("PreviewPageLabel")
        self.lbl_preview_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview_page.setMinimumWidth(90)

        self.btn_next_page = QPushButton("▶")
        self.btn_next_page.setObjectName("PreviewNavBtn")
        self.btn_next_page.setFixedSize(28, 26)
        self.btn_next_page.setCursor(Qt.CursorShape.PointingHandCursor)

        nav_bar.addWidget(lbl_prev_title)
        nav_bar.addStretch(1)
        nav_bar.addWidget(self.chk_zoom_bottom)
        nav_bar.addSpacing(8)
        nav_bar.addWidget(self.btn_prev_page)
        nav_bar.addWidget(self.lbl_preview_page)
        nav_bar.addWidget(self.btn_next_page)
        left_vbox.addLayout(nav_bar)

        # 중앙 미리보기 이미지 라벨
        self.preview_canvas = QLabel()
        self.preview_canvas.setObjectName("PageNumPreviewCanvas")
        self.preview_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_vbox.addWidget(self.preview_canvas, stretch=1)

        self.lbl_preview_notice = QLabel("")
        self.lbl_preview_notice.setObjectName("PreviewNoticeLabel")
        self.lbl_preview_notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_vbox.addWidget(self.lbl_preview_notice)

        self.splitter.addWidget(left_widget)

        # =====================================================================
        # 2. 우측 쪽번호 설정 패널
        # =====================================================================
        right_panel = QFrame(self)
        right_panel.setObjectName("PageNumRightPane")
        right_panel.setMinimumWidth(380)

        right_vbox = QVBoxLayout(right_panel)
        right_vbox.setContentsMargins(24, 20, 24, 20)
        right_vbox.setSpacing(16)

        lbl_title = QLabel("쪽번호 넣기 설정")
        lbl_title.setObjectName("RightHeaderTitle")
        right_vbox.addWidget(lbl_title)

        # --- [섹션 1] 쪽번호 형식 및 페이지 범위 ---
        sec1_frame = QFrame()
        sec1_frame.setObjectName("SettingSectionCard")
        sec1_grid = QGridLayout(sec1_frame)
        sec1_grid.setContentsMargins(14, 14, 14, 14)
        sec1_grid.setHorizontalSpacing(12)
        sec1_grid.setVerticalSpacing(12)
        sec1_grid.setColumnMinimumWidth(0, 120)
        sec1_grid.setColumnStretch(1, 1)

        lbl_fmt = QLabel("쪽번호 모양(형식)")
        lbl_fmt.setObjectName("FieldLabel")
        self.cmb_format = QComboBox()
        self.cmb_format.setObjectName("FieldCombo")
        self.cmb_format.setFixedHeight(34)
        self.cmb_format.addItem("-1-  (기본 형식)", "-{n}-")
        self.cmb_format.addItem("- 1 -  (공백 포함)", "- {n} -")
        self.cmb_format.addItem("1  (숫자만)", "{n}")
        sec1_grid.addWidget(lbl_fmt, 0, 0)
        sec1_grid.addWidget(self.cmb_format, 0, 1)

        lbl_start_page = QLabel("쪽번호 시작 페이지")
        lbl_start_page.setObjectName("FieldLabel")
        self.spin_start_page = ModernSpinBox(
            min_val=1,
            max_val=max(1, self.total_pages),
            initial=1,
            suffix=" 페이지부터",
            width=140,
            height=34,
        )
        sec1_grid.addWidget(lbl_start_page, 1, 0)
        sec1_grid.addWidget(
            self.spin_start_page, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft
        )

        lbl_end_page = QLabel("쪽번호 끝 페이지")
        lbl_end_page.setObjectName("FieldLabel")
        self.spin_end_page = ModernSpinBox(
            min_val=1,
            max_val=max(1, self.total_pages),
            initial=max(1, self.total_pages),
            suffix=" 페이지까지",
            width=140,
            height=34,
        )
        sec1_grid.addWidget(lbl_end_page, 2, 0)
        sec1_grid.addWidget(
            self.spin_end_page, 2, 1, alignment=Qt.AlignmentFlag.AlignLeft
        )

        lbl_start_num = QLabel("시작 쪽번호 값")
        lbl_start_num.setObjectName("FieldLabel")
        self.spin_start_num = ModernSpinBox(
            min_val=1,
            max_val=9999,
            initial=1,
            suffix=" 번으로 시작",
            width=140,
            height=34,
        )
        self.spin_start_num.setToolTip(
            "시작 페이지에 매겨질 첫 번째 번호입니다 (예: 2페이지부터 시작하더라도 -1- 로 시작 가능)"
        )
        sec1_grid.addWidget(lbl_start_num, 3, 0)
        sec1_grid.addWidget(
            self.spin_start_num, 3, 1, alignment=Qt.AlignmentFlag.AlignLeft
        )

        right_vbox.addWidget(sec1_frame)

        # --- [섹션 2] 하단 위치 선택 (좌측 / 중앙 / 우측) ---
        sec2_frame = QFrame()
        sec2_frame.setObjectName("SettingSectionCard")
        sec2_vbox = QVBoxLayout(sec2_frame)
        sec2_vbox.setContentsMargins(14, 14, 14, 14)
        sec2_vbox.setSpacing(12)

        lbl_pos_header = QLabel("하단 좌·우 위치 선택")
        lbl_pos_header.setObjectName("SectionSubTitle")
        sec2_vbox.addWidget(lbl_pos_header)

        align_row = QHBoxLayout()
        align_row.setSpacing(10)

        self.align_group = QButtonGroup(self)
        self.rb_left = QRadioButton("하단 좌측")
        self.rb_center = QRadioButton("하단 중앙 (기본)")
        self.rb_right = QRadioButton("하단 우측")
        self.rb_center.setChecked(True)

        for rb in (self.rb_left, self.rb_center, self.rb_right):
            rb.setObjectName("AlignRadioBtn")
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            self.align_group.addButton(rb)
            align_row.addWidget(rb)

        sec2_vbox.addLayout(align_row)

        # 좌/우 여백 조절 (좌측 또는 우측 선택 시 활용)
        h_margin_row = QHBoxLayout()
        lbl_h_margin = QLabel("좌·우 여백 간격:")
        lbl_h_margin.setObjectName("FieldLabel")
        self.spin_h_margin = ModernSpinBox(
            min_val=10,
            max_val=200,
            initial=42,
            suffix=" pt",
            width=105,
            height=32,
        )
        h_margin_row.addWidget(lbl_h_margin)
        h_margin_row.addWidget(self.spin_h_margin)
        h_margin_row.addStretch(1)
        sec2_vbox.addLayout(h_margin_row)

        right_vbox.addWidget(sec2_frame)

        # --- [섹션 3] 위·아래 위치 미세 조정 (겹침 방지) & 글자 크기 ---
        sec3_frame = QFrame()
        sec3_frame.setObjectName("SettingSectionCard")
        sec3_vbox = QVBoxLayout(sec3_frame)
        sec3_vbox.setContentsMargins(14, 14, 14, 14)
        sec3_vbox.setSpacing(10)

        lbl_v_header = QLabel("위·아래 위치 조정 (기존 글자 겹침 방지)")
        lbl_v_header.setObjectName("SectionSubTitle")
        sec3_vbox.addWidget(lbl_v_header)

        lbl_v_desc = QLabel(
            "다른 글자와 겹칠 경우 [▲ 위로] / [▼ 아래로] 버튼이나 슬라이더로 위치를 조정하세요."
        )
        lbl_v_desc.setObjectName("HelpHintLabel")
        lbl_v_desc.setWordWrap(True)
        sec3_vbox.addWidget(lbl_v_desc)

        v_ctrl_row = QHBoxLayout()
        v_ctrl_row.setSpacing(8)

        self.btn_move_up = QPushButton("▲ 위로 이동")
        self.btn_move_up.setObjectName("NudgeActionBtn")
        self.btn_move_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_up.setFixedHeight(32)
        self.btn_move_up.setAutoRepeat(True)
        self.btn_move_up.setToolTip("쪽번호를 위로 올립니다 (하단 여백 증가)")

        self.btn_move_down = QPushButton("▼ 아래로 이동")
        self.btn_move_down.setObjectName("NudgeActionBtn")
        self.btn_move_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_down.setFixedHeight(32)
        self.btn_move_down.setAutoRepeat(True)
        self.btn_move_down.setToolTip("쪽번호를 아래로 내립니다 (하단 여백 감소)")

        self.spin_bottom_offset = ModernSpinBox(
            min_val=6,
            max_val=180,
            initial=28,
            suffix=" pt",
            width=100,
            height=32,
        )
        self.spin_bottom_offset.setToolTip("페이지 하단 끝에서부터 쪽번호까지의 수직 거리(pt)")

        v_ctrl_row.addWidget(self.btn_move_up)
        v_ctrl_row.addWidget(self.btn_move_down)
        v_ctrl_row.addStretch(1)
        v_ctrl_row.addWidget(QLabel("하단 간격:"))
        v_ctrl_row.addWidget(self.spin_bottom_offset)
        sec3_vbox.addLayout(v_ctrl_row)

        self.slider_bottom_offset = QSlider(Qt.Orientation.Horizontal)
        self.slider_bottom_offset.setRange(6, 180)
        self.slider_bottom_offset.setValue(28)
        sec3_vbox.addWidget(self.slider_bottom_offset)

        # 글자 크기 설정
        font_row = QHBoxLayout()
        lbl_fsize = QLabel("쪽번호 글자 크기:")
        lbl_fsize.setObjectName("FieldLabel")
        self.spin_font_size = ModernSpinBox(
            min_val=7,
            max_val=24,
            initial=11,
            suffix=" pt",
            width=100,
            height=32,
        )
        font_row.addWidget(lbl_fsize)
        font_row.addWidget(self.spin_font_size)
        font_row.addStretch(1)
        sec3_vbox.addLayout(font_row)

        right_vbox.addWidget(sec3_frame)
        right_vbox.addStretch(1)

        # --- 하단 실행 / 취소 버튼 ---
        footer_row = QHBoxLayout()
        footer_row.setSpacing(8)
        footer_row.addStretch(1)

        self.btn_apply = QPushButton("쪽번호 넣기")
        self.btn_apply.setObjectName("PrimaryApplyBtn")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setFixedSize(110, 38)
        self.btn_apply.setDefault(True)

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("CancelDialogBtn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedSize(80, 38)

        footer_row.addWidget(self.btn_apply)
        footer_row.addWidget(self.btn_cancel)
        right_vbox.addLayout(footer_row)

        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([540, 440])

        root_layout.addWidget(self.splitter)

    def _connect_signals(self):
        self.btn_prev_page.clicked.connect(self._on_prev_preview_page)
        self.btn_next_page.clicked.connect(self._on_next_preview_page)
        self.chk_zoom_bottom.toggled.connect(self._update_preview)

        self.cmb_format.currentIndexChanged.connect(self._update_preview)
        self.spin_start_page.valueChanged.connect(self._on_start_page_changed)
        self.spin_end_page.valueChanged.connect(self._on_end_page_changed)
        self.spin_start_num.valueChanged.connect(self._update_preview)

        self.align_group.buttonClicked.connect(self._update_preview)
        self.spin_h_margin.valueChanged.connect(self._update_preview)

        self.btn_move_up.clicked.connect(
            lambda: self.spin_bottom_offset.setValue(
                self.spin_bottom_offset.value() + 3
            )
        )
        self.btn_move_down.clicked.connect(
            lambda: self.spin_bottom_offset.setValue(
                self.spin_bottom_offset.value() - 3
            )
        )
        self.spin_bottom_offset.valueChanged.connect(self._on_offset_spin_changed)
        self.slider_bottom_offset.valueChanged.connect(self._on_offset_slider_changed)
        self.spin_font_size.valueChanged.connect(self._update_preview)

        self.btn_apply.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _on_prev_preview_page(self):
        if self.preview_page_index > 0:
            self.preview_page_index -= 1
            self._update_preview()

    def _on_next_preview_page(self):
        if self.preview_page_index < self.total_pages - 1:
            self.preview_page_index += 1
            self._update_preview()

    def _on_start_page_changed(self, val: int):
        if val > self.spin_end_page.value():
            self.spin_end_page.setValue(val)
        # 시작 페이지 변경 시 해당 페이지를 바로 미리보기에 표시
        self.preview_page_index = max(0, min(self.total_pages - 1, val - 1))
        self._update_preview()

    def _on_end_page_changed(self, val: int):
        if val < self.spin_start_page.value():
            self.spin_start_page.setValue(val)
        self._update_preview()

    def _on_offset_spin_changed(self, val: int):
        if self.slider_bottom_offset.value() != val:
            self.slider_bottom_offset.blockSignals(True)
            self.slider_bottom_offset.setValue(val)
            self.slider_bottom_offset.blockSignals(False)
        self._update_preview()

    def _on_offset_slider_changed(self, val: int):
        if self.spin_bottom_offset.value() != val:
            self.spin_bottom_offset.blockSignals(True)
            self.spin_bottom_offset.setValue(val)
            self.spin_bottom_offset.blockSignals(False)
        self._update_preview()

    def get_alignment_value(self) -> str:
        if self.rb_left.isChecked():
            return "left"
        if self.rb_right.isChecked():
            return "right"
        return "center"

    def get_options(self) -> Dict[str, object]:
        return {
            "start_page_index": self.spin_start_page.value() - 1,
            "end_page_index": self.spin_end_page.value() - 1,
            "start_number": self.spin_start_num.value(),
            "alignment": self.get_alignment_value(),
            "bottom_offset_pt": float(self.spin_bottom_offset.value()),
            "horizontal_margin_pt": float(self.spin_h_margin.value()),
            "font_size": float(self.spin_font_size.value()),
            "format_template": str(self.cmb_format.currentData() or "-{n}-"),
        }

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview()

    def _update_preview(self, *_args):
        if self.doc is None or self.total_pages <= 0:
            return

        self.lbl_preview_page.setText(
            f"{self.preview_page_index + 1} / {self.total_pages} 페이지"
        )
        self.btn_prev_page.setEnabled(self.preview_page_index > 0)
        self.btn_next_page.setEnabled(self.preview_page_index < self.total_pages - 1)

        opts = self.get_options()
        s_idx = int(opts["start_page_index"])
        e_idx = int(opts["end_page_index"])
        start_num = int(opts["start_number"])
        alignment = str(opts["alignment"])
        bottom_offset = float(opts["bottom_offset_pt"])
        h_margin = float(opts["horizontal_margin_pt"])
        font_size = float(opts["font_size"])
        fmt_tpl = str(opts["format_template"])

        page = self.doc[self.preview_page_index]
        rect = page.rect

        # 하단 확대 보기 모드이면 페이지 하단 35% 영역만 고배율로 렌더링
        zoom_bottom = self.chk_zoom_bottom.isChecked()
        if zoom_bottom:
            clip_rect = fitz.Rect(
                rect.x0,
                rect.y0 + rect.height * 0.62,
                rect.x1,
                rect.y1,
            )
            scale = 1.65
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip_rect, alpha=False)
            origin_x = clip_rect.x0
            origin_y = clip_rect.y0
        else:
            avail_w = max(320, self.preview_canvas.width() - 24)
            avail_h = max(380, self.preview_canvas.height() - 24)
            scale = min(avail_w / max(1.0, rect.width), avail_h / max(1.0, rect.height))
            scale = max(0.45, min(1.5, scale))
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            origin_x = rect.x0
            origin_y = rect.y0

        qimg = QImage(
            pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
        ).copy()
        canvas_pix = QPixmap.fromImage(qimg)

        in_range = s_idx <= self.preview_page_index <= e_idx
        if in_range:
            num_val = start_num + (self.preview_page_index - s_idx)
            label_text = fmt_tpl.format(n=num_val)
            self.lbl_preview_notice.setText(
                f"현재 페이지({self.preview_page_index + 1}p)에는 '{label_text}' 쪽번호가 삽입됩니다."
            )
            self.lbl_preview_notice.setStyleSheet("color: #1d4ed8; font-weight: 700;")

            text_w_pt = fitz.get_text_length(
                label_text, fontname="helv", fontsize=font_size
            )
            if alignment == "left":
                x_pt = rect.x0 + h_margin
            elif alignment == "right":
                x_pt = rect.x1 - h_margin - text_w_pt
            else:
                x_pt = rect.x0 + (rect.width - text_w_pt) / 2.0

            baseline_y_pt = max(
                rect.y0 + font_size + 4.0,
                min(rect.y1 - 4.0, rect.y1 - bottom_offset),
            )

            px_x = (x_pt - origin_x) * scale
            px_baseline_y = (baseline_y_pt - origin_y) * scale
            px_font_size = max(7.0, font_size * scale)
            px_w = text_w_pt * scale

            painter = QPainter(canvas_pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

            # 쪽번호 위치를 쉽게 식별할 수 있도록 얇은 파란 점선 가이드 박스 표시
            guide_rect = QRectF(
                px_x - 6,
                px_baseline_y - px_font_size - 2,
                px_w + 12,
                px_font_size + 6,
            )
            painter.setPen(QPen(QColor(37, 99, 235, 190), 1.2, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(219, 234, 254, 110)))
            painter.drawRoundedRect(guide_rect, 3.0, 3.0)

            font = QFont("Arial")
            font.setPixelSize(int(round(px_font_size)))
            painter.setFont(font)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(QPointF(px_x, px_baseline_y), label_text)
            painter.end()
        else:
            self.lbl_preview_notice.setText(
                f"현재 페이지({self.preview_page_index + 1}p)는 설정한 시작~끝 페이지 범위 밖이므로 쪽번호가 들어가지 않습니다."
            )
            self.lbl_preview_notice.setStyleSheet("color: #64748b; font-weight: 600;")

        self.preview_canvas.setPixmap(canvas_pix)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #ffffff;
                font-family: "Malgun Gothic", "Segoe UI", sans-serif;
                font-size: 13px;
                color: #18181b;
            }
            QSplitter#PageNumSplitter::handle {
                background-color: #e4e4e7;
                width: 4px;
            }
            QSplitter#PageNumSplitter::handle:hover {
                background-color: #2563eb;
            }
            QFrame#PageNumPreviewPane {
                background-color: #f1f5f9;
            }
            QLabel#PreviewHeaderTitle {
                font-size: 14px;
                font-weight: 700;
                color: #1e293b;
            }
            QLabel#PreviewPageLabel {
                font-size: 12px;
                font-weight: 600;
                color: #334155;
            }
            QPushButton#PreviewNavBtn {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 5px;
                font-weight: 700;
                color: #334155;
            }
            QPushButton#PreviewNavBtn:hover {
                background-color: #e2e8f0;
            }
            QPushButton#PreviewNavBtn:disabled {
                color: #cbd5e1;
                border-color: #e2e8f0;
            }
            QLabel#PageNumPreviewCanvas {
                background-color: #e2e8f0;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px;
            }
            QLabel#PreviewNoticeLabel {
                font-size: 12px;
                padding: 2px;
            }
            QFrame#PageNumRightPane {
                background-color: #ffffff;
            }
            QLabel#RightHeaderTitle {
                font-size: 16px;
                font-weight: 700;
                color: #18181b;
            }
            QFrame#SettingSectionCard {
                background-color: #fafafa;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
            }
            QLabel#SectionSubTitle {
                font-size: 13px;
                font-weight: 700;
                color: #18181b;
            }
            QLabel#FieldLabel {
                font-size: 12.5px;
                color: #27272a;
            }
            QLabel#HelpHintLabel {
                font-size: 11.5px;
                color: #64748b;
            }
            QComboBox#FieldCombo {
                background-color: #ffffff;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12.5px;
            }
            QRadioButton#AlignRadioBtn {
                font-size: 12.5px;
                font-weight: 600;
                color: #27272a;
                spacing: 6px;
            }
            QPushButton#NudgeActionBtn {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#NudgeActionBtn:hover {
                background-color: #eff6ff;
                border-color: #93c5fd;
                color: #1d4ed8;
            }
            QPushButton#NudgeActionBtn:pressed {
                background-color: #dbeafe;
            }
            QFrame#ModernSpinFrame {
                background-color: #ffffff;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
            }
            QLineEdit#ModernSpinEdit {
                background-color: transparent;
                border: none;
                color: #18181b;
                font-size: 12.5px;
            }
            QPushButton#ModernSpinStepBtn {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 3px;
            }
            QPushButton#ModernSpinStepBtn:hover {
                background-color: #e2e8f0;
            }
            QPushButton#PrimaryApplyBtn {
                background-color: #0b57d0;
                color: #ffffff;
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#PrimaryApplyBtn:hover {
                background-color: #0842a0;
            }
            QPushButton#CancelDialogBtn {
                background-color: #ffffff;
                color: #0b57d0;
                border: 1px solid #747775;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#CancelDialogBtn:hover {
                background-color: #f0f4f9;
            }
            """
        )
