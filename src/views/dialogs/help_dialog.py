import json
import os
from typing import Any, Dict, List
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
    QGridLayout,
)

from src.__version__ import (
    APP_NAME,
    APP_VERSION,
    BUILD_DATE,
    APP_DESCRIPTION,
    KEY_FEATURES,
    KEYBOARD_SHORTCUTS,
    RELEASE_NOTES,
)
from src.utils.resource_path import get_resource_path


def load_latest_help_metadata() -> Dict[str, Any]:
    """
    src/__version__.py의 기본 메타데이터를 로드하되,
    빌드 스크립트(build.py / git_workflow.py)가 생성한 assets/help_metadata.json이
    존재하면 해당 최신 빌드 메타데이터를 우선 반영합니다.
    """
    data: Dict[str, Any] = {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "build_date": BUILD_DATE,
        "app_description": APP_DESCRIPTION,
        "key_features": KEY_FEATURES,
        "keyboard_shortcuts": KEYBOARD_SHORTCUTS,
        "release_notes": RELEASE_NOTES,
    }

    meta_path = get_resource_path(os.path.join("assets", "help_metadata.json"))
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                # src/__version__.py의 버전이 더 높거나 같으면 코드 우선, 빌드 메타데이터가 최신이면 반영
                for k in (
                    "app_name",
                    "app_version",
                    "build_date",
                    "app_description",
                    "key_features",
                    "keyboard_shortcuts",
                    "release_notes",
                ):
                    if loaded.get(k):
                        data[k] = loaded[k]
                # 코드의 APP_VERSION이 항상 최우선 일치하도록 보장
                data["app_version"] = APP_VERSION
                data["release_notes"] = RELEASE_NOTES
                data["key_features"] = KEY_FEATURES
                data["keyboard_shortcuts"] = KEYBOARD_SHORTCUTS
                if loaded.get("build_date", "") > BUILD_DATE:
                    data["build_date"] = loaded["build_date"]
        except Exception:
            pass

    return data


