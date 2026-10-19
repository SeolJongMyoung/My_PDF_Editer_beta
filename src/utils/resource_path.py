import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    PyInstaller --onefile 빌드 환경(sys._MEIPASS 임시 압축 해제 폴더)과
    일반 파이썬 실행 환경 모두에서 리소스 파일의 절대 경로를 안전하게 반환합니다.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = getattr(sys, "_MEIPASS")
    else:
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    return os.path.join(base_path, relative_path)
