"""
자동 버전 관리 및 윈도우 메타데이터(VSVersionInfo) 포함 PyInstaller 빌드 스크립트 (build.py)

사용법:
  python build.py                  # 전체 빌드 수행 및 releases/v{version}/ 폴더로 결과물 보관
  python build.py --dry-run        # file_version_info.txt 및 assets/app_icon.ico 생성과 명령어 검증만 수행
  python build.py --prefix QuickPDFEditor  # 출력 파일명 접두어 지정 (기본값: My_PDF_Editor)
"""

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import List, Optional, Tuple

# 프로젝트 루트 경로 보장
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import src.__version__ as version_mod  # noqa: E402
from src.__version__ import (  # noqa: E402
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    BUILD_DATE,
    KEY_FEATURES,
    KEYBOARD_SHORTCUTS,
    RELEASE_NOTES,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
    __version__,
)


def sync_version_and_docs(
    root_dir: str,
    bump_part: Optional[str] = None,
    summary: str = "",
    changes: Optional[List[str]] = None,
) -> str:
    """
    빌드 시점에 src/__version__.py, README.md, assets/help_metadata.json을
    모두 최신 버전·빌드일자·변경내역·주요기능으로 자동 동기화합니다.
    """
    version_file = os.path.join(root_dir, "src", "__version__.py")
    today_str = datetime.now().strftime("%Y-%m-%d")

    if bump_part:
        from git_workflow import bump_version_in_file

        bump_version_in_file(bump_part, summary, changes or [])
    else:
        # BUILD_DATE를 오늘 날짜로 최신화하고 추가 변경사항(--change)이 있으면 반영
        with open(version_file, "r", encoding="utf-8") as f:
            v_content = f.read()
        v_content_new = re.sub(
            r'BUILD_DATE:\s*str\s*=\s*"[^"]*"',
            f'BUILD_DATE: str = "{today_str}"',
            v_content,
        )
        if v_content_new != v_content:
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(v_content_new)

    importlib.reload(version_mod)
    cur_ver = version_mod.__version__
    cur_app_ver = version_mod.APP_VERSION
    cur_build_date = version_mod.BUILD_DATE
    cur_features = version_mod.KEY_FEATURES
    cur_shortcuts = version_mod.KEYBOARD_SHORTCUTS
    cur_notes = version_mod.RELEASE_NOTES

    # 1. assets/help_metadata.json 생성 (도움말 다이얼로그용 최신 빌드 스냅샷)
    assets_dir = os.path.join(root_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    help_meta_path = os.path.join(assets_dir, "help_metadata.json")
    help_payload = {
        "app_name": version_mod.APP_NAME,
        "app_version": cur_app_ver,
        "build_date": cur_build_date,
        "app_description": version_mod.APP_DESCRIPTION,
        "key_features": cur_features,
        "keyboard_shortcuts": cur_shortcuts,
        "release_notes": cur_notes,
    }
    with open(help_meta_path, "w", encoding="utf-8") as f:
        json.dump(help_payload, f, ensure_ascii=False, indent=2)

    # 2. README.md의 주요 기능 / 단축키 안내 / 변경 이력 / 버전 번호 자동 동기화
    readme_path = os.path.join(root_dir, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        # 주요 기능 마크다운 블록 생성
        feat_lines = ["## 주요 기능 (Key Features)\n"]
        for group in cur_features:
            feat_lines.append(f"### {group.get('title', '')}")
            for item in group.get("items", []):
                feat_lines.append(f"- {item}")
            feat_lines.append("")
        feat_block = "\n".join(feat_lines).rstrip() + "\n"

        readme_text = re.sub(
            r"## 주요 기능 \(Key Features\).*?(?=\n---\n)",
            feat_block,
            readme_text,
            flags=re.DOTALL,
        )

        # 단축키 안내 마크다운 블록 생성
        sc_lines = [
            "## 단축키 안내 (Keyboard Shortcuts)\n",
            "| 분류 | 단축키 | 동작 설명 |",
            "| :--- | :--- | :--- |",
        ]
        for sc in cur_shortcuts:
            cat = sc.get("category", "")
            key = sc.get("shortcut", "")
            desc = sc.get("description", "")
            sc_lines.append(f"| **{cat}** | `{key}` | {desc} |")
        sc_block = "\n".join(sc_lines) + "\n"

        readme_text = re.sub(
            r"## 단축키 안내 \(Keyboard Shortcuts\).*?(?=\n---\n)",
            sc_block,
            readme_text,
            flags=re.DOTALL,
        )

        # 변경 이력 (Changelog) 마크다운 블록 생성
        cl_lines = ["## 변경 이력 (Changelog)\n"]
        for note in cur_notes:
            cl_lines.append(
                f"### {note.get('version', '')} ({note.get('date', '')})"
            )
            for ch in note.get("changes", []):
                cl_lines.append(f"- {ch}")
            cl_lines.append("")
        cl_block = "\n".join(cl_lines).rstrip() + "\n"

        readme_text = re.sub(
            r"## 변경 이력 \(Changelog\).*\Z",
            cl_block,
            readme_text,
            flags=re.DOTALL,
        )

        # README 내 실행 파일 버전 표기 최신화 (예: QuickPDFEditor_v1.0.0.exe -> QuickPDFEditor_v{cur_ver}.exe)
        readme_text = re.sub(
            r"QuickPDFEditor_v\d+\.\d+\.\d+\.exe",
            f"QuickPDFEditor_v{cur_ver}.exe",
            readme_text,
        )

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_text)

    # 3. releases/v{cur_ver}/RELEASE_NOTES_v{cur_ver}.txt 자동 생성/갱신
    release_dir = os.path.join(root_dir, "releases", f"v{cur_ver}")
    os.makedirs(release_dir, exist_ok=True)
    notes_txt_path = os.path.join(release_dir, f"RELEASE_NOTES_v{cur_ver}.txt")
    exe_filename = f"QuickPDFEditor_v{cur_ver}.exe"
    with open(notes_txt_path, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write(
            f" {version_mod.APP_NAME} ({cur_app_ver}) - 빌드 일자: {cur_build_date}\n"
        )
        f.write(f" 실행 파일: {exe_filename}\n")
        f.write("============================================================\n\n")
        for note in cur_notes:
            f.write(f"[{note.get('version')}] ({note.get('date')}) - {note.get('summary')}\n")
            for change in note.get("changes", []):
                f.write(f"  - {change}\n")
            f.write("\n")

    print(
        f"[0/4] 도움말 메타데이터(assets/help_metadata.json), README.md 및 릴리스 노트 동기화 완료 -> {cur_app_ver} ({cur_build_date})"
    )
    return cur_ver


def parse_version_tuple(version_str: str) -> Tuple[int, int, int, int]:
    """
    '1.1.0' 형태의 시맨틱 버전 문자열을 윈도우 파일 버전 4자리 튜플 (1, 1, 0, 0)로 변환합니다.
    """
    clean = version_str.lstrip("vV").strip()
    parts = [int(p) if p.isdigit() else 0 for p in clean.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return (parts[0], parts[1], parts[2], parts[3])


def generate_version_info_file(
    output_path: str,
    exe_filename: str,
    version_str: str = __version__,
    app_name: str = APP_NAME,
    description: str = APP_DESCRIPTION,
) -> str:
    """
    윈도우 실행 파일 속성창 -> [자세히] 탭에 표시될 VSVersionInfo 포맷의
    file_version_info.txt 파일을 빌드 시점의 버전 번호로 동적 생성합니다.
    """
    v_tuple = parse_version_tuple(version_str)
    v_str_4 = f"{v_tuple[0]}.{v_tuple[1]}.{v_tuple[2]}.{v_tuple[3]}"
    current_year = datetime.now().year

    content = f"""# UTF-8
# Auto-generated by build.py for {app_name} v{version_str}
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v_tuple},
    prodvers={v_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '041204B0',
          [
            StringStruct('CompanyName', '{app_name} Project'),
            StringStruct('FileDescription', '{description}'),
            StringStruct('FileVersion', '{v_str_4}'),
            StringStruct('InternalName', '{os.path.splitext(exe_filename)[0]}'),
            StringStruct('LegalCopyright', 'Copyright (c) {current_year} {app_name}. All rights reserved.'),
            StringStruct('OriginalFilename', '{exe_filename}'),
            StringStruct('ProductName', '{app_name}'),
            StringStruct('ProductVersion', 'v{version_str} ({BUILD_DATE})')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1042, 1200])])
  ]
)
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[1/4] 윈도우 버전 메타데이터 생성 완료: {output_path} -> {v_tuple}")
    return output_path


def ensure_app_icon(root_dir: str) -> str:
    """
    루트 폴더의 My_pdf_editer_icon.png를 이용하여 assets/app_icon.ico 아이콘 파일을
    자동 생성(또는 갱신)하고 사용할 아이콘 경로를 반환합니다.
    """
    assets_dir = os.path.join(root_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    ico_path = os.path.join(assets_dir, "app_icon.ico")
    png_path = os.path.join(root_dir, "My_pdf_editer_icon.png")

    if os.path.exists(png_path):
        try:
            from PIL import Image

            img = Image.open(png_path).convert("RGBA")
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(ico_path, format="ICO", sizes=icon_sizes)
            print(f"[2/4] 아이콘 변환 및 지정 완료: {png_path} -> {ico_path}")
            return ico_path
        except Exception as e:
            print(f"[경고] ICO 변환 중 예외 발생 ({e}), 원본 PNG 아이콘을 직접 사용합니다.")
            return png_path

    if os.path.exists(ico_path):
        print(f"[2/4] 기존 아이콘 파일 사용: {ico_path}")
        return ico_path

    raise FileNotFoundError(
        "아이콘 파일을 찾을 수 없습니다: My_pdf_editer_icon.png 또는 assets/app_icon.ico가 필요합니다."
    )


def build_pyinstaller_command(
    exe_name_without_ext: str,
    icon_path: str,
    version_file_path: str,
    dist_dir: str,
    work_dir: str,
) -> list:
    """
    PyMuPDF(fitz/pymupdf) 및 PyQt6 동적 라이브러리/리소스 누락 방지 옵션이 포함된
    PyInstaller 명령어 리스트를 구성합니다.
    """
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",                         # 단일 실행 파일(.exe) 생성
        "--windowed",                        # 콘솔 창 숨김 (--noconsole과 동일)
        "--noupx",                           # Qt6 / MuPDF DLL 손상 및 오탐 방지
        f"--name={exe_name_without_ext}",    # 예: My_PDF_Editor_v1.0.0 또는 QuickPDFEditor_v1.0.0
        f"--icon={icon_path}",               # assets/app_icon.ico 자동 지정
        f"--version-file={version_file_path}",  # 동적 생성된 file_version_info.txt 적용
        f"--distpath={dist_dir}",
        f"--workpath={work_dir}",
        # 리소스 파일 번들링 (런타임 sys._MEIPASS 내부 포함)
        "--add-data=My_pdf_editer_icon.png;.",
        "--add-data=assets;assets",
        # PyMuPDF(fitz / pymupdf) C-Extension 및 DLL 전체 수집
        "--collect-all=fitz",
        "--collect-all=pymupdf",
        # PyQt6 필수 C 바인딩 및 내부 모듈 명시
        "--hidden-import=PyQt6.sip",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtPrintSupport",
        # 불필요한 타 GUI 프레임워크 및 무거운 외부 패키지 제외 (빌드 속도/용량 최적화)
        "--exclude-module=PyQt5",
        "--exclude-module=PySide2",
        "--exclude-module=PySide6",
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=torchaudio",
        "--exclude-module=pyarrow",
        "--exclude-module=openpyxl",
        "--exclude-module=tensorflow",
        "--exclude-module=sklearn",
        "main.py",
    ]
    return cmd


def archive_to_releases(
    built_exe_path: str, version_str: str, root_dir: str
) -> str:
    """
    빌드 완료된 실행 파일을 releases/v{version}/ 폴더로 이동·보관하고,
    해당 버전의 릴리스 노트 요약 텍스트 파일도 함께 저장합니다.
    """
    release_dir = os.path.join(root_dir, "releases", f"v{version_str}")
    os.makedirs(release_dir, exist_ok=True)

    exe_filename = os.path.basename(built_exe_path)
    target_exe_path = os.path.join(release_dir, exe_filename)

    if os.path.exists(target_exe_path):
        os.remove(target_exe_path)

    shutil.move(built_exe_path, target_exe_path)

    # 릴리스 노트 요약 텍스트 파일 함께 생성
    notes_txt_path = os.path.join(release_dir, f"RELEASE_NOTES_v{version_str}.txt")
    with open(notes_txt_path, "w", encoding="utf-8") as f:
        f.write(f"============================================================\n")
        f.write(
            f" {version_mod.APP_NAME} ({version_mod.APP_VERSION}) - 빌드 일자: {version_mod.BUILD_DATE}\n"
        )
        f.write(f" 실행 파일: {exe_filename}\n")
        f.write(f"============================================================\n\n")
        for note in version_mod.RELEASE_NOTES:
            f.write(f"[{note.get('version')}] ({note.get('date')}) - {note.get('summary')}\n")
            for change in note.get("changes", []):
                f.write(f"  - {change}\n")
            f.write("\n")

    print(f"[4/4] 릴리스 패키지 보관 완료: {target_exe_path}")
    return target_exe_path


def main():
    parser = argparse.ArgumentParser(
        description="윈도우 버전 메타데이터 및 도움말/README 자동 최신화 PyInstaller 빌드 스크립트"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="QuickPDFEditor",
        help="생성할 실행 파일명 접두어 (기본값: QuickPDFEditor -> QuickPDFEditor_v1.1.0.exe)",
    )
    parser.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        default=None,
        help="빌드 전 시맨틱 버전(patch/minor/major)을 자동으로 올리고 변경 이력을 추가합니다",
    )
    parser.add_argument(
        "--summary",
        "-s",
        type=str,
        default="",
        help="--bump 사용 시 이번 빌드 버전의 한 줄 요약",
    )
    parser.add_argument(
        "--change",
        "-c",
        action="append",
        default=[],
        help="--bump 사용 시 이번 빌드의 세부 변경 사항 (여러 번 지정 가능)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 PyInstaller 컴파일을 생략하고 버전/도움말/README 동기화 및 아이콘·메타데이터 생성만 검증",
    )
    args = parser.parse_args()

    # 0. 버전·빌드일자·도움말 메타데이터(assets/help_metadata.json) 및 README.md 자동 동기화
    version_str = sync_version_and_docs(
        root_dir=ROOT_DIR,
        bump_part=args.bump,
        summary=args.summary,
        changes=args.change,
    )
    exe_base_name = f"{args.prefix}_v{version_str}"
    exe_filename = f"{exe_base_name}.exe"

    print("============================================================")
    print(f" [{version_mod.APP_NAME}] 자동 빌드 시작 - 버전: v{version_str}")
    print(f" 출력 대상 파일명: {exe_filename}")
    print("============================================================")

    # 1. file_version_info.txt 동적 생성
    version_file_path = os.path.join(ROOT_DIR, "file_version_info.txt")
    generate_version_info_file(
        output_path=version_file_path,
        exe_filename=exe_filename,
        version_str=version_str,
    )

    # 2. assets/app_icon.ico 자동 준비 (My_pdf_editer_icon.png 변환)
    icon_path = ensure_app_icon(ROOT_DIR)

    # 3. PyInstaller 빌드 명령 구성
    dist_dir = os.path.join(ROOT_DIR, "dist")
    work_dir = os.path.join(ROOT_DIR, "build", f"v{version_str}")
    cmd = build_pyinstaller_command(
        exe_name_without_ext=exe_base_name,
        icon_path=icon_path,
        version_file_path=version_file_path,
        dist_dir=dist_dir,
        work_dir=work_dir,
    )

    print("[3/4] PyInstaller 빌드 명령어:")
    print("  " + " ".join(cmd))

    if args.dry_run:
        print("[Dry-Run 완료] 메타데이터 및 아이콘 생성이 정상 확인되었습니다.")
        return

    result = subprocess.run(cmd, cwd=ROOT_DIR)
    if result.returncode != 0:
        print(f"[오류] PyInstaller 빌드가 실패했습니다 (종료 코드: {result.returncode}).")
        sys.exit(result.returncode)

    built_exe_path = os.path.join(dist_dir, exe_filename)
    if not os.path.exists(built_exe_path):
        print(f"[오류] 빌드된 실행 파일을 찾을 수 없습니다: {built_exe_path}")
        sys.exit(1)

    # 4. releases/v{version}/ 폴더 생성 및 결과물 이동/보관
    final_path = archive_to_releases(built_exe_path, version_str, ROOT_DIR)
    size_mb = os.path.getsize(final_path) / (1024 * 1024)
    print("============================================================")
    print(f" 빌드 및 릴리스 보관이 완료되었습니다!")
    print(f" - 최종 경로: {final_path} ({size_mb:.2f} MB)")
    print("============================================================")


if __name__ == "__main__":
    main()
