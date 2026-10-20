import math
from typing import List, Optional, Set, Tuple
import fitz
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QColor,
    QPen,
    QIcon,
    QPageSize,
    QPageLayout,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QFrame,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo, QPrintDialog


# 용지 크기별 (가로 mm, 세로 mm, QPageSize.PageSizeId) 매핑
PAPER_SPECS = {
    "A4": (210.0, 297.0, QPageSize.PageSizeId.A4),
    "A3": (297.0, 420.0, QPageSize.PageSizeId.A3),
    "B4": (250.0, 353.0, QPageSize.PageSizeId.B4),
    "B5": (176.0, 250.0, QPageSize.PageSizeId.B5),
    "Letter": (215.9, 279.4, QPageSize.PageSizeId.Letter),
    "Legal": (215.9, 355.6, QPageSize.PageSizeId.Legal),
}


def make_printer_icon() -> QIcon:
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.scale(2.0, 2.0)
    pen = QPen(QColor("#5f6368"), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawRect(4, 2, 8, 4)
    p.drawRoundedRect(2, 6, 12, 6, 1.5, 1.5)
    p.fillRect(4, 10, 8, 4, QColor("#ffffff"))
    p.drawRect(4, 10, 8, 4)
    p.end()
    pix.setDevicePixelRatio(2.0)
    return QIcon(pix)


def make_external_dialog_icon() -> QIcon:
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.scale(2.0, 2.0)
    pen = QPen(QColor("#5f6368"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # 사각 창 테두리 + 우상단 화살표 아이콘
    p.drawLine(7, 3, 3, 3)
    p.drawLine(3, 3, 3, 13)
    p.drawLine(3, 13, 13, 13)
    p.drawLine(13, 13, 13, 9)
    p.drawLine(8, 8, 13, 3)
    p.drawLine(9, 3, 13, 3)
    p.drawLine(13, 3, 13, 7)
    p.end()
    pix.setDevicePixelRatio(2.0)
    return QIcon(pix)


def make_spin_arrow_icon(up: bool) -> QIcon:
    pix = QPixmap(20, 12)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.scale(2.0, 2.0)
    pen = QPen(
        QColor("#3c4043"),
        1.4,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    if up:
        p.drawLine(3, 4, 5, 2)
        p.drawLine(5, 2, 7, 4)
    else:
        p.drawLine(3, 2, 5, 4)
        p.drawLine(5, 4, 7, 2)
    p.end()
    pix.setDevicePixelRatio(2.0)
    return QIcon(pix)


class ModernSpinBox(QFrame):
    """
    Windows QSS 적용 시 기본 QSpinBox의 숫자 영역과 상/하 버튼이 겹치는 문제를 방지하기 위해
    좌측 숫자 입력창(QLineEdit)과 우측 수직 상/하 화살표 버튼을 명확히 분리한 커스텀 스핀박스
    """

    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        min_val: int = 1,
        max_val: int = 999,
        initial: int = 1,
        suffix: str = "",
        width: int = 96,
        height: int = 36,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("ModernSpinFrame")
        self._min = min_val
        self._max = max_val
        self._val = initial
        self._suffix = suffix

        self.setFixedSize(width, height)

        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(8, 1, 2, 1)
        h_layout.setSpacing(2)

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("ModernSpinEdit")
        self.line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._sync_text()
        self.line_edit.editingFinished.connect(self._on_text_edited)

        btn_col = QVBoxLayout()
        btn_col.setContentsMargins(0, 1, 1, 1)
        btn_col.setSpacing(1)

        self.btn_up = QPushButton(self)
        self.btn_up.setObjectName("ModernSpinStepBtn")
        self.btn_up.setIcon(make_spin_arrow_icon(True))
        self.btn_up.setIconSize(QSize(10, 6))
        self.btn_up.setFixedSize(22, (height - 6) // 2)
        self.btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_up.setAutoRepeat(True)
        self.btn_up.clicked.connect(self.stepUp)

        self.btn_down = QPushButton(self)
        self.btn_down.setObjectName("ModernSpinStepBtn")
        self.btn_down.setIcon(make_spin_arrow_icon(False))
        self.btn_down.setIconSize(QSize(10, 6))
        self.btn_down.setFixedSize(22, (height - 6) // 2)
        self.btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_down.setAutoRepeat(True)
        self.btn_down.clicked.connect(self.stepDown)

        btn_col.addWidget(self.btn_up)
        btn_col.addWidget(self.btn_down)

        h_layout.addWidget(self.line_edit, stretch=1)
        h_layout.addLayout(btn_col)

    def _sync_text(self):
        self.line_edit.setText(f"{self._val}{self._suffix}")

    def _on_text_edited(self):
        raw = self.line_edit.text().replace(self._suffix, "").strip()
        try:
            num = int(raw)
        except ValueError:
            num = self._val
        self.setValue(num)

    def value(self) -> int:
        return self._val

    def setValue(self, val: int):
        clamped = max(self._min, min(self._max, int(val)))
        changed = clamped != self._val
        self._val = clamped
        self._sync_text()
        if changed:
            self.valueChanged.emit(self._val)

    def setRange(self, min_val: int, max_val: int):
        self._min = min_val
        self._max = max_val
        self.setValue(self._val)

    def setSuffix(self, suffix: str):
        self._suffix = suffix
        self._sync_text()

    def stepUp(self):
        self.setValue(self._val + 1)

    def stepDown(self):
        self.setValue(self._val - 1)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.stepUp()
        elif delta < 0:
            self.stepDown()
        event.accept()


class PreviewScrollArea(QScrollArea):
    """스크롤 및 리사이즈 시 현재 화면에 보이는 시트만 지연 렌더링하도록 알리는 미리보기 스크롤 영역"""

    viewport_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.verticalScrollBar().valueChanged.connect(lambda _: self.viewport_changed.emit())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.viewport_changed.emit()


class PrintDialog(QDialog):
    """
    모던 웹 브라우저(Chrome/Edge) 스타일 실시간 인쇄 미리보기 및 설정 다이얼로그
    - 좌측: 시트당 페이지 수(N-up), 컬러/흑백, 용지 크기, 배율이 실시간 반영되는 가상화 용지 미리보기
    - 우측: 대상 프린터, 페이지 범위, 매수, 컬러, 설정 더보기(용지 크기, 시트당 페이지 수, 품질, 배율, 양면),
            시스템 대화상자 인쇄(Ctrl+Shift+P), [인쇄] / [취소] 버튼
    """

    PREVIEW_MARGIN_TOP = 22
    PREVIEW_MARGIN_BOTTOM = 22
    PREVIEW_SHEET_SPACING = 18

    def __init__(self, doc: fitz.Document, parent=None, open_system_dialog_directly: bool = False):
        super().__init__(parent)
        self.doc = doc
        self.total_doc_pages = len(doc) if doc is not None else 0
        self._open_system_directly = open_system_dialog_directly

        self.setWindowTitle("인쇄")
        self.setMinimumSize(980, 660)
        self.resize(1220, 800)

        self._sheet_groups: List[List[int]] = []
        self._sheet_sizes: List[Tuple[int, int]] = []
        self._sheet_labels: List[QLabel] = []
        self._rendered_sheets: Set[int] = set()
        self._more_expanded: bool = True

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(60)
        self._preview_timer.timeout.connect(self._rebuild_preview_sheets)

        self._init_ui()
        self._apply_styles()
        self._populate_printers()
        self._connect_signals()

        # 초기 미리보기 구성
        self._rebuild_preview_sheets()

    @staticmethod
    def _configure_combo(cmb: QComboBox) -> QComboBox:
        """긴 텍스트(프린터 이름 등)로 인해 오른쪽 패널 밖으로 콤보박스가 잘리는 현상 방지"""
        cmb.setObjectName("PrintCombo")
        cmb.setFixedHeight(36)
        cmb.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        cmb.setMinimumContentsLength(6)
        return cmb

    def _init_ui(self):
        root_h_layout = QHBoxLayout(self)
        root_h_layout.setContentsMargins(0, 0, 0, 0)
        root_h_layout.setSpacing(0)

        # 좌·우 창 크기를 사용자가 마우스 드래그로 자유롭게 조절할 수 있는 QSplitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.main_splitter.setObjectName("PrintMainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(5)

        # =====================================================================
        # 1. 좌측 인쇄 미리보기 영역 (회색 배경 + 시트별 흰색 용지 카드)
        # =====================================================================
        self.preview_scroll = PreviewScrollArea(self)
        self.preview_scroll.setObjectName("PrintPreviewScroll")
        self.preview_scroll.setMinimumWidth(420)
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.preview_container = QWidget()
        self.preview_container.setObjectName("PrintPreviewContainer")
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(
            24, self.PREVIEW_MARGIN_TOP, 24, self.PREVIEW_MARGIN_BOTTOM
        )
        self.preview_layout.setSpacing(self.PREVIEW_SHEET_SPACING)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.preview_scroll.setWidget(self.preview_container)
        self.main_splitter.addWidget(self.preview_scroll)

        # =====================================================================
        # 2. 우측 인쇄 설정 패널 (사용자 좌·우 폭 조절 지원, 기본 폭 430px)
        # =====================================================================
        self.right_panel = QFrame(self)
        self.right_panel.setObjectName("PrintRightPanel")
        self.right_panel.setMinimumWidth(360)

        right_vbox = QVBoxLayout(self.right_panel)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(0)

        # --- [2-1] 상단 헤더: "인쇄" + "용지 N장" ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(22, 18, 22, 14)

        lbl_title = QLabel("인쇄")
        lbl_title.setObjectName("PrintHeaderTitle")

        self.lbl_sheet_summary = QLabel("용지 1장")
        self.lbl_sheet_summary.setObjectName("PrintSheetCountLabel")

        header_layout.addWidget(lbl_title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.lbl_sheet_summary)
        right_vbox.addWidget(header_widget)

        # --- [2-2] 중앙 스크롤 가능 폼 영역 ---
        form_scroll = QScrollArea()
        form_scroll.setObjectName("PrintFormScroll")
        form_scroll.setWidgetResizable(True)
        form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        form_content = QWidget()
        form_content.setObjectName("PrintFormContent")
        form_vbox = QVBoxLayout(form_content)
        form_vbox.setContentsMargins(22, 6, 22, 12)
        form_vbox.setSpacing(14)

        # 기본 설정 그리드 (대상, 페이지, 매수, 컬러)
        basic_grid = QGridLayout()
        basic_grid.setHorizontalSpacing(12)
        basic_grid.setVerticalSpacing(14)
        basic_grid.setColumnMinimumWidth(0, 96)
        basic_grid.setColumnStretch(1, 1)

        # (1) 대상
        lbl_dest = QLabel("대상")
        lbl_dest.setObjectName("PrintFieldLabel")
        self.cmb_printer = self._configure_combo(QComboBox())
        self.cmb_printer.view().setMinimumWidth(320)
        basic_grid.addWidget(lbl_dest, 0, 0)
        basic_grid.addWidget(self.cmb_printer, 0, 1)

        # (2) 페이지
        lbl_pages = QLabel("페이지")
        lbl_pages.setObjectName("PrintFieldLabel")
        self.cmb_pages = self._configure_combo(QComboBox())
        self.cmb_pages.addItems(["전체", "홀수 페이지만", "짝수 페이지만", "맞춤 설정"])
        basic_grid.addWidget(lbl_pages, 1, 0)
        basic_grid.addWidget(self.cmb_pages, 1, 1)

        # 맞춤 페이지 범위 입력창 (맞춤 설정 선택 시에만 표시)
        self.edit_custom_pages = QLineEdit()
        self.edit_custom_pages.setObjectName("PrintLineEdit")
        self.edit_custom_pages.setFixedHeight(34)
        self.edit_custom_pages.setPlaceholderText("예: 1-5, 8, 11-13")
        self.edit_custom_pages.setVisible(False)
        basic_grid.addWidget(self.edit_custom_pages, 2, 1)

        # (3) 매수 (숫자와 상/하 버튼이 겹치지 않는 ModernSpinBox)
        lbl_copies = QLabel("매수")
        lbl_copies.setObjectName("PrintFieldLabel")
        self.spin_copies = ModernSpinBox(
            min_val=1, max_val=999, initial=1, suffix="", width=92, height=36
        )
        basic_grid.addWidget(lbl_copies, 3, 0)
        basic_grid.addWidget(
            self.spin_copies, 3, 1, alignment=Qt.AlignmentFlag.AlignLeft
        )

        # (4) 컬러
        lbl_color = QLabel("컬러")
        lbl_color.setObjectName("PrintFieldLabel")
        self.cmb_color = self._configure_combo(QComboBox())
        self.cmb_color.addItems(["컬러", "흑백"])
        basic_grid.addWidget(lbl_color, 4, 0)
        basic_grid.addWidget(self.cmb_color, 4, 1)

        form_vbox.addLayout(basic_grid)

        # 구분선
        div1 = QFrame()
        div1.setObjectName("PrintHorizontalDivider")
        div1.setFrameShape(QFrame.Shape.HLine)
        form_vbox.addWidget(div1)

        # --- [설정 더보기] 토글 헤더 ---
        self.btn_toggle_more = QPushButton()
        self.btn_toggle_more.setObjectName("MoreSettingsToggleBtn")
        self.btn_toggle_more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_more.setFixedHeight(34)
        toggle_layout = QHBoxLayout(self.btn_toggle_more)
        toggle_layout.setContentsMargins(0, 0, 4, 0)

        lbl_more_title = QLabel("설정 더보기")
        lbl_more_title.setObjectName("MoreSettingsLabel")
        lbl_more_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.lbl_more_chevron = QLabel("︿")
        self.lbl_more_chevron.setObjectName("MoreSettingsChevron")
        self.lbl_more_chevron.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        toggle_layout.addWidget(lbl_more_title)
        toggle_layout.addStretch(1)
        toggle_layout.addWidget(self.lbl_more_chevron)
        form_vbox.addWidget(self.btn_toggle_more)

        # --- [설정 더보기] 내부 컨테이너 ---
        self.more_container = QWidget()
        more_grid = QGridLayout(self.more_container)
        more_grid.setContentsMargins(0, 4, 0, 4)
        more_grid.setHorizontalSpacing(12)
        more_grid.setVerticalSpacing(14)
        more_grid.setColumnMinimumWidth(0, 96)
        more_grid.setColumnStretch(1, 1)

        # (5) 용지 크기
        lbl_paper = QLabel("용지 크기")
        lbl_paper.setObjectName("PrintFieldLabel")
        self.cmb_paper_size = self._configure_combo(QComboBox())
        self.cmb_paper_size.addItems(list(PAPER_SPECS.keys()))
        more_grid.addWidget(lbl_paper, 0, 0)
        more_grid.addWidget(self.cmb_paper_size, 0, 1)

        # (6) 시트당 페이지 수
        lbl_nup = QLabel("시트당 페이지 수")
        lbl_nup.setObjectName("PrintFieldLabel")
        self.cmb_pages_per_sheet = self._configure_combo(QComboBox())
        self.cmb_pages_per_sheet.addItems(["1", "2", "4", "6", "9", "16"])
        more_grid.addWidget(lbl_nup, 1, 0)
        more_grid.addWidget(self.cmb_pages_per_sheet, 1, 1)

        # (7) 품질
        lbl_dpi = QLabel("품질")
        lbl_dpi.setObjectName("PrintFieldLabel")
        self.cmb_dpi = self._configure_combo(QComboBox())
        self.cmb_dpi.addItems(["300dpi", "600dpi", "1200dpi"])
        self.cmb_dpi.setCurrentText("600dpi")
        more_grid.addWidget(lbl_dpi, 2, 0)
        more_grid.addWidget(self.cmb_dpi, 2, 1)

        # (8) 배율
        lbl_scale = QLabel("배율")
        lbl_scale.setObjectName("PrintFieldLabel")
        self.cmb_scale = self._configure_combo(QComboBox())
        self.cmb_scale.addItems(["기본값", "용지에 맞춤", "맞춤 설정"])
        more_grid.addWidget(lbl_scale, 3, 0)
        more_grid.addWidget(self.cmb_scale, 3, 1)

        self.spin_custom_scale = ModernSpinBox(
            min_val=10, max_val=200, initial=100, suffix="%", width=102, height=36
        )
        self.spin_custom_scale.setVisible(False)
        more_grid.addWidget(
            self.spin_custom_scale, 4, 1, alignment=Qt.AlignmentFlag.AlignLeft
        )

        # (9) 양면
        lbl_duplex = QLabel("양면")
        lbl_duplex.setObjectName("PrintFieldLabel")
        self.chk_duplex = QCheckBox("양면에 인쇄")
        self.chk_duplex.setObjectName("PrintCheckBox")
        more_grid.addWidget(lbl_duplex, 5, 0)
        more_grid.addWidget(self.chk_duplex, 5, 1)

        form_vbox.addWidget(self.more_container)

        # 구분선
        div2 = QFrame()
        div2.setObjectName("PrintHorizontalDivider")
        div2.setFrameShape(QFrame.Shape.HLine)
        form_vbox.addWidget(div2)

        # --- 시스템 대화상자를 사용하여 인쇄... (Ctrl+Shift+P) ---
        self.btn_system_dialog = QPushButton()
        self.btn_system_dialog.setObjectName("SystemDialogLinkBtn")
        self.btn_system_dialog.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_system_dialog.setFixedHeight(38)
        sys_btn_layout = QHBoxLayout(self.btn_system_dialog)
        sys_btn_layout.setContentsMargins(0, 0, 4, 0)

        lbl_sys_text = QLabel("시스템 대화상자를 사용하여 인쇄... (Ctrl+Shift+P)")
        lbl_sys_text.setObjectName("SystemDialogLinkText")
        lbl_sys_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        lbl_sys_icon = QLabel()
        lbl_sys_icon.setPixmap(make_external_dialog_icon().pixmap(16, 16))
        lbl_sys_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        sys_btn_layout.addWidget(lbl_sys_text)
        sys_btn_layout.addStretch(1)
        sys_btn_layout.addWidget(lbl_sys_icon)
        form_vbox.addWidget(self.btn_system_dialog)

        form_vbox.addStretch(1)
        form_scroll.setWidget(form_content)
        right_vbox.addWidget(form_scroll, stretch=1)

        # --- [2-3] 하단 버튼 영역: [인쇄] [취소] ---
        footer_widget = QWidget()
        footer_widget.setObjectName("PrintFooterBar")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(22, 14, 22, 18)
        footer_layout.setSpacing(8)
        footer_layout.addStretch(1)

        self.btn_print = QPushButton("인쇄")
        self.btn_print.setObjectName("PrimaryPrintBtn")
        self.btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_print.setFixedSize(76, 36)
        self.btn_print.setDefault(True)

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("CancelPrintBtn")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedSize(76, 36)

        footer_layout.addWidget(self.btn_print)
        footer_layout.addWidget(self.btn_cancel)
        right_vbox.addWidget(footer_widget)

        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 0)
        self.main_splitter.setSizes([790, 430])

        root_h_layout.addWidget(self.main_splitter)

        # 단축키 Ctrl+Shift+P 연결
        self.sc_sys_print = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.sc_sys_print.activated.connect(self.open_system_print_dialog)

    def _populate_printers(self):
        printer_icon = make_printer_icon()
        printers = QPrinterInfo.availablePrinterNames()
        default_name = QPrinterInfo.defaultPrinterName()

        # 기본 프린터가 있으면 맨 앞에 오도록 정렬
        ordered = []
        if default_name and default_name in printers:
            ordered.append(default_name)
        for p in printers:
            if p not in ordered:
                ordered.append(p)

        for p_name in ordered:
            self.cmb_printer.addItem(printer_icon, p_name)

        self.cmb_printer.addItem(printer_icon, "PDF로 저장")
        self.cmb_printer.setToolTip(self.cmb_printer.currentText())

    def _connect_signals(self):
        self.preview_scroll.viewport_changed.connect(self._refresh_visible_sheets)
        self.main_splitter.splitterMoved.connect(self._schedule_preview_update)
        self.cmb_printer.currentTextChanged.connect(self.cmb_printer.setToolTip)

        self.cmb_pages.currentTextChanged.connect(self._on_pages_mode_changed)
        self.edit_custom_pages.textChanged.connect(self._schedule_preview_update)
        self.spin_copies.valueChanged.connect(self._update_sheet_count_label)
        self.cmb_color.currentTextChanged.connect(self._schedule_preview_update)
        self.cmb_paper_size.currentTextChanged.connect(self._schedule_preview_update)
        self.cmb_pages_per_sheet.currentTextChanged.connect(self._schedule_preview_update)
        self.cmb_scale.currentTextChanged.connect(self._on_scale_mode_changed)
        self.spin_custom_scale.valueChanged.connect(self._schedule_preview_update)
        self.chk_duplex.toggled.connect(self._update_sheet_count_label)

        self.btn_toggle_more.clicked.connect(self._toggle_more_settings)
        self.btn_system_dialog.clicked.connect(self.open_system_print_dialog)
        self.btn_print.clicked.connect(self.execute_print)
        self.btn_cancel.clicked.connect(self.reject)

    def _toggle_more_settings(self):
        self._more_expanded = not self._more_expanded
        self.more_container.setVisible(self._more_expanded)
        self.lbl_more_chevron.setText("︿" if self._more_expanded else "﹀")

    def _on_pages_mode_changed(self, text: str):
        is_custom = text == "맞춤 설정"
        self.edit_custom_pages.setVisible(is_custom)
        if is_custom and not self.edit_custom_pages.text().strip():
            self.edit_custom_pages.setText(f"1-{self.total_doc_pages}" if self.total_doc_pages > 1 else "1")
        self._schedule_preview_update()

    def _on_scale_mode_changed(self, text: str):
        self.spin_custom_scale.setVisible(text == "맞춤 설정")
        self._schedule_preview_update()

    def _schedule_preview_update(self, *_args):
        pages = self.get_target_page_indices()
        nup = int(self.cmb_pages_per_sheet.currentText() or "1")
        self._sheet_groups = [
            pages[i : i + nup] for i in range(0, len(pages), nup)
        ]
        self._update_sheet_count_label()
        self._preview_timer.start()

    # =========================================================================
    # 페이지 범위 파싱 및 시트(용지) 그룹화·장수 계산
    # =========================================================================
    def get_target_page_indices(self) -> List[int]:
        if self.total_doc_pages <= 0:
            return []

        mode = self.cmb_pages.currentText()
        if mode == "전체":
            return list(range(self.total_doc_pages))
        if mode == "홀수 페이지만":
            return [i for i in range(self.total_doc_pages) if (i + 1) % 2 == 1]
        if mode == "짝수 페이지만":
            return [i for i in range(self.total_doc_pages) if (i + 1) % 2 == 0]

        # 맞춤 설정 파싱 (예: "1-5, 8, 11-13")
        raw = self.edit_custom_pages.text().strip()
        if not raw:
            return list(range(self.total_doc_pages))

        result: List[int] = []
        seen = set()
        for part in raw.split(","):
            token = part.strip()
            if not token:
                continue
            if "-" in token:
                bounds = token.split("-", 1)
                try:
                    start_p = int(bounds[0].strip()) if bounds[0].strip() else 1
                    end_p = (
                        int(bounds[1].strip())
                        if bounds[1].strip()
                        else self.total_doc_pages
                    )
                    if start_p > end_p:
                        start_p, end_p = end_p, start_p
                    for p in range(max(1, start_p), min(self.total_doc_pages, end_p) + 1):
                        idx = p - 1
                        if idx not in seen:
                            seen.add(idx)
                            result.append(idx)
                except ValueError:
                    continue
            else:
                try:
                    p = int(token)
                    if 1 <= p <= self.total_doc_pages:
                        idx = p - 1
                        if idx not in seen:
                            seen.add(idx)
                            result.append(idx)
                except ValueError:
                    continue

        return result if result else list(range(self.total_doc_pages))

    @staticmethod
    def get_nup_grid(pages_per_sheet: int, first_page_landscape: bool) -> Tuple[int, int, bool]:
        """
        시트당 페이지 수(N-up)에 따른 (열 수, 행 수, 시트 가로방향 여부)를 반환합니다.
        - 1p/시트: 원본 페이지 방향 유지 (1x1)
        - 2p/시트: 가로(Landscape) 용지에 좌·우 2열 배치 (2x1) -> 첨부 이미지와 동일한 방식
        - 4p/시트: 세로(Portrait) 용지에 2x2 배치
        - 6p/시트: 가로(Landscape) 용지에 3x2 배치
        - 9p/시트: 세로(Portrait) 용지에 3x3 배치
        - 16p/시트: 세로(Portrait) 용지에 4x4 배치
        """
        if pages_per_sheet == 2:
            return (2, 1, True)
        if pages_per_sheet == 4:
            return (2, 2, False)
        if pages_per_sheet == 6:
            return (3, 2, True)
        if pages_per_sheet == 9:
            return (3, 3, False)
        if pages_per_sheet == 16:
            return (4, 4, False)
        return (1, 1, first_page_landscape)

    def _update_sheet_count_label(self):
        printed_sides = len(self._sheet_groups)
        if self.chk_duplex.isChecked():
            sheets_per_copy = math.ceil(printed_sides / 2.0)
        else:
            sheets_per_copy = printed_sides
        total_sheets = max(0, sheets_per_copy * self.spin_copies.value())
        self.lbl_sheet_summary.setText(f"용지 {total_sheets}장")
        self.btn_print.setEnabled(total_sheets > 0)

    # =========================================================================
    # 좌측 미리보기 시트 구성 및 가상화(Lazy) 렌더링
    # =========================================================================
    def _rebuild_preview_sheets(self):
        pages = self.get_target_page_indices()
        nup = int(self.cmb_pages_per_sheet.currentText() or "1")
        paper_name = self.cmb_paper_size.currentText() or "A4"
        paper_w_mm, paper_h_mm, _ = PAPER_SPECS.get(paper_name, PAPER_SPECS["A4"])

        self._sheet_groups = [
            pages[i : i + nup] for i in range(0, len(pages), nup)
        ]
        self._rendered_sheets.clear()

        # 미리보기 화면 기준 용지 크기 계산 (가로 폭 약 680px 기준 비율 유지)
        preview_base_w = max(520, min(720, self.preview_scroll.viewport().width() - 56))
        self._sheet_sizes = []

        for grp in self._sheet_groups:
            first_rect = self.doc[grp[0]].rect if (self.doc and grp) else fitz.Rect(0, 0, 595, 842)
            first_is_land = first_rect.width > first_rect.height
            _cols, _rows, sheet_is_land = self.get_nup_grid(nup, first_is_land)

            if sheet_is_land:
                aspect = max(paper_w_mm, paper_h_mm) / min(paper_w_mm, paper_h_mm)
                sw = preview_base_w
                sh = int(round(sw / aspect))
            else:
                aspect = min(paper_w_mm, paper_h_mm) / max(paper_w_mm, paper_h_mm)
                sw = int(round(preview_base_w * 0.82))
                sh = int(round(sw / aspect))
            self._sheet_sizes.append((sw, sh))

        # 시트 라벨 슬롯 준비
        while len(self._sheet_labels) < len(self._sheet_groups):
            lbl = QLabel()
            lbl.setObjectName("PreviewSheetCard")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sheet_labels.append(lbl)
            self.preview_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        for idx, lbl in enumerate(self._sheet_labels):
            if idx < len(self._sheet_groups):
                sw, sh = self._sheet_sizes[idx]
                lbl.clear()
                lbl.setText(f"용지 {idx + 1}")
                lbl.setFixedSize(sw, sh)
                lbl.setVisible(True)
            else:
                lbl.clear()
                lbl.setVisible(False)

        total_h = (
            self.PREVIEW_MARGIN_TOP
            + self.PREVIEW_MARGIN_BOTTOM
            + sum(sh for _, sh in self._sheet_sizes)
            + max(0, len(self._sheet_sizes) - 1) * self.PREVIEW_SHEET_SPACING
        )
        max_w = max((sw for sw, _ in self._sheet_sizes), default=560) + 48
        self.preview_container.setMinimumSize(max_w, total_h)
        self.preview_layout.activate()
        self.preview_container.adjustSize()

        self._update_sheet_count_label()
        self._refresh_visible_sheets()

    def _refresh_visible_sheets(self):
        if not self._sheet_groups:
            return

        vbar = self.preview_scroll.verticalScrollBar()
        view_top = vbar.value()
        viewport_h = max(1, self.preview_scroll.viewport().height())
        view_bottom = view_top + viewport_h
        buffer_px = max(450, int(viewport_h * 0.8))

        render_top = view_top - buffer_px
        render_bottom = view_bottom + buffer_px

        visible_sheets: Set[int] = set()
        y_cursor = self.PREVIEW_MARGIN_TOP
        for idx, (_sw, sh) in enumerate(self._sheet_sizes):
            s_top = y_cursor
            s_bottom = s_top + sh
            y_cursor = s_bottom + self.PREVIEW_SHEET_SPACING
            if s_bottom >= render_top and s_top <= render_bottom:
                visible_sheets.add(idx)

        # 화면 밖 시트 메모리 해제
        for r_idx in list(self._rendered_sheets):
            if r_idx not in visible_sheets and 0 <= r_idx < len(self._sheet_labels):
                self._sheet_labels[r_idx].clear()
                self._sheet_labels[r_idx].setText(f"용지 {r_idx + 1}")
                self._rendered_sheets.discard(r_idx)

        # 화면 안 시트 렌더링
        for v_idx in sorted(visible_sheets):
            if v_idx not in self._rendered_sheets:
                sw, sh = self._sheet_sizes[v_idx]
                sheet_img = self.render_sheet_qimage(v_idx, sw, sh, dpr=1.5)
                if sheet_img is not None:
                    pix = QPixmap.fromImage(sheet_img)
                    pix.setDevicePixelRatio(1.5)
                    self._sheet_labels[v_idx].setText("")
                    self._sheet_labels[v_idx].setPixmap(pix)
                    self._rendered_sheets.add(v_idx)

    def render_sheet_qimage(
        self, sheet_index: int, target_w: int, target_h: int, dpr: float = 1.0
    ) -> Optional[QImage]:
        """
        단일 시트(용지 1면)를 지정된 픽셀 해상도(target_w * dpr, target_h * dpr)로 합성하여 반환합니다.
        미리보기와 실제 프린터 출력이 동일한 렌더링 로직을 공유합니다.
        """
        if self.doc is None or not (0 <= sheet_index < len(self._sheet_groups)):
            return None

        page_indices = self._sheet_groups[sheet_index]
        if not page_indices:
            return None

        nup = int(self.cmb_pages_per_sheet.currentText() or "1")
        is_grayscale = self.cmb_color.currentText() == "흑백"
        scale_mode = self.cmb_scale.currentText()
        custom_scale = (
            self.spin_custom_scale.value() / 100.0
            if scale_mode == "맞춤 설정"
            else 1.0
        )

        first_rect = self.doc[page_indices[0]].rect
        cols, rows, _is_land = self.get_nup_grid(
            nup, first_rect.width > first_rect.height
        )

        px_w = max(1, int(round(target_w * dpr)))
        px_h = max(1, int(round(target_h * dpr)))

        canvas = QImage(px_w, px_h, QImage.Format.Format_RGB888)
        canvas.fill(QColor("#ffffff"))

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # 여백 비율 설정 ("용지에 맞춤"이면 여백 최소화, "기본값"이면 적정 여백)
        margin_ratio = 0.015 if scale_mode == "용지에 맞춤" else 0.035
        pad_x = int(px_w * margin_ratio)
        pad_y = int(px_h * margin_ratio)

        usable_w = max(1, px_w - pad_x * 2)
        usable_h = max(1, px_h - pad_y * 2)
        cell_w = usable_w / cols
        cell_h = usable_h / rows

        colorspace = fitz.csGRAY if is_grayscale else fitz.csRGB

        for slot_i, page_idx in enumerate(page_indices):
            if not (0 <= page_idx < len(self.doc)):
                continue
            r = slot_i // cols
            c = slot_i % cols

            cell_x = pad_x + c * cell_w
            cell_y = pad_y + r * cell_h
            inner_pad = min(cell_w, cell_h) * (0.02 if nup > 1 else 0.0)
            box_w = max(1.0, cell_w - inner_pad * 2)
            box_h = max(1.0, cell_h - inner_pad * 2)

            page = self.doc[page_idx]
            p_rect = page.rect
            fit_zoom = min(box_w / max(1.0, p_rect.width), box_h / max(1.0, p_rect.height))
            final_zoom = max(0.05, min(8.0, fit_zoom * custom_scale))

            pix = page.get_pixmap(
                matrix=fitz.Matrix(final_zoom, final_zoom),
                colorspace=colorspace,
                alpha=False,
            )
            fmt = (
                QImage.Format.Format_Grayscale8
                if is_grayscale
                else QImage.Format.Format_RGB888
            )
            page_qimg = QImage(
                pix.samples, pix.width, pix.height, pix.stride, fmt
            ).copy()

            draw_x = int(round(cell_x + inner_pad + (box_w - pix.width) / 2.0))
            draw_y = int(round(cell_y + inner_pad + (box_h - pix.height) / 2.0))
            painter.drawImage(draw_x, draw_y, page_qimg)

        painter.end()
        return canvas

    # =========================================================================
    # 실제 인쇄 실행 및 시스템 대화상자 인쇄 (Ctrl+Shift+P)
    # =========================================================================
    def _configure_printer(self, printer: QPrinter):
        target_name = self.cmb_printer.currentText()
        if target_name and target_name != "PDF로 저장":
            printer.setPrinterName(target_name)

        dpi_text = self.cmb_dpi.currentText().replace("dpi", "").strip()
        try:
            printer.setResolution(int(dpi_text))
        except ValueError:
            printer.setResolution(600)

        printer.setCopyCount(self.spin_copies.value())
        is_gray = self.cmb_color.currentText() == "흑백"
        printer.setColorMode(
            QPrinter.ColorMode.GrayScale if is_gray else QPrinter.ColorMode.Color
        )

        paper_name = self.cmb_paper_size.currentText() or "A4"
        _, _, page_size_id = PAPER_SPECS.get(paper_name, PAPER_SPECS["A4"])
        printer.setPageSize(QPageSize(page_size_id))

        if self.chk_duplex.isChecked():
            printer.setDuplex(QPrinter.DuplexMode.DuplexAuto)
        else:
            printer.setDuplex(QPrinter.DuplexMode.DuplexNone)

    def _spool_sheets_to_printer(self, printer: QPrinter) -> bool:
        if not self._sheet_groups:
            return False

        nup = int(self.cmb_pages_per_sheet.currentText() or "1")
        painter = QPainter()

        for s_idx, grp in enumerate(self._sheet_groups):
            first_rect = self.doc[grp[0]].rect
            _cols, _rows, sheet_is_land = self.get_nup_grid(
                nup, first_rect.width > first_rect.height
            )
            printer.setPageOrientation(
                QPageLayout.Orientation.Landscape
                if sheet_is_land
                else QPageLayout.Orientation.Portrait
            )

            if s_idx == 0:
                if not painter.begin(printer):
                    return False
            else:
                printer.newPage()

            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            pw = max(1, int(page_rect.width()))
            ph = max(1, int(page_rect.height()))

            sheet_img = self.render_sheet_qimage(s_idx, pw, ph, dpr=1.0)
            if sheet_img is not None:
                painter.drawImage(0, 0, sheet_img)

        painter.end()
        return True

    def execute_print(self):
        if self._preview_timer.isActive():
            self._preview_timer.stop()
            self._rebuild_preview_sheets()
        if not self._sheet_groups:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self._configure_printer(printer)

        if self.cmb_printer.currentText() == "PDF로 저장":
            save_path, _ = QFileDialog.getSaveFileName(
                self, "인쇄 결과를 PDF로 저장", "printed_output.pdf", "PDF Files (*.pdf)"
            )
            if not save_path:
                return
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(save_path)
        else:
            printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            ok = self._spool_sheets_to_printer(printer)
        finally:
            QApplication.restoreOverrideCursor()

        if ok:
            self.accept()
        else:
            QMessageBox.critical(
                self, "인쇄 오류", "프린터로 문서를 전송하는 중 오류가 발생했습니다."
            )

    def open_system_print_dialog(self):
        """[시스템 대화상자를 사용하여 인쇄... (Ctrl+Shift+P)]"""
        if self._preview_timer.isActive():
            self._preview_timer.stop()
            self._rebuild_preview_sheets()
        if not self._sheet_groups:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self._configure_printer(printer)

        sys_dlg = QPrintDialog(printer, self)
        sys_dlg.setWindowTitle("인쇄")
        if sys_dlg.exec() == QDialog.DialogCode.Accepted:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                ok = self._spool_sheets_to_printer(printer)
            finally:
                QApplication.restoreOverrideCursor()
            if ok:
                self.accept()

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #ffffff;
                font-family: "Malgun Gothic", "Segoe UI", sans-serif;
                font-size: 13px;
                color: #202124;
            }
            /* 좌·우 크기 조절 스플리터 핸들 */
            QSplitter#PrintMainSplitter::handle {
                background-color: #dadce0;
                width: 4px;
            }
            QSplitter#PrintMainSplitter::handle:hover {
                background-color: #1a73e8;
            }

            /* 좌측 미리보기 배경 */
            QScrollArea#PrintPreviewScroll {
                background-color: #e8eaed;
                border: none;
            }
            QWidget#PrintPreviewContainer {
                background-color: #e8eaed;
            }
            QLabel#PreviewSheetCard {
                background-color: #ffffff;
                border: 1px solid #c4c7c5;
                color: #5f6368;
                font-size: 13px;
            }

            /* 우측 설정 패널 */
            QFrame#PrintRightPanel {
                background-color: #ffffff;
            }
            QLabel#PrintHeaderTitle {
                font-size: 16px;
                font-weight: 700;
                color: #202124;
            }
            QLabel#PrintSheetCountLabel {
                font-size: 13px;
                font-weight: 600;
                color: #3c4043;
            }
            QScrollArea#PrintFormScroll {
                background-color: #ffffff;
                border: none;
            }
            QWidget#PrintFormContent {
                background-color: #ffffff;
            }
            QLabel#PrintFieldLabel {
                font-size: 13px;
                color: #202124;
            }

            /* 입력 컨트롤 (콤보박스, 텍스트박스) */
            QComboBox#PrintCombo, QLineEdit#PrintLineEdit {
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QComboBox#PrintCombo:hover, QLineEdit#PrintLineEdit:hover {
                border-color: #bdc1c6;
            }
            QComboBox#PrintCombo:focus, QLineEdit#PrintLineEdit:focus {
                border: 1.5px solid #1a73e8;
            }
            QComboBox#PrintCombo::drop-down {
                border: none;
                width: 24px;
            }

            /* 매수 / 맞춤 배율 커스텀 스핀박스 (숫자와 상·하 버튼 정렬 보장) */
            QFrame#ModernSpinFrame {
                background-color: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 6px;
            }
            QFrame#ModernSpinFrame:hover {
                border-color: #bdc1c6;
            }
            QLineEdit#ModernSpinEdit {
                background-color: transparent;
                border: none;
                color: #202124;
                font-size: 13px;
                padding: 0px 2px;
            }
            QPushButton#ModernSpinStepBtn {
                background-color: #f8f9fa;
                border: 1px solid #e8eaed;
                border-radius: 3px;
                padding: 0px;
            }
            QPushButton#ModernSpinStepBtn:hover {
                background-color: #e8eaed;
                border-color: #dadce0;
            }
            QPushButton#ModernSpinStepBtn:pressed {
                background-color: #dadce0;
            }
            QCheckBox#PrintCheckBox {
                font-size: 13px;
                color: #202124;
                spacing: 8px;
            }

            /* 구분선 */
            QFrame#PrintHorizontalDivider {
                background-color: #e8eaed;
                max-height: 1px;
                min-height: 1px;
                border: none;
                margin: 2px 0px;
            }

            /* 설정 더보기 & 시스템 대화상자 링크 버튼 */
            QPushButton#MoreSettingsToggleBtn, QPushButton#SystemDialogLinkBtn {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                text-align: left;
            }
            QPushButton#MoreSettingsToggleBtn:hover, QPushButton#SystemDialogLinkBtn:hover {
                background-color: #f8f9fa;
            }
            QLabel#MoreSettingsLabel {
                font-size: 13px;
                font-weight: 600;
                color: #202124;
            }
            QLabel#MoreSettingsChevron {
                font-size: 13px;
                font-weight: 700;
                color: #5f6368;
            }
            QLabel#SystemDialogLinkText {
                font-size: 12.5px;
                color: #202124;
            }

            /* 하단 인쇄 / 취소 버튼 */
            QWidget#PrintFooterBar {
                background-color: #ffffff;
                border-top: 1px solid #f1f3f4;
            }
            QPushButton#PrimaryPrintBtn {
                background-color: #0b57d0;
                color: #ffffff;
                border: none;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#PrimaryPrintBtn:hover {
                background-color: #0842a0;
            }
            QPushButton#PrimaryPrintBtn:disabled {
                background-color: #e8eaed;
                color: #9aa0a6;
            }
            QPushButton#CancelPrintBtn {
                background-color: #ffffff;
                color: #0b57d0;
                border: 1px solid #747775;
                border-radius: 18px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#CancelPrintBtn:hover {
                background-color: #f0f4f9;
            }
            """
        )