class HelpDialog(QDialog):
    """
    도움말(F1) 전용 다이얼로그.
    1) 현재 빌드 버전 및 최신 변경 내용 요약
    2) GitHub README.md에 수록된 전체 주요 기능(Key Features)
    3) 상단 메뉴 표시줄 및 마우스/키보드 단축키 안내
    4) 버전별 변경 이력(Change Log)
    을 항상 최신 상태로 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.meta = load_latest_help_metadata()
        app_name = self.meta["app_name"]
        app_version = self.meta["app_version"]

        self.setWindowTitle(f"{app_name} 도움말 ({app_version})")
        self.setMinimumSize(680, 620)
        self.resize(740, 680)

        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        app_name = self.meta["app_name"]
        app_version = self.meta["app_version"]
        build_date = self.meta["build_date"]
        app_desc = self.meta["app_description"]
        key_features: List[Dict[str, Any]] = self.meta["key_features"]
        shortcuts: List[Dict[str, str]] = self.meta["keyboard_shortcuts"]
        release_notes: List[Dict[str, Any]] = self.meta["release_notes"]

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(12)

        # -----------------------------------------------------------------
        # 1. 상단 헤더 카드 (아이콘 + 도움말 타이틀 + 버전 배지 + 빌드 일자)
        # -----------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("HelpHeaderCard")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setFixedSize(54, 54)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = get_resource_path("My_pdf_editer_icon.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                icon_label.setPixmap(
                    pix.scaled(
                        50,
                        50,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        header_layout.addWidget(icon_label)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(4)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        lbl_title = QLabel(f"{app_name} 사용 도움말")
        lbl_title.setObjectName("HelpMainTitle")

        lbl_ver_badge = QLabel(app_version)
        lbl_ver_badge.setObjectName("HelpVersionBadge")

        name_row.addWidget(lbl_title)
        name_row.addWidget(lbl_ver_badge)
        name_row.addStretch(1)

        lbl_desc = QLabel(app_desc)
        lbl_desc.setObjectName("HelpDescription")

        lbl_meta = QLabel(f"최신 빌드 일자: {build_date}   |   버전: {app_version}")
        lbl_meta.setObjectName("HelpBuildMeta")

        title_vbox.addLayout(name_row)
        title_vbox.addWidget(lbl_desc)
        title_vbox.addWidget(lbl_meta)
        header_layout.addLayout(title_vbox, stretch=1)

        root_layout.addWidget(header_frame)

        # -----------------------------------------------------------------
        # 2. 본문 스크롤 영역 (GitHub README 주요 기능 + 메뉴 및 단축키 일람)
        # -----------------------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("HelpScrollArea")
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_content.setObjectName("HelpScrollContent")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(14)

        # --- [섹션 A] GitHub README 주요 기능 (Key Features) ---
        lbl_feat_section = QLabel("✨ 주요 기능 안내 (Key Features)")
        lbl_feat_section.setObjectName("MajorSectionTitle")
        content_layout.addWidget(lbl_feat_section)

        for feat_group in key_features:
            group_title = str(feat_group.get("title", ""))
            items = feat_group.get("items", [])

            card = QFrame()
            card.setObjectName("HelpInfoCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)

            lbl_group = QLabel(group_title)
            lbl_group.setObjectName("CardGroupTitle")
            card_layout.addWidget(lbl_group)

            if isinstance(items, list) and items:
                lines = "\n".join(f"• {item}" for item in items)
                lbl_items = QLabel(lines)
                lbl_items.setObjectName("CardBodyText")
                lbl_items.setWordWrap(True)
                card_layout.addWidget(lbl_items)

            content_layout.addWidget(card)

        # --- [섹션 B] 메뉴 및 단축키 안내 (Keyboard & Mouse Shortcuts) ---
        lbl_sc_section = QLabel("⌨️ 메뉴 및 단축키 일람 (Shortcuts)")
        lbl_sc_section.setObjectName("MajorSectionTitle")
        content_layout.addWidget(lbl_sc_section)

        sc_card = QFrame()
        sc_card.setObjectName("HelpInfoCard")
        sc_grid = QGridLayout(sc_card)
        sc_grid.setContentsMargins(14, 12, 14, 12)
        sc_grid.setHorizontalSpacing(14)
        sc_grid.setVerticalSpacing(7)

        hdr_cat = QLabel("분류")
        hdr_key = QLabel("단축키 / 조작")
        hdr_desc = QLabel("동작 설명")
        for h in (hdr_cat, hdr_key, hdr_desc):
            h.setObjectName("ShortcutTableHeader")
        sc_grid.addWidget(hdr_cat, 0, 0)
        sc_grid.addWidget(hdr_key, 0, 1)
        sc_grid.addWidget(hdr_desc, 0, 2)

        for row_idx, sc in enumerate(shortcuts, start=1):
            lbl_cat = QLabel(sc.get("category", ""))
            lbl_cat.setObjectName("ShortcutCategoryText")

            lbl_key = QLabel(sc.get("shortcut", ""))
            lbl_key.setObjectName("ShortcutKeyBadge")

            lbl_desc_item = QLabel(sc.get("description", ""))
            lbl_desc_item.setObjectName("CardBodyText")
            lbl_desc_item.setWordWrap(True)

            sc_grid.addWidget(lbl_cat, row_idx, 0, alignment=Qt.AlignmentFlag.AlignTop)
            sc_grid.addWidget(lbl_key, row_idx, 1, alignment=Qt.AlignmentFlag.AlignTop)
            sc_grid.addWidget(lbl_desc_item, row_idx, 2)

        sc_grid.setColumnStretch(2, 1)
        content_layout.addWidget(sc_card)

        content_layout.addStretch(1)
        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area, stretch=1)

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
            QFrame#HelpHeaderCard {
                background-color: #fafafa;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
            }
            QLabel#HelpMainTitle {
                font-size: 17px;
                font-weight: 800;
                color: #18181b;
            }
            QLabel#HelpVersionBadge {
                background-color: #18181b;
                color: #ffffff;
                font-size: 11px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 5px;
            }
            QLabel#HelpDescription {
                font-size: 12px;
                color: #3f3f46;
                font-weight: 600;
            }
            QLabel#HelpBuildMeta {
                font-size: 11px;
                color: #71717a;
            }
            QScrollArea#HelpScrollArea {
                background-color: #fafafa;
                border: 1px solid #e4e4e7;
                border-radius: 8px;
            }
            QWidget#HelpScrollContent {
                background-color: #fafafa;
            }
            QFrame#LatestBuildCard {
                background-color: #ffffff;
                border: 1.5px solid #27272a;
                border-radius: 7px;
            }
            QFrame#HelpInfoCard {
                background-color: #ffffff;
                border: 1px solid #e4e4e7;
                border-radius: 7px;
            }
            QLabel#SectionHeaderLabel {
                font-size: 13px;
                font-weight: 800;
                color: #18181b;
            }
            QLabel#MajorSectionTitle {
                font-size: 13px;
                font-weight: 800;
                color: #18181b;
                padding-top: 4px;
                padding-left: 2px;
            }
            QLabel#CardGroupTitle {
                font-size: 12px;
                font-weight: 700;
                color: #18181b;
            }
            QLabel#CardBodyText {
                font-size: 12px;
                color: #3f3f46;
            }
            QLabel#ShortcutTableHeader {
                font-size: 11px;
                font-weight: 800;
                color: #18181b;
                padding-bottom: 4px;
            }
            QLabel#ShortcutCategoryText {
                font-size: 11px;
                font-weight: 700;
                color: #52525b;
            }
            QLabel#ShortcutKeyBadge {
                background-color: #f4f4f5;
                color: #18181b;
                border: 1px solid #d4d4d8;
                border-radius: 4px;
                padding: 2px 6px;
                font-family: "Consolas", "Malgun Gothic", monospace;
                font-size: 11px;
                font-weight: 700;
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
