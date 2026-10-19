from typing import Dict, List, Optional, Union

# -----------------------------------------------------------------------------
# 시맨틱 버저닝 (Semantic Versioning: Major.Minor.Patch) 중앙 관리 모듈
# -----------------------------------------------------------------------------
APP_NAME: str = "My PDF Editor"
VERSION_MAJOR: int = 1
VERSION_MINOR: int = 0
VERSION_PATCH: int = 0

__version__: str = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
APP_VERSION: str = f"v{__version__}"
BUILD_DATE: str = "2026-10-19"
APP_DESCRIPTION: str = "PyQt6 & PyMuPDF 기반 데스크톱 PDF 뷰어 및 편집 도구"

# 버전별 주요 변경 이력 (Change Log / Release Notes)
RELEASE_NOTES: List[Dict[str, Union[str, List[str]]]] = [
    {
        "version": "v1.0.0",
        "date": "2026-10-19",
        "summary": "정식 릴리스 및 전체 편집/병합/추출 기능 완성",
        "changes": [
            "외부 PDF 파일 페이지 합병(삽입) 기능 추가 (미리보기 썸네일, 구간 지정, 탐색기 드래그 앤 드롭 지원)",
            "페이지 목록 드래그 앤 드롭 순서 이동 기능 추가 (실시간 가로 구분선 표시 및 이동 확인 대화창)",
            "Ctrl/Shift 다중 페이지 선택 및 선택 페이지 새 PDF 추출 저장 기능",
            "텍스트 수정 고도화: 윈도우 설치 전체 폰트(970+종) 스캔·검색 필터 및 글자 색상(Color) 변경 기능",
            "최대 10단계 실행 취소(Undo, Ctrl+Z) / 다시 실행(Redo, Ctrl+Y) 및 종료 시 미저장 변경사항 확인",
            "오른쪽 접이식 책갈피(Bookmark) 드로어 패널 및 모던 그레이스케일 1줄 툴바 UI 적용",
        ],
    },
    {
        "version": "v0.3.0",
        "date": "2026-10-19",
        "summary": "텍스트 서식 감지 및 UI/UX 개선",
        "changes": [
            "원본 PDF 텍스트의 폰트·크기·굵기·기울임·베이스라인(Baseline) 자동 감지 및 정밀 치환",
            "페이지 목록 썸네일 선택 시 페이지 번호 텍스트를 제외한 이미지 박스 단독 하이라이트 적용",
            "흰색 바탕 캔버스 및 접이식 책갈피 관리(조회/추가/삭제) 기능 구현",
        ],
    },
    {
        "version": "v0.1.0",
        "date": "2026-10-19",
        "summary": "초기 프로토타입 및 핵심 뷰어/주석 엔진 구축",
        "changes": [
            "PyQt6 + PyMuPDF(fitz) MVC 아키텍처 설계 및 화면-PDF 좌표 정밀 변환(CoordConverter) 구현",
            "PDF 열기/저장, 확대/축소(Zoom), 페이지 회전/삭제, 사각 박스 검토 및 형광펜 하이라이트 모드 구현",
        ],
    },
]


def get_window_title(
    file_name: Optional[str] = None, is_modified: bool = False
) -> str:
    """
    메인 윈도우 타이틀바 문자열을 일관된 형식으로 반환합니다.
    - 기본 상태: "My PDF Editor - v1.0.0"
    - 파일 열림: "sample.pdf - My PDF Editor - v1.0.0"
    - 수정됨:    "sample.pdf * - My PDF Editor - v1.0.0"
    """
    base_title = f"{APP_NAME} - {APP_VERSION}"
    if file_name:
        dirty_mark = " *" if is_modified else ""
        return f"{file_name}{dirty_mark} - {base_title}"
    return base_title
