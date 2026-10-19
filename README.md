# My PDF Editor (QuickPDFEditor)

<p align="center">
  <img src="My_pdf_editer_icon.png" alt="My PDF Editor Logo" width="120" />
</p>

**My PDF Editor (`QuickPDFEditor`)**는 **PyQt6**와 **PyMuPDF (`fitz`)** 기반으로 제작된 가볍고 빠른 데스크톱 PDF 뷰어 및 올인원 편집 도구입니다.  
문서 열람부터 **원본 서식 유지 텍스트 수정, 형광펜/도형 주석, 다중 페이지 추출, 드래그 앤 드롭 페이지 순서 변경, 외부 PDF 병합, 책갈피(TOC) 편집**까지 직관적인 단일 화면 UI에서 처리할 수 있습니다.

---

## 주요 기능 (Key Features)

### 1. PDF 열람 및 탐색
- **고해상도 렌더링 & 확대/축소**: `25%` ~ `400%` 자유로운 줌 조절 및 `Ctrl + 마우스 휠` 확대/축소 지원
- **썸네일 사이드바**: 좌측 페이지 목록에서 빠른 페이지 이동 및 다중 페이지(`Ctrl` / `Shift` 클릭) 선택
- **접이식 책갈피(Bookmark) 드로어**: 우측 슬라이드 패널에서 문서 목차(TOC) 조회, 현재 페이지 책갈피 추가 및 삭제

### 2. 정밀 텍스트 수정 및 주석 도구
- **원본 텍스트 수정 (Redaction & Insertion)**:
  - 드래그한 영역의 원본 텍스트 **폰트, 크기, 굵기(Bold), 기울임(Italic), 베이스라인(Baseline) 좌표** 자동 감지
  - **Windows 시스템 설치 전체 폰트(970+종)** 실시간 검색 필터 및 **글자 색상(Color)** 피커 지원
- **형광펜 (Highlight)**: 마우스 드래그 영역에 반투명 노란색 하이라이트 주석 추가
- **사각 테두리 박스 (Rect Box)**: 주요 영역 강조를 위한 붉은색 사각 박스 마킹

### 3. 페이지 관리 (병합 · 추출 · 이동 · 회전 · 삭제)
- **외부 PDF 페이지 합병 (Merge)**:
  - 다른 PDF 파일의 첫 페이지 썸네일 미리보기 확인
  - 전체 또는 원하는 페이지 구간(`예: 1-3, 5`)만 지정하여 현재 문서의 원하는 위치(맨 앞/현재 페이지 앞·뒤/맨 끝/직접 지정)에 삽입
  - Windows 탐색기에서 PDF 파일을 좌측 페이지 목록으로 **드래그 앤 드롭(Drag & Drop)**하여 원하는 위치에 즉시 합병
- **드래그 앤 드롭 페이지 순서 변경**: 좌측 썸네일 목록에서 페이지를 마우스로 끌어 실시간 파란색 삽입 가이드라인 위치를 확인한 뒤 순서 재배치
- **선택 페이지 추출 (Extract)**: 다중 선택한 페이지들을 새로운 PDF 파일로 즉시 분리 저장
- **페이지 회전 및 삭제**: 선택 페이지 `90°` 시계 방향 회전 및 다중 페이지 일괄 삭제

### 4. 안전한 편집 이력 관리
- **실행 취소 / 다시 실행 (Undo / Redo)**: 메모리 스냅샷 기반으로 최대 **10단계**까지 모든 편집 작업(`텍스트 수정, 주석, 회전, 삭제, 이동, 병합, 책갈피`) 즉시 복원 (`Ctrl+Z` / `Ctrl+Y`)
- **미저장 변경사항 보호**: 문서 수정 시 타이틀바에 `*` 표시 및 프로그램 종료/새 파일 열기 시 저장 여부 확인 알림창 제공

---

## 단축키 안내 (Keyboard Shortcuts)

| 단축키 | 동작 설명 |
| :--- | :--- |
| `Ctrl + Z` | 실행 취소 (Undo, 최대 10단계) |
| `Ctrl + Y` / `Ctrl + Shift + Z` | 다시 실행 (Redo) |
| `Ctrl + 마우스 휠` | 캔버스 확대 / 축소 (Zoom In / Out) |
| `Ctrl + 클릭` | 페이지 목록에서 개별 다중 페이지 선택/해제 |
| `Shift + 클릭` | 페이지 목록에서 연속 구간 다중 페이지 선택 |

---

## 프로젝트 구조 (Directory Structure)

