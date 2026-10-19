"""
Git 브랜치 워크플로우 및 src/__version__.py 시맨틱 버전 자동 갱신 보조 스크립트 (git_workflow.py)

사용 예시:
  1) 새 기능 브랜치 생성/전환:
     python git_workflow.py start-feature watermark-support

  2) src/__version__.py 버전 자동 올리기 (patch / minor / major):
     python git_workflow.py bump minor --summary "워터마크 삽입 기능 추가" --change "페이지별 텍스트/이미지 워터마크 지원"

  3) 릴리스 병합 및 Annotated 태그 생성 안내/실행:
     python git_workflow.py release-guide
"""

import argparse
import os
import re
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(ROOT_DIR, "src", "__version__.py")


def read_current_version():
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    from src.__version__ import VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, __version__
    return VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, __version__


def bump_version_in_file(part: str, summary: str, changes: list) -> str:
    major, minor, patch, old_ver = read_current_version()
    part = part.lower().strip()
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"지원하지 않는 버전 단위입니다: {part} (major/minor/patch 중 선택)")

    new_ver = f"{major}.{minor}.{patch}"
    today_str = datetime.now().strftime("%Y-%m-%d")

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r"VERSION_MAJOR:\s*int\s*=\s*\d+", f"VERSION_MAJOR: int = {major}", content)
    content = re.sub(r"VERSION_MINOR:\s*int\s*=\s*\d+", f"VERSION_MINOR: int = {minor}", content)
    content = re.sub(r"VERSION_PATCH:\s*int\s*=\s*\d+", f"VERSION_PATCH: int = {patch}", content)
    content = re.sub(r'BUILD_DATE:\s*str\s*=\s*"[^"]*"', f'BUILD_DATE: str = "{today_str}"', content)

    # RELEASE_NOTES 맨 앞에 새 버전 블록 자동 삽입
    if summary or changes:
        use_summary = summary or f"v{new_ver} 업데이트"
        use_changes = changes if changes else [use_summary]
        changes_lines = ",\n".join(f'            "{c}"' for c in use_changes)
        new_entry = (
            "    {\n"
            f'        "version": "v{new_ver}",\n'
            f'        "date": "{today_str}",\n'
            f'        "summary": "{use_summary}",\n'
            "        \"changes\": [\n"
            f"{changes_lines},\n"
            "        ],\n"
            "    },\n"
        )
        marker = "RELEASE_NOTES: List[Dict[str, Union[str, List[str]]]] = [\n"
        if marker in content:
            content = content.replace(marker, marker + new_entry, 1)

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[완료] src/__version__.py 버전 갱신: v{old_ver} -> v{new_ver} ({today_str})")
    return new_ver


def main():
    parser = argparse.ArgumentParser(description="Git 브랜치 및 시맨틱 버전 관리 도우미")
    subparsers = parser.add_subparsers(dest="command")

    # bump 서브커맨드
    p_bump = subparsers.add_parser("bump", help="src/__version__.py의 버전(patch/minor/major) 자동 갱신")
    p_bump.add_argument("part", choices=["patch", "minor", "major"], help="올릴 버전 자리")
    p_bump.add_argument("--summary", "-s", type=str, default="", help="릴리스 노트 한 줄 요약")
    p_bump.add_argument("--change", "-c", action="append", default=[], help="세부 변경 항목 (여러 번 지정 가능)")

    args = parser.parse_args()
    if args.command == "bump":
        new_ver = bump_version_in_file(args.part, args.summary, args.change)
        commit_prefix = "fix" if args.part == "patch" else "feat"
        msg = args.summary or f"v{new_ver} 버전 업데이트"
        print("\n다음 추천 Git 명령어:")
        print(f'  git add src/__version__.py')
        print(f'  git commit -m "{commit_prefix}: {msg} (v{new_ver})"')
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
