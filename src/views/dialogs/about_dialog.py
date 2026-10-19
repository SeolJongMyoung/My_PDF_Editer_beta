import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QWidget,
)

from src.__version__ import (
    APP_NAME,
    APP_VERSION,
    BUILD_DATE,
    APP_DESCRIPTION,
    RELEASE_NOTES,
)
from src.utils.resource_path import get_resource_path


class AboutDialog(QDialog):
    """
    도움말/정보(About) 팝업 다이얼로그.
    src/__version__.py에 정의된 앱 이름, 현재 시맨틱 버전, 빌드 일자,
    그리고 버전별 주요 변경 이력(Change Log)을 깔끔한 모던 그레이스케일 UI로 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} 정보 ({APP_VERSION})")
        self.setMinimumSize(540, 480)
        self.resize(560, 520)

        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(14)

        # -----------------------------------------------------------------
        # 1. 상단 앱 헤더 카드 (아이콘 + 프로그램 이름 + 버전 배지 + 빌드 일자)
        # -----------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("AboutHeaderCard")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = get_resource_path("My_pdf_editer_icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                icon_label.setPixmap(
                    pix.scaled(
                        52,
                        52,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        header_layout.addWidget(icon_label)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(4)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        lbl_app_name = QLabel(APP_NAME)
        lbl_app_name.setObjectName("AboutAppName")

        lbl_ver_badge = QLabel(APP_VERSION)
        lbl_ver_badge.setObjectName("AboutVersionBadge")

        name_row.addWidget(lbl_app_name)
        name_row.addWidget(lbl_ver_badge)
        name_row.addStretch(1)

        lbl_desc = QLabel(APP_DESCRIPTION)
        lbl_desc.setObjectName("AboutDescription")

        lbl_build = QLabel(f"빌드 일자: {BUILD_DATE}   |   Semantic Versioning 적용")
        lbl_build.setObjectName("AboutBuildDate")

        title_vbox.addLayout(name_row)
        title_vbox.addWidget(lbl_desc)
        title_vbox.addWidget(lbl_build)
        header_layout.addLayout(title_vbox, stretch=1)

        root_layout.addWidget(header_frame)

        # -----------------------------------------------------------------
        # 2. 주요 변경 이력 (Change Log / Release Notes) 스크롤 영역
        # -----------------------------------------------------------------
        lbl_changelog_title = QLabel("버전별 주요 변경 이력 (Change Log)")
        lbl_changelog_title.setObjectName("ChangelogSectionTitle")
        root_layout.addWidget(lbl_changelog_title)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("ChangelogScroll")
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_content.setObjectName("ChangelogContent")
        notes_layout = QVBoxLayout(scroll_content)
        notes_layout.setContentsMargins(12, 12, 12, 12)
        notes_layout.setSpacing(12)

        for idx, note in enumerate(RELEASE_NOTES):
            ver_str = str(note.get("version", ""))
            date_str = str(note.get("date", ""))
            summary_str = str(note.get("summary", ""))
            changes_list = note.get("changes", [])

            card = QFrame()
            card.setObjectName("ReleaseNoteCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)

            top_row = QHBoxLayout()
            ver_lbl = QLabel(f"{ver_str}  —  {summary_str}")
            ver_lbl.setObjectName(
                "LatestReleaseTitle" if idx == 0 else "PastReleaseTitle"
            )
            date_lbl = QLabel(date_str)
            date_lbl.setObjectName("ReleaseDateLabel")

            top_row.addWidget(ver_lbl)
            top_row.addStretch(1)
            top_row.addWidget(date_lbl)
            card_layout.addLayout(top_row)

            if isinstance(changes_list, list):
                bullet_lines = "\n".join(f"• {item}" for item in changes_list)
                changes_lbl = QLabel(bullet_lines)
                changes_lbl.setObjectName("ReleaseChangesText")
                changes_lbl.setWordWrap(True)
                card_layout.addWidget(changes_lbl)

            notes_layout.addWidget(card)

        notes_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        root_layout.addWidget(scroll_area, stretch=1)

        # -----------------------------------------------------------------
        # 3. 하단 [확인] 버튼
        # -----------------------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.btn_close = QPushButton("확인")
        self.btn_close.setObjectName("PrimaryCloseBtn")
        self.btn_close.setFixedWidth(96)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_close)
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
            QFrame#AboutHeaderCard {
                background-color: #fafafa;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
            }
            QLabel#AboutAppName {
                font-size: 18px;
                font-weight: 800;
                color: #18181b;
            }
            QLabel#AboutVersionBadge {
                background-color: #18181b;
                color: #ffffff;
                font-size: 11px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 5px;
            }
            QLabel#AboutDescription {
                font-size: 12px;
                color: #3f3f46;
                font-weight: 600;
            }
            QLabel#AboutBuildDate {
                font-size: 11px;
                color: #71717a;
            }
            QLabel#ChangelogSectionTitle {
                font-size: 13px;
                font-weight: 700;
                color: #27272a;
                padding-left: 2px;
            }
            QScrollArea#ChangelogScroll {
                background-color: #fafafa;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
            }
            QWidget#ChangelogContent {
                background-color: #fafafa;
            }
            QFrame#ReleaseNoteCard {
                background-color: #ffffff;
                border: 1px solid #e4e4e7;
                border-radius: 7px;
            }
            QLabel#LatestReleaseTitle {
                font-size: 13px;
                font-weight: 800;
                color: #18181b;
            }
            QLabel#PastReleaseTitle {
                font-size: 12px;
                font-weight: 700;
                color: #3f3f46;
            }
            QLabel#ReleaseDateLabel {
                font-size: 11px;
                color: #71717a;
                font-weight: 600;
            }
            QLabel#ReleaseChangesText {
                font-size: 12px;
                color: #3f3f46;
                line-height: 1.4;
                padding-top: 2px;
            }
            QPushButton#PrimaryCloseBtn {
                background-color: #18181b;
                color: #ffffff;
                border: 1px solid #18181b;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 700;
            }
            QPushButton#PrimaryCloseBtn:hover {
                background-color: #27272a;
            }
            """
        )