```text
My_PDF_Editer/
├── main.py                        # 애플리케이션 진입점 (Entry Point)
├── build.py                       # 버전 메타데이터 동적 생성 및 PyInstaller 원클릭 빌드 스크립트
├── git_workflow.py                # Git 브랜치/태그/릴리스 자동화 헬퍼 스크립트
├── requirements.txt               # Python 패키지 의존성 목록
├── My_pdf_editer_icon.png         # 애플리케이션 원본 아이콘
├── assets/
│   └── app_icon.ico               # 빌드 시 자동 변환되는 멀티 사이즈 Windows 아이콘
├── src/
│   ├── __version__.py             # 시맨틱 버전(v1.0.0) 및 릴리스 노트 중앙 관리
│   ├── controllers/
│   │   └── main_controller.py     # View 시그널과 Model 비즈니스 로직 연결 (MVC Controller)
│   ├── models/
│   │   └── pdf_document.py        # PyMuPDF(fitz) 래퍼, Undo/Redo 스택, 렌더링/편집 엔진 (MVC Model)
│   ├── utils/
│   │   └── coord_converter.py     # 화면 픽셀 좌표(QRectF) ↔ PDF 포인트 좌표(fitz.Rect) 정밀 변환기
│   └── views/
│       ├── main_window.py         # 메인 윈도우, 1줄 모던 툴바, 좌측 썸네일 리스트, 우측 책갈피 드로어
│       ├── canvas_view.py         # PDF 페이지 렌더링 캔버스 및 마우스 드래그 인터랙션 뷰
│       └── merge_dialog.py        # 외부 PDF 합병 설정 및 미리보기 다이얼로그
├── releases/
│   └── v1.0.0/
│       └── RELEASE_NOTES_v1.0.0.txt
└── .github/
    └── workflows/
        └── build-release.yml      # 태그 푸시 시 Windows 단일 EXE 자동 빌드 & GitHub Release 배포
```

---

## 설치 및 실행 방법 (Getting Started)

### 1. 실행 파일(`.exe`) 바로 다운로드
Python 설치 없이 바로 실행하려면 우측 **[Releases](https://github.com/SeolJongMyoung/My_PDF_Editer_beta/releases)** 탭에서 최신 버전의 `QuickPDFEditor_v1.0.0.exe` 파일을 다운로드하여 실행하세요.

### 2. 소스 코드로 실행 (개발 환경)
- **권장 환경**: Windows 10/11, Python 3.10 이상

```bash
# 1. 저장소 클론
git clone https://github.com/SeolJongMyoung/My_PDF_Editer_beta.git
cd My_PDF_Editer_beta

# 2. 의존성 패키지 설치
pip install -r requirements.txt

# 3. 애플리케이션 실행
python main.py
```

---

## 단일 실행 파일(`.exe`) 빌드 방법

프로젝트 루트의 `build.py`를 실행하면 `src/__version__.py`의 버전 정보를 읽어 **Windows 파일 속성 메타데이터(`file_version_info.txt`)** 및 **아이콘(`assets/app_icon.ico`)**을 자동 생성한 뒤, `releases/v{버전}/` 폴더에 단일 실행 파일(`QuickPDFEditor_v{버전}.exe`)과 릴리스 노트를 패키징합니다.

```bash
# 전체 빌드 수행 (releases/v1.0.0/QuickPDFEditor_v1.0.0.exe 생성)
python build.py

# 컴파일 없이 버전 메타데이터 및 아이콘 생성만 검증 (Dry-Run)
python build.py --dry-run
```

---

## GitHub Actions 자동 릴리스 (CI/CD)

`.github/workflows/build-release.yml` 워크플로우가 구성되어 있어, `v*` 형식의 Git 태그를 푸시하면 GitHub Actions의 `windows-latest` 러너에서 자동으로 단일 `.exe`를 빌드하고 **GitHub Releases**에 첨부 파일을 등록합니다.

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## 변경 이력 (Changelog)

### v1.0.0 (2026-10-19)
- 외부 PDF 파일 페이지 합병(삽입) 기능 추가 (미리보기 썸네일, 구간 지정, 탐색기 드래그 앤 드롭 지원)
- 페이지 목록 드래그 앤 드롭 순서 이동 기능 추가 (실시간 가로 구분선 표시 및 이동 확인 대화창)
- `Ctrl` / `Shift` 다중 페이지 선택 및 선택 페이지 새 PDF 추출 저장 기능
- 텍스트 수정 고도화: 윈도우 설치 전체 폰트(970+종) 스캔·검색 필터 및 글자 색상(Color) 변경 기능
- 최대 10단계 실행 취소(`Undo`, `Ctrl+Z`) / 다시 실행(`Redo`, `Ctrl+Y`) 및 종료 시 미저장 변경사항 확인
- 오른쪽 접이식 책갈피(Bookmark) 드로어 패널 및 모던 그레이스케일 1줄 툴바 UI 적용
