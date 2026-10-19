# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# 1. PyMuPDF(fitz / pymupdf)의 내부 C-Extension(_extra, _mupdf 등) 및 동적 라이브러리(DLL) 전체 수집
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all("fitz")
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("pymupdf")

# 2. 프로젝트 리소스 파일 포함 (실행 시 sys._MEIPASS 루트에 압축 해제됨)
added_datas = [
    ("My_pdf_editer_icon.png", "."),
]
if os.path.isdir("assets"):
    added_datas.append(("assets", "assets"))

datas = added_datas + fitz_datas + pymupdf_datas
binaries = fitz_binaries + pymupdf_binaries

# 3. C-Extension 및 PyQt6 / PyMuPDF 누락 방지용 hiddenimports
hiddenimports = (
    [
        "fitz",
        "pymupdf",
        "PyQt6.sip",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ]
    + fitz_hiddenimports
    + pymupdf_hiddenimports
    + collect_submodules("src")
)

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PySide2",
        "PySide6",
        "tkinter",
        "matplotlib",
        "pandas",
        "scipy",
        "torch",
        "torchvision",
        "torchaudio",
        "pyarrow",
        "openpyxl",
        "tensorflow",
        "sklearn",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 4. 단일 실행 파일(--onefile) + 콘솔 창 숨김(--noconsole) + 아이콘 적용
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="My_PDF_Editor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Qt6 / MuPDF DLL 손상 및 백신 오탐 방지를 위해 UPX 비활성화 권장
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔(검은색 터미널) 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="My_pdf_editer_icon.png",  # 루트 폴더의 PNG 아이콘 지정 (Pillow 설치 시 자동 ICO 변환)
)
