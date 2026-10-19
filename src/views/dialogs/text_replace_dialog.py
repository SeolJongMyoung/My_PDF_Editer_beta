from typing import List, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QColorDialog,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
)
from src.models.pdf_handler import TextStyleInfo


class TextEditDialog(QDialog):
    """
    클릭/드래그한 PDF 텍스트의 원본 폰트, 스타일, 크기, 색상 정보를 표시하고
    윈도우 전체 폰트 목록(검색 필터 지원), 크기, 스타일, 글자 색상을 변경하여 적용할 수 있는 다이얼로그
    """

    PRESET_COLORS: List[Tuple[str, str]] = [
        ("검정", "#000000"),
        ("빨강", "#dc2626"),
        ("파랑", "#2563eb"),
        ("초록", "#16a34a"),
        ("주황", "#ea580c"),
    ]

    def __init__(
        self,
        style_info: TextStyleInfo,
        font_choices: List[Tuple[str, str]],
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("텍스트 수정 (폰트 / 크기 / 스타일 / 색상 설정)")
        self.setMinimumWidth(500)

        self.style_info = style_info
        self.all_font_choices: List[Tuple[str, str]] = list(font_choices)

        # 원본 색상 (0.0~1.0 RGB -> QColor)
        self.orig_qcolor = self._rgb_float_to_qcolor(style_info.color)
        self.selected_qcolor = QColor(self.orig_qcolor)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # ---------------------------------------------------------------------
        # 1. 감지된 원본 글씨 정보 표시 박스
        # ---------------------------------------------------------------------
        info_group = QGroupBox("감지된 원본 텍스트 정보")
        info_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #18181b;
            }
            """
        )
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(6)

        orig_text_preview = style_info.text if style_info.text else "(빈 영역)"
        if len(orig_text_preview) > 45:
            orig_text_preview = orig_text_preview[:45] + "..."

        style_tags = []
        if style_info.is_bold:
            style_tags.append("굵게(Bold)")
        if style_info.is_italic:
            style_tags.append("기울임(Italic)")
        if not style_tags:
            style_tags.append("보통(Regular)")
        style_str = ", ".join(style_tags)

        lbl_orig_text = QLabel(orig_text_preview)
        lbl_orig_text.setStyleSheet("color: #18181b; font-weight: 600;")

        lbl_orig_font = QLabel(
            f"{style_info.clean_font_name}  (원본 PDF: {style_info.raw_font_name})"
        )
        lbl_orig_font.setStyleSheet("color: #3f3f46;")

        orig_hex = self.orig_qcolor.name().upper()
        lbl_orig_spec = QLabel(
            f"{style_info.font_size:.1f} pt   |   스타일: {style_str}   |   원본 색상: {orig_hex}"
        )
        lbl_orig_spec.setStyleSheet("color: #18181b; font-weight: 600;")

        info_layout.addRow("선택된 글씨:", lbl_orig_text)
        info_layout.addRow("원본 폰트명:", lbl_orig_font)
        info_layout.addRow("크기/스타일/색상:", lbl_orig_spec)

        main_layout.addWidget(info_group)

        # ---------------------------------------------------------------------
        # 2. 수정할 텍스트 및 폰트/스타일/크기/색상 변경 폼
        # ---------------------------------------------------------------------
        edit_group = QGroupBox(
            f"수정할 내용 및 서식 설정 (윈도우 폰트 {len(self.all_font_choices)}종 사용 가능)"
        )
        edit_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #18181b;
            }
            """
        )
        form_layout = QFormLayout(edit_group)
        form_layout.setSpacing(10)

        # (1) 바꿀 텍스트 입력
        self.text_input = QLineEdit(style_info.text)
        self.text_input.setPlaceholderText("바꿀 새 텍스트 입력 (비워두면 기존 텍스트만 삭제)")
        self.text_input.selectAll()
        form_layout.addRow("바꿀 텍스트:", self.text_input)

        # (2) 윈도우 폰트 빠른 검색 + 폰트 선택 콤보박스
        font_vbox = QVBoxLayout()
        font_vbox.setSpacing(5)

        self.font_search_input = QLineEdit()
        self.font_search_input.setPlaceholderText(
            "폰트 빠른 검색 (예: 굴림, 바탕, 함초롬, 나눔, 서울, Arial...)"
        )
        self.font_search_input.setClearButtonEnabled(True)
        self.font_search_input.textChanged.connect(self._filter_font_combo)

        self.font_combo = QComboBox()
        self.font_combo.setMaxVisibleItems(18)
        self._populate_font_combo(self.all_font_choices, style_info.matched_font_key)

        font_vbox.addWidget(self.font_search_input)
        font_vbox.addWidget(self.font_combo)
        form_layout.addRow("적용할 폰트:", font_vbox)

        # (3) 폰트 크기 스핀박스 (감지된 원본 크기 자동 세팅)
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(4.0, 96.0)
        self.size_spin.setDecimals(1)
        self.size_spin.setSingleStep(0.5)
        self.size_spin.setSuffix(" pt")
        self.size_spin.setValue(style_info.font_size)
        form_layout.addRow("폰트 크기:", self.size_spin)

        # (4) 폰트 스타일 체크박스 (굵게 / 기울임)
        style_box = QHBoxLayout()
        self.bold_check = QCheckBox("굵게 (Bold)")
        self.bold_check.setChecked(style_info.is_bold)
        self.italic_check = QCheckBox("기울임 (Italic)")
        self.italic_check.setChecked(style_info.is_italic)
        style_box.addWidget(self.bold_check)
        style_box.addWidget(self.italic_check)
        style_box.addStretch()
        form_layout.addRow("폰트 스타일:", style_box)

        # (5) 글자 색상 선택 (색상 미리보기 칩 + 색상 선택기 대화상자 + 빠른 색상 버튼)
        color_row = QHBoxLayout()
        color_row.setSpacing(6)

        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(24, 24)

        self.color_hex_label = QLabel()
        self.color_hex_label.setFixedWidth(68)
        self.color_hex_label.setStyleSheet("font-weight: 700; color: #18181b;")

        self.btn_pick_color = QPushButton("색상 선택...")
        self.btn_pick_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick_color.setStyleSheet(
            """
            QPushButton {
                background-color: #f4f4f5;
                color: #18181b;
                border: 1px solid #d4d4d8;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e4e4e7;
            }
            """
        )
        self.btn_pick_color.clicked.connect(self._on_pick_color_clicked)

        color_row.addWidget(self.color_swatch)
        color_row.addWidget(self.color_hex_label)
        color_row.addWidget(self.btn_pick_color)

        for preset_name, hex_code in self.PRESET_COLORS:
            chip_btn = QPushButton(preset_name)
            chip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            chip_btn.setToolTip(f"{preset_name} ({hex_code.upper()}) 적용")
            chip_btn.setFixedHeight(24)
            chip_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: #ffffff;
                    color: {hex_code};
                    border: 1px solid #d4d4d8;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: #f4f4f5;
                    border-color: {hex_code};
                }}
                """
            )
            chip_btn.clicked.connect(
                lambda checked=False, hc=hex_code: self._set_selected_color(QColor(hc))
            )
            color_row.addWidget(chip_btn)

        btn_reset_color = QPushButton("원본색")
        btn_reset_color.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_color.setToolTip("감지된 원본 글자 색상으로 되돌립니다")
        btn_reset_color.setFixedHeight(24)
        btn_reset_color.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #52525b;
                border: 1px solid #d4d4d8;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #f4f4f5;
                color: #18181b;
            }
            """
        )
        btn_reset_color.clicked.connect(
            lambda: self._set_selected_color(QColor(self.orig_qcolor))
        )
        color_row.addWidget(btn_reset_color)
        color_row.addStretch()

        self._update_color_Display()
        form_layout.addRow("글자 색상:", color_row)

        # (6) 수직 위치(Baseline) 미세 보정
        self.y_offset_spin = QDoubleSpinBox()
        self.y_offset_spin.setRange(-20.0, 20.0)
        self.y_offset_spin.setDecimals(1)
        self.y_offset_spin.setSingleStep(0.5)
        self.y_offset_spin.setSuffix(" pt (0 = 원본 줄 맞춤)")
        self.y_offset_spin.setValue(0.0)
        form_layout.addRow("상하 위치 보정:", self.y_offset_spin)

        main_layout.addWidget(edit_group)

        # 확인 / 취소 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("적용")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("취소")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.text_input.setFocus()

    # -------------------------------------------------------------------------
    # 폰트 검색 필터 및 색상 선택 제어
    # -------------------------------------------------------------------------
    def _populate_font_combo(
        self, choices: List[Tuple[str, str]], prefer_key: str
    ):
        self.font_combo.clear()
        selected_idx = 0
        for idx, (f_key, f_label) in enumerate(choices):
            self.font_combo.addItem(f_label, userData=f_key)
            if f_key == prefer_key:
                selected_idx = idx
        if self.font_combo.count() > 0:
            self.font_combo.setCurrentIndex(selected_idx)

    def _filter_font_combo(self, keyword: str):
        current_key = (
            str(self.font_combo.currentData())
            if self.font_combo.currentData()
            else self.style_info.matched_font_key
        )
        kw = keyword.strip().lower()
        if not kw:
            filtered = self.all_font_choices
        else:
            filtered = [
                (k, lbl)
                for k, lbl in self.all_font_choices
                if kw in lbl.lower() or kw in k.lower()
            ]
        if not filtered:
            filtered = self.all_font_choices
        self._populate_font_combo(filtered, current_key)

    def _on_pick_color_clicked(self):
        chosen = QColorDialog.getColor(
            self.selected_qcolor, self, "적용할 글자 색상 선택"
        )
        if chosen.isValid():
            self._set_selected_color(chosen)

    def _set_selected_color(self, qcolor: QColor):
        if qcolor.isValid():
            self.selected_qcolor = QColor(qcolor)
            self._update_color_Display()

    def _update_color_Display(self):
        hex_str = self.selected_qcolor.name().upper()
        self.color_swatch.setStyleSheet(
            f"background-color: {hex_str}; border: 1.5px solid #71717a; border-radius: 4px;"
        )
        self.color_hex_label.setText(hex_str)

    @staticmethod
    def _rgb_float_to_qcolor(rgb: Tuple[float, float, float]) -> QColor:
        r = max(0, min(255, int(round(rgb[0] * 255))))
        g = max(0, min(255, int(round(rgb[1] * 255))))
        b = max(0, min(255, int(round(rgb[2] * 255))))
        return QColor(r, g, b)

    def get_selected_color_rgb(self) -> Tuple[float, float, float]:
        return (
            round(self.selected_qcolor.red() / 255.0, 4),
            round(self.selected_qcolor.green() / 255.0, 4),
            round(self.selected_qcolor.blue() / 255.0, 4),
        )

    def get_edit_values(self):
        """
        (바꿀 텍스트, 선택한 font_key, 폰트 크기, 굵게 여부, 기울임 여부, 글자 색상 RGB 튜플, 수직 오프셋) 반환
        """
        selected_key = self.font_combo.currentData()
        if not selected_key:
            selected_key = self.style_info.matched_font_key
        return (
            self.text_input.text(),
            str(selected_key),
            float(self.size_spin.value()),
            bool(self.bold_check.isChecked()),
            bool(self.italic_check.isChecked()),
            self.get_selected_color_rgb(),
            float(self.y_offset_spin.value()),
        )
