import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import fitz  # PyMuPDF
from PyQt6.QtGui import QImage, QPixmap


@dataclass
class TextStyleInfo:
    """클릭/드래그한 영역에서 추출한 원본 텍스트의 폰트·스타일·크기·좌표 정보"""
    rect: fitz.Rect
    text: str = ""
    raw_font_name: str = "Unknown"
    clean_font_name: str = "Unknown"
    matched_font_key: str = "gulim"
    font_size: float = 10.0
    is_bold: bool = False
    is_italic: bool = False
    color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    baseline_y: Optional[float] = None


class PdfHandler:
    """PyMuPDF(fitz)를 활용하여 PDF 문서 조작 및 10단계 Undo/Redo를 전담하는 클래스"""

    MAX_HISTORY: int = 10

    FONT_CATALOG: List[Tuple[str, str, str, Optional[str], Optional[str]]] = [
        ("gulim", "굴림 / 돋움 (Gulim / Dotum)", "C:/Windows/Fonts/gulim.ttc", None, None),
        ("batang", "바탕 / 명조 (Batang / Myeongjo)", "C:/Windows/Fonts/batang.ttc", None, None),
        ("malgun", "맑은 고딕 (Malgun Gothic)", "C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf", None),
        ("h2mjre", "HY신명조 (H2MJRE)", "C:/Windows/Fonts/H2MJRE.TTF", None, None),
        ("h2gtrm", "HY중고딕 / 견고딕 (H2GTRM)", "C:/Windows/Fonts/H2GTRM.TTF", "C:/Windows/Fonts/H2GTRE.TTF", None),
        ("h2gsrb", "HY궁서 (H2GSRB)", "C:/Windows/Fonts/H2GSRB.TTF", None, None),
        ("hmfmmuex", "휴먼명조 (HMFMMUEX)", "C:/Windows/Fonts/HMFMMUEX.TTC", None, None),
        ("nanum", "나눔고딕 (NanumGothic)", "C:/Windows/Fonts/NanumGothic.ttf", "C:/Windows/Fonts/NanumGothicBold.ttf", None),
        ("arial", "Arial (영문 고딕)", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/ariali.ttf"),
        ("times", "Times New Roman (영문 명조)", "C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/timesi.ttf"),
    ]

    def __init__(self, custom_font_path: Optional[str] = None):
        self.doc: Optional[fitz.Document] = None
        self.file_path: Optional[str] = None
        self._state_id: int = 0
        self._saved_state_id: int = 0
        self._next_state_seq: int = 1

        self._undo_stack: List[Tuple[bytes, int]] = []
        self._redo_stack: List[Tuple[bytes, int]] = []

        self.available_fonts: Dict[str, Dict[str, Optional[str]]] = self._scan_system_fonts()
        self.font_path: Optional[str] = self._resolve_font_path(custom_font_path)

    @property
    def is_modified(self) -> bool:
        return self.doc is not None and (self._state_id != self._saved_state_id)

    @is_modified.setter
    def is_modified(self, value: bool):
        if not value:
            self._saved_state_id = self._state_id
        else:
            if self._state_id == self._saved_state_id:
                self._state_id = self._next_state_seq
                self._next_state_seq += 1

    @property
    def can_undo(self) -> bool:
        return self.doc is not None and len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return self.doc is not None and len(self._redo_stack) > 0

    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        return len(self._redo_stack)

    def _push_undo_snapshot(self):
        if self.doc is None:
            return
        try:
            snapshot = self.doc.tobytes()
            self._undo_stack.append((snapshot, self._state_id))
            if len(self._undo_stack) > self.MAX_HISTORY:
                self._undo_stack.pop(0)
            self._redo_stack.clear()
        except Exception as e:
            print(f"[PdfHandler] Undo 스냅샷 생성 실패: {e}")

    def _advance_state(self):
        self._state_id = self._next_state_seq
        self._next_state_seq += 1

    def undo(self) -> bool:
        if not self.can_undo or self.doc is None:
            return False
        try:
            current_bytes = self.doc.tobytes()
            self._redo_stack.append((current_bytes, self._state_id))
            if len(self._redo_stack) > self.MAX_HISTORY:
                self._redo_stack.pop(0)

            prev_bytes, prev_state_id = self._undo_stack.pop()
            self.doc.close()
            self.doc = fitz.open("pdf", prev_bytes)
            self._state_id = prev_state_id
            return True
        except Exception as e:
            print(f"[PdfHandler] Undo 실행 오류: {e}")
            return False

    def redo(self) -> bool:
        if not self.can_redo or self.doc is None:
            return False
        try:
            current_bytes = self.doc.tobytes()
            self._undo_stack.append((current_bytes, self._state_id))
            if len(self._undo_stack) > self.MAX_HISTORY:
                self._undo_stack.pop(0)

            next_bytes, next_state_id = self._redo_stack.pop()
            self.doc.close()
            self.doc = fitz.open("pdf", next_bytes)
            self._state_id = next_state_id
            return True
        except Exception as e:
            print(f"[PdfHandler] Redo 실행 오류: {e}")
            return False

    KOREAN_FILENAME_ALIASES: Dict[str, str] = {
        "ngulim.ttf": "새굴림 (New Gulim)",
        "hmkmami.ttf": "휴먼아미체 (Ami R)",
        "hmkmrhd.ttf": "휴먼둥근헤드라인 (Headline R)",
        "hmfmold.ttf": "휴먼옛체 (Yet R)",
        "hmfmmag.ttf": "휴먼매직체 (Magic R)",
        "hmkmag.ttf": "휴먼매직체 (Magic R)",
        "hmkmagic.ttf": "휴먼매직체 (Magic R)",
        "hmfmpun.ttf": "휴먼편지체 (Pyunji R)",
        "hmfmpyun.ttf": "휴먼편지체 (Pyunji R)",
        "h2gprm.ttf": "HY그래픽M (HYGraphic-Medium)",
        "h2gtre.ttf": "HY견고딕 (HYGothic-Extra)",
        "h2hdrm.ttf": "HY헤드라인M (HYHeadLine-Medium)",
        "h2mkpb.ttf": "HY목각파임B (HYPMokGak-Bold)",
        "h2mjsm.ttf": "HY신명조M (HYSinMyeongJo-Medium)",
        "h2sa1m.ttf": "HY얕은샘물M (HYShortSamul-Medium)",
        "h2porl.ttf": "HY엽서L (HYPost-Light)",
        "h2porm.ttf": "HY엽서M (HYPost-Medium)",
        "malgunsl.ttf": "맑은 고딕 SemiLight (Malgun Gothic SL)",
    }

    def _scan_system_fonts(self) -> Dict[str, Dict[str, Optional[str]]]:
        fonts: Dict[str, Dict[str, Optional[str]]] = {}
        registered_files = set()

        # 1. 대표 한글/영문 표준 폰트 우선 등록
        for key, label, reg_path, bold_path, italic_path in self.FONT_CATALOG:
            if os.path.exists(reg_path):
                norm_reg = os.path.normcase(os.path.abspath(reg_path))
                registered_files.add(norm_reg)
                fonts[key] = {
                    "label": f"★ {label}",
                    "regular": reg_path,
                    "bold": bold_path if (bold_path and os.path.exists(bold_path)) else None,
                    "italic": italic_path if (italic_path and os.path.exists(italic_path)) else None,
                }

        # 2. Windows 레지스트리 및 Fonts 폴더에서 모든 설치된 폰트(.ttf, .ttc, .otf) 수집
        win_dir = os.environ.get("WINDIR", "C:/Windows")
        sys_fonts_dir = os.path.join(win_dir, "Fonts")
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        user_fonts_dir = (
            os.path.join(local_app_data, "Microsoft", "Windows", "Fonts")
            if local_app_data
            else ""
        )

        file_to_display_name: Dict[str, str] = {}
        try:
            import winreg

            reg_key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            for root_hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root_hive, reg_key_path) as k:
                        num_vals = winreg.QueryInfoKey(k)[1]
                        for i in range(num_vals):
                            raw_name, val, _ = winreg.EnumValue(k, i)
                            if not isinstance(val, str):
                                continue
                            font_path = (
                                val
                                if os.path.isabs(val)
                                else os.path.join(sys_fonts_dir, val)
                            )
                            if os.path.exists(font_path) and font_path.lower().endswith(
                                (".ttf", ".ttc", ".otf")
                            ):
                                norm_p = os.path.normcase(os.path.abspath(font_path))
                                clean_disp = (
                                    str(raw_name)
                                    .replace("(TrueType)", "")
                                    .replace("(OpenType)", "")
                                    .strip()
                                )
                                if norm_p not in file_to_display_name:
                                    file_to_display_name[norm_p] = clean_disp
                except Exception:
                    pass
        except Exception:
            pass

        # 폴더 직접 스캔으로 레지스트리에 누락된 폰트 파일까지 모두 포함
        for folder in (sys_fonts_dir, user_fonts_dir):
            if folder and os.path.isdir(folder):
                try:
                    for fname in os.listdir(folder):
                        if fname.lower().endswith((".ttf", ".ttc", ".otf")):
                            fpath = os.path.join(folder, fname)
                            norm_p = os.path.normcase(os.path.abspath(fpath))
                            if norm_p not in file_to_display_name:
                                file_to_display_name[norm_p] = os.path.splitext(fname)[0]
                except Exception:
                    pass

        korean_discovered: List[Tuple[str, str, str]] = []
        other_discovered: List[Tuple[str, str, str]] = []

        for norm_p, disp_name in file_to_display_name.items():
            if norm_p in registered_files:
                continue
            fname = os.path.basename(norm_p)
            fname_low = fname.lower()
            stem = os.path.splitext(fname_low)[0]
            key = f"win_{stem}"
            if key in fonts:
                key = f"win_{fname_low}"

            alias = self.KOREAN_FILENAME_ALIASES.get(fname_low)
            if alias:
                label = f"{alias} [{fname}]"
            else:
                label = f"{disp_name} [{fname}]"

            has_korean = any(ord(ch) > 127 for ch in label) or any(
                tag in fname_low
                for tag in ("gulim", "batang", "malgun", "nanum", "han", "h2", "hm", "seoul", "bareun", "kbiz")
            )
            if has_korean:
                korean_discovered.append((key, label, norm_p))
            else:
                other_discovered.append((key, label, norm_p))

        korean_discovered.sort(key=lambda x: x[1].lower())
        other_discovered.sort(key=lambda x: x[1].lower())

        for key, label, fpath in korean_discovered + other_discovered:
            fonts[key] = {
                "label": label,
                "regular": fpath,
                "bold": None,
                "italic": None,
            }

        return fonts

    def get_available_font_choices(self) -> List[Tuple[str, str]]:
        return [(k, v["label"]) for k, v in self.available_fonts.items()]

    def _match_pdf_font_to_key(self, pdf_font_name: str) -> str:
        low = pdf_font_name.lower()
        compact = low.replace(" ", "").replace("-", "").replace("_", "")

        # 1. 대표 한글/영문 폰트 우선 매칭
        if any(w in low for w in ("gulim", "dotum", "굴림", "돋움")):
            if "새굴림" in low or "ngulim" in low:
                if "win_ngulim" in self.available_fonts:
                    return "win_ngulim"
            if "gulim" in self.available_fonts:
                return "gulim"
        if any(w in low for w in ("hcrbatang", "hanbatang", "함초롬바탕")):
            if "win_hanbatang" in self.available_fonts:
                return "win_hanbatang"
        if any(w in low for w in ("hcrdotum", "handotum", "함초롬돋움")):
            if "win_handotum" in self.available_fonts:
                return "win_handotum"
        if any(w in low for w in ("batang", "myeongjo", "myungjo", "바탕", "명조")):
            if "batang" in self.available_fonts:
                return "batang"
        if any(w in low for w in ("h2mj", "신명조")):
            if "h2mjre" in self.available_fonts:
                return "h2mjre"
            if "batang" in self.available_fonts:
                return "batang"
        if any(w in low for w in ("h2gtr", "중고딕", "견고딕")):
            if "h2gtrm" in self.available_fonts:
                return "h2gtrm"
        if any(w in low for w in ("gungsuh", "궁서", "h2gsr")):
            if "h2gsrb" in self.available_fonts:
                return "h2gsrb"
        if any(w in low for w in ("hmfm", "휴먼")):
            if "hmfmmuex" in self.available_fonts:
                return "hmfmmuex"
        if any(w in low for w in ("nanum", "나눔")):
            if "nanum" in self.available_fonts:
                return "nanum"
        if any(w in low for w in ("malgun", "맑은")):
            if "malgun" in self.available_fonts:
                return "malgun"
        if any(w in low for w in ("times", "roman", "serif")):
            if "times" in self.available_fonts:
                return "times"
        if any(w in low for w in ("arial", "helvetica", "helv", "sans")):
            if "arial" in self.available_fonts:
                return "arial"

        # 2. 전체 윈도우 폰트 목록에서 파일명/표시명 매칭
        if compact:
            for k, info in self.available_fonts.items():
                lbl_compact = (
                    str(info.get("label", ""))
                    .lower()
                    .replace(" ", "")
                    .replace("-", "")
                    .replace("_", "")
                )
                reg_stem = os.path.splitext(
                    os.path.basename(str(info.get("regular", "")))
                )[0].lower()
                if compact in lbl_compact or (reg_stem and reg_stem in compact):
                    return k

        if "gulim" in self.available_fonts:
            return "gulim"
        if "malgun" in self.available_fonts:
            return "malgun"
        return next(iter(self.available_fonts.keys()), "gulim")

    def _resolve_font_path(self, custom_font_path: Optional[str] = None) -> Optional[str]:
        from src.utils.resource_path import get_resource_path

        candidates = []
        if custom_font_path:
            candidates.append(custom_font_path)
        candidates.extend([
            get_resource_path(os.path.join("assets", "fonts", "NanumGothic.ttf")),
            os.path.join("assets", "fonts", "NanumGothic.ttf"),
            "C:/Windows/Fonts/gulim.ttc",
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/batang.ttc",
        ])
        for path in candidates:
            if path and os.path.exists(path):
                return path
        return None

    def _validate_page_num(self, page_num: int) -> bool:
        if self.doc is None:
            return False
        return 0 <= page_num < len(self.doc)

    def _to_fitz_rect(self, rect: Union[fitz.Rect, Tuple[float, float, float, float], list]) -> fitz.Rect:
        if isinstance(rect, fitz.Rect):
            return fitz.Rect(rect).normalize()
        return fitz.Rect(*rect).normalize()

    @property
    def page_count(self) -> int:
        return len(self.doc) if self.doc is not None else 0

    def get_page_origin(self, page_num: int) -> fitz.Point:
        if not self._validate_page_num(page_num):
            return fitz.Point(0, 0)
        return self.doc[page_num].rect.tl

    def get_page_display_size(self, page_num: int, zoom: float = 1.0) -> Tuple[int, int]:
        """픽셀 렌더링 없이 특정 페이지의 화면 표시 크기(width, height)만 빠르게 계산합니다."""
        if not self._validate_page_num(page_num):
            return (595, 842)
        zoom = max(0.1, min(zoom, 10.0))
        rect = self.doc[page_num].rect * fitz.Matrix(zoom, zoom)
        irect = rect.irect
        return (max(1, irect.width), max(1, irect.height))

    def get_all_page_display_sizes(self, zoom: float = 1.0) -> List[Tuple[int, int]]:
        """전체 페이지의 화면 표시 크기(width, height) 리스트를 픽셀 렌더링 없이 즉시 반환합니다."""
        if self.doc is None:
            return []
        return [self.get_page_display_size(i, zoom) for i in range(len(self.doc))]

    # -------------------------------------------------------------------------
    # 1. 문서 열기 및 총 페이지 수 반환
    # -------------------------------------------------------------------------
    def load_document(self, file_path: str) -> int:
        if not file_path or not os.path.exists(file_path):
            print(f"[PdfHandler] 파일이 존재하지 않습니다: {file_path}")
            return 0

        try:
            if self.doc is not None:
                self.doc.close()

            self.doc = fitz.open(file_path)
            if self.doc.is_encrypted and not self.doc.authenticate(""):
                print(f"[PdfHandler] 암호로 보호된 PDF 파일입니다: {file_path}")
                self.doc.close()
                self.doc = None
                return 0

            self.file_path = file_path
            self._state_id = 0
            self._saved_state_id = 0
            self._next_state_seq = 1
            self._undo_stack.clear()
            self._redo_stack.clear()
            return len(self.doc)
        except Exception as e:
            print(f"[PdfHandler] PDF 로드 실패 ({file_path}): {e}")
            self.doc = None
            self.file_path = None
            return 0

    def close_document(self):
        """현재 열려 있는 PDF 문서를 닫고 내부 상태 및 히스토리를 초기화합니다."""
        if self.doc is not None:
            try:
                self.doc.close()
            except Exception:
                pass
        self.doc = None
        self.file_path = None
        self._state_id = 0
        self._saved_state_id = 0
        self._next_state_seq = 1
        self._undo_stack.clear()
        self._redo_stack.clear()

    # -------------------------------------------------------------------------
    # 2. 특정 페이지를 QImage(또는 QPixmap)로 변환하여 반환
    # -------------------------------------------------------------------------
    def get_page_pixmap(
        self, page_num: int, zoom: float = 1.0, as_qpixmap: bool = False
    ) -> Optional[Union[QImage, QPixmap]]:
        if not self._validate_page_num(page_num):
            return None

        try:
            zoom = max(0.1, min(zoom, 10.0))
            page = self.doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            qimage = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888,
            ).copy()

            if as_qpixmap:
                return QPixmap.fromImage(qimage)
            return qimage
        except Exception as e:
            print(f"[PdfHandler] 페이지 렌더링 오류 (page={page_num}): {e}")
            return None

    # -------------------------------------------------------------------------
    # 3. 텍스트 정보 감지 및 Redact & 새 텍스트 삽입
    # -------------------------------------------------------------------------
    def inspect_text_at_rect(self, page_num: int, pdf_rect: fitz.Rect) -> TextStyleInfo:
        if not self._validate_page_num(page_num):
            return TextStyleInfo(rect=pdf_rect)

        page = self.doc[page_num]
        is_click = pdf_rect.width < 5 or pdf_rect.height < 5
        center = fitz.Point(
            (pdf_rect.x0 + pdf_rect.x1) / 2.0,
            (pdf_rect.y0 + pdf_rect.y1) / 2.0,
        )

        target_rect = fitz.Rect(pdf_rect)
        detected_text = ""

        if is_click:
            words = page.get_text("words")
            for w in words:
                w_rect = fitz.Rect(w[:4])
                if w_rect.contains(center):
                    target_rect = w_rect
                    detected_text = str(w[4]).strip()
                    break
            if not detected_text:
                target_rect = fitz.Rect(center.x, center.y - 9, center.x + 100, center.y + 4) & page.rect
        else:
            detected_text = page.get_text("text", clip=target_rect).strip()

        raw_font = "Gulim"
        clean_font = "Gulim"
        font_size = 10.0
        is_bold = False
        is_italic = False
        color_rgb = (0.0, 0.0, 0.0)
        baseline_y: Optional[float] = None

        best_overlap = -1.0
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    s_bbox = fitz.Rect(span.get("bbox", (0, 0, 0, 0)))
                    if is_click and s_bbox.contains(center):
                        overlap = 999999.0
                    else:
                        inter = s_bbox & target_rect
                        overlap = inter.get_area() if not inter.is_empty else 0.0

                    if overlap > best_overlap and overlap > 0:
                        best_overlap = overlap
                        raw_font = str(span.get("font", "Gulim"))
                        clean_font = raw_font.split("+")[-1] if "+" in raw_font else raw_font

                        raw_size = float(span.get("size", 10.0))
                        if raw_size < 4.0 and s_bbox.height > 4.0:
                            font_size = round(s_bbox.height * 0.85, 1)
                        else:
                            font_size = round(raw_size, 1)

                        flags = int(span.get("flags", 0))
                        font_lower = clean_font.lower()
                        is_bold = bool(flags & 16) or any(
                            b in font_lower for b in ("bold", "bd", "heavy", "black")
                        )
                        is_italic = bool(flags & 2) or any(
                            i in font_lower for i in ("italic", "oblique", "slanted")
                        )

                        c_int = int(span.get("color", 0))
                        r = ((c_int >> 16) & 255) / 255.0
                        g = ((c_int >> 8) & 255) / 255.0
                        b = (c_int & 255) / 255.0
                        color_rgb = (r, g, b)

                        origin = span.get("origin")
                        if origin and len(origin) == 2:
                            baseline_y = float(origin[1])

                        if not detected_text:
                            detected_text = str(span.get("text", "")).strip()

        matched_key = self._match_pdf_font_to_key(clean_font)

        return TextStyleInfo(
            rect=target_rect,
            text=detected_text,
            raw_font_name=raw_font,
            clean_font_name=clean_font,
            matched_font_key=matched_key,
            font_size=font_size,
            is_bold=is_bold,
            is_italic=is_italic,
            color=color_rgb,
            baseline_y=baseline_y,
        )

    def replace_rect_area_styled(
        self,
        page_num: int,
        style_info: TextStyleInfo,
        new_text: str,
        font_key: str,
        font_size: float,
        is_bold: bool = False,
        is_italic: bool = False,
        text_color: Optional[Tuple[float, float, float]] = None,
        y_offset: float = 0.0,
    ) -> bool:
        if not self._validate_page_num(page_num):
            return False

        try:
            target_rect = self._to_fitz_rect(style_info.rect)
            if target_rect.is_empty or target_rect.is_infinite:
                return False

            self._push_undo_snapshot()
            page = self.doc[page_num]

            redact_rect = fitz.Rect(
                target_rect.x0 + 0.2,
                target_rect.y0 + 0.4,
                target_rect.x1 - 0.2,
                target_rect.y1 - 0.4,
            )
            if redact_rect.is_empty or redact_rect.width < 1 or redact_rect.height < 1:
                redact_rect = target_rect

            page.add_redact_annot(redact_rect, fill=(1.0, 1.0, 1.0))
            page.apply_redactions()

            if new_text:
                use_color = (
                    text_color if text_color is not None else style_info.color
                )
                self._write_styled_text(
                    page=page,
                    target_rect=target_rect,
                    baseline_y=style_info.baseline_y,
                    new_text=new_text,
                    font_key=font_key,
                    font_size=font_size,
                    is_bold=is_bold,
                    is_italic=is_italic,
                    color=use_color,
                    y_offset=y_offset,
                )

            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 스타일 텍스트 치환 오류 (page={page_num}): {e}")
            return False

    def _write_styled_text(
        self,
        page: fitz.Page,
        target_rect: fitz.Rect,
        baseline_y: Optional[float],
        new_text: str,
        font_key: str,
        font_size: float,
        is_bold: bool,
        is_italic: bool,
        color: Tuple[float, float, float],
        y_offset: float = 0.0,
    ):
        font_info = self.available_fonts.get(font_key)
        font_file = None
        used_native_bold = False
        used_native_italic = False

        if font_info:
            if is_bold and font_info.get("bold"):
                font_file = font_info["bold"]
                used_native_bold = True
            elif is_italic and font_info.get("italic"):
                font_file = font_info["italic"]
                used_native_italic = True
            else:
                font_file = font_info.get("regular")

        if not font_file:
            font_file = self.font_path

        try:
            font_obj = fitz.Font(fontfile=font_file) if font_file else fitz.Font("helv")
        except Exception:
            font_obj = (
                fitz.Font(fontfile=self.font_path)
                if self.font_path
                else fitz.Font("helv")
            )

        if baseline_y is not None:
            base_y = baseline_y + y_offset
        else:
            base_y = target_rect.y1 - (target_rect.height * 0.15) + y_offset

        insert_pt = fitz.Point(target_rect.x0, base_y)

        tw = fitz.TextWriter(page.rect)
        lines = new_text.splitlines() or [new_text]
        line_spacing = font_size * 1.25

        for idx, line_str in enumerate(lines):
            pt = fitz.Point(insert_pt.x, insert_pt.y + (idx * line_spacing))
            tw.append(pt, line_str, font=font_obj, fontsize=font_size)
            if is_bold and not used_native_bold:
                bold_offset = max(0.35, font_size * 0.035)
                tw.append(
                    fitz.Point(pt.x + bold_offset, pt.y),
                    line_str,
                    font=font_obj,
                    fontsize=font_size,
                )

        morph = None
        if is_italic and not used_native_italic:
            shear_matrix = fitz.Matrix(1.0, 0.0, 0.20, 1.0, 0.0, 0.0)
            morph = (insert_pt, shear_matrix)

        tw.write_text(page, color=color, morph=morph)

    def replace_text(
        self,
        page_num: int,
        target_text: str,
        new_text: str,
        font_size: float = 10.0,
    ) -> int:
        if not self._validate_page_num(page_num) or not target_text:
            return 0

        try:
            page = self.doc[page_num]
            found_rects = page.search_for(target_text)
            if not found_rects:
                return 0

            self._push_undo_snapshot()
            styles = [self.inspect_text_at_rect(page_num, r) for r in found_rects]

            for r in found_rects:
                page.add_redact_annot(r, fill=(1.0, 1.0, 1.0))
            page.apply_redactions()

            if new_text:
                for st in styles:
                    use_size = font_size if font_size > 0 else st.font_size
                    self._write_styled_text(
                        page=page,
                        target_rect=st.rect,
                        baseline_y=st.baseline_y,
                        new_text=new_text,
                        font_key=st.matched_font_key,
                        font_size=use_size,
                        is_bold=st.is_bold,
                        is_italic=st.is_italic,
                        color=st.color,
                    )

            self._advance_state()
            return len(found_rects)
        except Exception as e:
            print(f"[PdfHandler] 텍스트 교체 오류 (page={page_num}): {e}")
            return 0

    # -------------------------------------------------------------------------
    # 4. 지정된 사각 영역 텍스트 하이라이트 주석 추가
    # -------------------------------------------------------------------------
    def add_highlight(
        self,
        page_num: int,
        rect: Union[fitz.Rect, Tuple[float, float, float, float]],
        color: Tuple[float, float, float] = (1.0, 0.95, 0.0),
    ) -> bool:
        if not self._validate_page_num(page_num):
            return False

        try:
            target_rect = self._to_fitz_rect(rect)
            if target_rect.is_empty or target_rect.is_infinite:
                return False

            self._push_undo_snapshot()
            page = self.doc[page_num]

            words = page.get_text("words", clip=target_rect)
            if words:
                quads = [fitz.Rect(w[:4]).quad for w in words]
                annot = page.add_highlight_annot(quads)
            else:
                annot = page.add_highlight_annot(target_rect)

            annot.set_colors(stroke=color)
            annot.update()
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 하이라이트 추가 오류 (page={page_num}): {e}")
            return False

    # -------------------------------------------------------------------------
    # 5. 검토용 사각형 박스(Red Box) 주석 추가
    # -------------------------------------------------------------------------
    def add_box_annotation(
        self,
        page_num: int,
        rect: Union[fitz.Rect, Tuple[float, float, float, float]],
        color: Tuple[float, float, float] = (1, 0, 0),
        width: float = 2.0,
    ) -> bool:
        if not self._validate_page_num(page_num):
            return False

        try:
            target_rect = self._to_fitz_rect(rect)
            if target_rect.is_empty or target_rect.is_infinite:
                return False

            self._push_undo_snapshot()
            page = self.doc[page_num]

            annot = page.add_rect_annot(target_rect)
            annot.set_colors(stroke=color)
            annot.set_border(width=max(0.5, float(width)))
            annot.update()
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 박스 주석 추가 오류 (page={page_num}): {e}")
            return False

    # -------------------------------------------------------------------------
    # 5-2. 클라우드 마크(Revision Cloud) 다각형 주석 추가
    # -------------------------------------------------------------------------
    def add_cloud_polygon_annotation(
        self,
        page_num: int,
        points: List[Union[fitz.Point, Tuple[float, float]]],
        color: Tuple[float, float, float] = (0.93, 0.2, 0.2),
        cloud_scale: float = 2.5,
        width: float = 2.2,
    ) -> bool:
        """
        다중 클릭으로 지정된 다각형 꼭짓점(points, 최소 3점)을 따라
        바깥쪽으로 볼록하게 부풀어 오른 구름 모양(Revision Cloud) 마크를 생성합니다.
        기본 MuPDF 구름(chord ~9.5pt) 대비 약 2.5배 크기(chord ~24pt)로 선명하게 렌더링됩니다.
        """
        if not self._validate_page_num(page_num) or len(points) < 3:
            return False

        try:
            fitz_pts: List[fitz.Point] = []
            for pt in points:
                if isinstance(pt, fitz.Point):
                    p = pt
                else:
                    p = fitz.Point(float(pt[0]), float(pt[1]))
                if not fitz_pts or math.hypot(p.x - fitz_pts[-1].x, p.y - fitz_pts[-1].y) > 1.0:
                    fitz_pts.append(p)

            if len(fitz_pts) > 2 and math.hypot(fitz_pts[0].x - fitz_pts[-1].x, fitz_pts[0].y - fitz_pts[-1].y) <= 1.0:
                fitz_pts.pop()

            if len(fitz_pts) < 3:
                return False

            # 다각형의 부호 있는 면적(Signed Area) 계산 (PDF 화면 좌표계: Y축 아래 방향 증가)
            # signed_area > 0 이면 시계 방향(CW)이므로 바깥쪽 법선은 (ty, -tx)
            signed_area = 0.0
            n_pts = len(fitz_pts)
            for i in range(n_pts):
                p1 = fitz_pts[i]
                p2 = fitz_pts[(i + 1) % n_pts]
                signed_area += p1.x * p2.y - p2.x * p1.y

            if signed_area < 0:
                fitz_pts.reverse()

            self._push_undo_snapshot()
            page = self.doc[page_num]
            shape = page.new_shape()

            # 기본 MuPDF 구름 아크 폭(~9.5pt)의 약 2.5배인 24.0pt 기준
            scale_val = max(0.5, float(cloud_scale))
            target_chord = 9.6 * scale_val
            max_bulge = 7.6 * scale_val
            min_bulge = 4.0 * scale_val

            n_pts = len(fitz_pts)
            for i in range(n_pts):
                p1 = fitz_pts[i]
                p2 = fitz_pts[(i + 1) % n_pts]
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                edge_len = math.hypot(dx, dy)
                if edge_len < 1e-3:
                    continue

                tx = dx / edge_len
                ty = dy / edge_len
                # 시계 방향(CW) 다각형 기준 바깥쪽 단위 법선 벡터
                nx = ty
                ny = -tx

                num_arcs = max(1, round(edge_len / target_chord))
                chord = edge_len / num_arcs
                # 바깥쪽으로 부풀어 오르는 구름 볼록 높이
                bulge_h = min(max_bulge, max(min_bulge, chord * 0.75))

                for k in range(num_arcs):
                    a = fitz.Point(p1.x + dx * (k / num_arcs), p1.y + dy * (k / num_arcs))
                    b = fitz.Point(p1.x + dx * ((k + 1) / num_arcs), p1.y + dy * ((k + 1) / num_arcs))
                    # 3차 베지어 제어점: 바깥쪽 법선 방향으로 아크를 풍성하게 확장
                    c1 = fitz.Point(
                        a.x + tx * (chord * 0.12) + nx * bulge_h,
                        a.y + ty * (chord * 0.12) + ny * bulge_h,
                    )
                    c2 = fitz.Point(
                        b.x - tx * (chord * 0.12) + nx * bulge_h,
                        b.y - ty * (chord * 0.12) + ny * bulge_h,
                    )
                    shape.draw_bezier(a, c1, c2, b)

            shape.finish(
                color=color,
                fill=None,
                width=max(0.5, float(width)),
                lineJoin=1,
                lineCap=1,
                closePath=False,
            )
            shape.commit()
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 클라우드 마크 추가 오류 (page={page_num}): {e}")
            return False

    # -------------------------------------------------------------------------
    # 5-3. 당초/변경 마크 (사각형 테두리 + 내부 중앙 텍스트) 추가
    # -------------------------------------------------------------------------
    def _draw_stamp_mark_on_page(
        self,
        page: fitz.Page,
        stamp_text: str = "당초",
        box_width: float = 72.0,
        box_height: float = 32.0,
        border_color: Tuple[float, float, float] = (0.90, 0.08, 0.08),
        border_width: float = 2.5,
        font_key: str = "malgun",
        font_size: float = 15.0,
        is_bold: bool = True,
        top_margin_pt: float = 24.0,
        right_margin_pt: float = 28.0,
        custom_rect: Optional[fitz.Rect] = None,
    ):
        p_rect = page.rect
        bw = max(24.0, float(box_width))
        bh = max(16.0, float(box_height))

        if custom_rect is not None and not custom_rect.is_empty:
            box_rect = custom_rect
        else:
            x1 = p_rect.x1 - float(right_margin_pt)
            x0 = x1 - bw
            y0 = p_rect.y0 + float(top_margin_pt)
            y1 = y0 + bh
            box_rect = fitz.Rect(x0, y0, x1, y1)

        # 1) 사각형 테두리 그리기
        shape = page.new_shape()
        shape.draw_rect(box_rect)
        shape.finish(
            color=border_color,
            fill=None,
            width=max(0.5, float(border_width)),
            lineJoin=0,
            lineCap=0,
        )
        shape.commit()

        # 2) 내부 중앙에 '당초' / '변경' 텍스트 그리기
        clean_label = (stamp_text or "당초").strip()
        if not clean_label:
            clean_label = "당초"

        font_info = self.available_fonts.get(font_key)
        font_file = None
        used_native_bold = False
        if font_info:
            if is_bold and font_info.get("bold"):
                font_file = font_info["bold"]
                used_native_bold = True
            else:
                font_file = font_info.get("regular")
        if not font_file:
            font_file = self.font_path

        try:
            font_obj = fitz.Font(fontfile=font_file) if font_file else fitz.Font("helv")
        except Exception:
            font_obj = (
                fitz.Font(fontfile=self.font_path)
                if self.font_path
                else fitz.Font("helv")
            )

        fsize = max(6.0, float(font_size))
        try:
            text_w = font_obj.text_length(clean_label, fontsize=fsize)
        except Exception:
            text_w = fsize * len(clean_label)

        tx = box_rect.x0 + (box_rect.width - text_w) / 2.0
        ty = box_rect.y0 + (box_rect.height / 2.0) + (fsize * 0.36)

        tw = fitz.TextWriter(p_rect)
        tw.append(fitz.Point(tx, ty), clean_label, font=font_obj, fontsize=fsize)
        if is_bold and not used_native_bold:
            bold_offset = max(0.4, fsize * 0.04)
            tw.append(
                fitz.Point(tx + bold_offset, ty),
                clean_label,
                font=font_obj,
                fontsize=fsize,
            )
        tw.write_text(page, color=border_color)

    def add_stamp_mark_annotation(
        self,
        page_num: int,
        stamp_text: str = "당초",
        box_width: float = 72.0,
        box_height: float = 32.0,
        border_color: Tuple[float, float, float] = (0.90, 0.08, 0.08),
        border_width: float = 2.5,
        font_key: str = "malgun",
        font_size: float = 15.0,
        is_bold: bool = True,
        top_margin_pt: float = 24.0,
        right_margin_pt: float = 28.0,
        custom_rect: Optional[fitz.Rect] = None,
    ) -> bool:
        """단일 페이지 우측 상단(또는 지정 영역)에 당초/변경 마크를 추가합니다. (Undo/Redo 지원)"""
        if not self._validate_page_num(page_num):
            return False
        try:
            self._push_undo_snapshot()
            page = self.doc[page_num]
            self._draw_stamp_mark_on_page(
                page=page,
                stamp_text=stamp_text,
                box_width=box_width,
                box_height=box_height,
                border_color=border_color,
                border_width=border_width,
                font_key=font_key,
                font_size=font_size,
                is_bold=is_bold,
                top_margin_pt=top_margin_pt,
                right_margin_pt=right_margin_pt,
                custom_rect=custom_rect,
            )
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 당초/변경 마크 추가 오류 (page={page_num}): {e}")
            return False

    def apply_stamp_marks_by_page(
        self,
        page_stamp_map: Dict[int, str],
        box_width: float = 72.0,
        box_height: float = 32.0,
        border_color: Tuple[float, float, float] = (0.90, 0.08, 0.08),
        border_width: float = 2.5,
        font_key: str = "malgun",
        font_size: float = 15.0,
        is_bold: bool = True,
        top_margin_pt: float = 24.0,
        right_margin_pt: float = 28.0,
    ) -> List[int]:
        """
        페이지별로 지정된 당초/변경 마크(page_stamp_map: {page_idx: '당초'|'변경'})를
        각 페이지 우측 상단에 일괄 삽입합니다. (Undo/Redo 1단계 스냅샷 지원)
        """
        if self.doc is None or not page_stamp_map:
            return []

        valid_items = [
            (int(p), str(lbl).strip())
            for p, lbl in sorted(page_stamp_map.items())
            if self._validate_page_num(int(p)) and str(lbl).strip()
        ]
        if not valid_items:
            return []

        try:
            self._push_undo_snapshot()
            modified_pages: List[int] = []
            for page_idx, lbl in valid_items:
                page = self.doc[page_idx]
                self._draw_stamp_mark_on_page(
                    page=page,
                    stamp_text=lbl,
                    box_width=box_width,
                    box_height=box_height,
                    border_color=border_color,
                    border_width=border_width,
                    font_key=font_key,
                    font_size=font_size,
                    is_bold=is_bold,
                    top_margin_pt=top_margin_pt,
                    right_margin_pt=right_margin_pt,
                )
                modified_pages.append(page_idx)
            self._advance_state()
            return modified_pages
        except Exception as e:
            print(f"[PdfHandler] 페이지별 당초/변경 마크 일괄 적용 오류: {e}")
            return []

    # -------------------------------------------------------------------------
    # 6. 페이지 관리 (삭제, 회전, 드래그앤드롭 슬롯 이동, 추출 저장)
    # -------------------------------------------------------------------------
    def manage_page(self, action: str, page_num: int, **kwargs) -> bool:
        if not self._validate_page_num(page_num):
            return False

        try:
            action = action.lower().strip()

            if action == "delete":
                if len(self.doc) <= 1:
                    print("[PdfHandler] 마지막 남은 1페이지는 삭제할 수 없습니다.")
                    return False
                self._push_undo_snapshot()
                self.doc.delete_page(page_num)
                self._advance_state()
                return True

            elif action == "rotate":
                angle = int(kwargs.get("angle", 90))
                self._push_undo_snapshot()
                page = self.doc[page_num]
                new_rotation = (page.rotation + angle) % 360
                page.set_rotation(new_rotation)
                self._advance_state()
                return True

            elif action == "move":
                to_index = kwargs.get("to_page", kwargs.get("target_index", None))
                if to_index is None or not self._validate_page_num(int(to_index)):
                    return False
                to_index = int(to_index)
                if page_num == to_index:
                    return False

                self._push_undo_snapshot()
                if page_num < to_index:
                    if to_index + 1 < len(self.doc):
                        self.doc.move_page(page_num, to_index + 1)
                    else:
                        self.doc.move_page(page_num, -1)
                else:
                    self.doc.move_page(page_num, to_index)

                self._advance_state()
                return True

            else:
                print(f"[PdfHandler] 지원하지 않는 action입니다: {action}")
                return False

        except Exception as e:
            print(f"[PdfHandler] 페이지 관리 오류 (action={action}, page={page_num}): {e}")
            return False

    def compute_reordered_pages(
        self, selected_indices: List[int], insert_before_index: int
    ) -> Tuple[List[int], List[int]]:
        """
        선택된 페이지들(selected_indices)을 insert_before_index(0 ~ page_count) 슬롯에 넣었을 때의
        (전체 새 페이지 순서 리스트, 이동된 페이지들의 새 인덱스 리스트)를 계산합니다.
        """
        if self.doc is None:
            return [], []
        total = len(self.doc)
        all_pages = list(range(total))
        moving = [p for p in sorted(set(selected_indices)) if 0 <= p < total]
        if not moving:
            return all_pages, []

        slot = max(0, min(total, insert_before_index))
        before = [p for p in all_pages[:slot] if p not in moving]
        after = [p for p in all_pages[slot:] if p not in moving]
        new_order = before + moving + after
        new_selected_positions = list(range(len(before), len(before) + len(moving)))
        return new_order, new_selected_positions

    def would_move_change_order(
        self, selected_indices: List[int], insert_before_index: int
    ) -> bool:
        """드래그 앤 드롭한 위치가 실제 페이지 순서를 바꾸는지 여부를 확인합니다."""
        if self.doc is None:
            return False
        new_order, _ = self.compute_reordered_pages(selected_indices, insert_before_index)
        return new_order != list(range(len(self.doc)))

    def move_pages_to_slot(
        self, selected_indices: List[int], insert_before_index: int
    ) -> Optional[List[int]]:
        """
        선택된 페이지들을 insert_before_index 위치로 실제 이동시키고,
        이동 후 해당 페이지들이 위치한 새로운 0-based 인덱스 리스트를 반환합니다.
        """
        if self.doc is None:
            return None

        new_order, new_positions = self.compute_reordered_pages(
            selected_indices, insert_before_index
        )
        if not new_order or new_order == list(range(len(self.doc))):
            return None

        try:
            self._push_undo_snapshot()
            self.doc.select(new_order)
            self._advance_state()
            return new_positions
        except Exception as e:
            print(f"[PdfHandler] 드래그 앤 드롭 페이지 이동 오류: {e}")
            return None

    def rotate_pages(self, page_indices: List[int], angle: int = 90) -> bool:
        if self.doc is None or not page_indices:
            return False
        valid = [p for p in sorted(set(page_indices)) if self._validate_page_num(p)]
        if not valid:
            return False
        try:
            self._push_undo_snapshot()
            for p in valid:
                page = self.doc[p]
                page.set_rotation((page.rotation + angle) % 360)
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 다중 페이지 회전 오류: {e}")
            return False

    def delete_pages(self, page_indices: List[int]) -> bool:
        if self.doc is None or not page_indices:
            return False
        valid = [p for p in sorted(set(page_indices), reverse=True) if self._validate_page_num(p)]
        if not valid or len(self.doc) - len(valid) < 1:
            return False
        try:
            self._push_undo_snapshot()
            for p in valid:
                self.doc.delete_page(p)
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 다중 페이지 삭제 오류: {e}")
            return False

    def extract_pages(self, page_indices: List[int], output_path: str) -> bool:
        if self.doc is None or not page_indices or not output_path:
            return False

        valid_pages = [p for p in sorted(set(page_indices)) if self._validate_page_num(p)]
        if not valid_pages:
            return False

        new_doc = None
        try:
            new_doc = fitz.open()
            for p in valid_pages:
                new_doc.insert_pdf(self.doc, from_page=p, to_page=p)

            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()
            return True
        except Exception as e:
            print(f"[PdfHandler] 페이지 추출 저장 실패 ({output_path}): {e}")
            if new_doc is not None:
                new_doc.close()
            return False

    @staticmethod
    def inspect_external_pdf(
        file_path: str, thumb_zoom: float = 0.2
    ) -> Tuple[int, List[QPixmap]]:
        """
        합병할 외부 PDF 파일을 열어 총 페이지 수와 미리보기 썸네일(QPixmap 리스트)을 반환합니다.
        파일을 열 수 없거나 암호화된 경우 (0, [])를 반환합니다.
        """
        if not file_path or not os.path.exists(file_path):
            return 0, []

        ext_doc = None
        try:
            ext_doc = fitz.open(file_path)
            if ext_doc.is_encrypted and not ext_doc.authenticate(""):
                ext_doc.close()
                return 0, []

            total = len(ext_doc)
            thumbs: List[QPixmap] = []
            mat = fitz.Matrix(thumb_zoom, thumb_zoom)
            for idx in range(total):
                page = ext_doc[idx]
                pix = page.get_pixmap(matrix=mat, alpha=False)
                qimg = QImage(
                    pix.samples,
                    pix.width,
                    pix.height,
                    pix.stride,
                    QImage.Format.Format_RGB888,
                ).copy()
                thumbs.append(QPixmap.fromImage(qimg))

            ext_doc.close()
            return total, thumbs
        except Exception as e:
            print(f"[PdfHandler] 외부 PDF 미리보기 로드 실패 ({file_path}): {e}")
            if ext_doc is not None:
                ext_doc.close()
            return 0, []

    def merge_pages_from_file(
        self,
        source_pdf_path: str,
        source_page_indices: List[int],
        insert_before_index: int,
    ) -> Optional[List[int]]:
        """
        외부 PDF 파일(source_pdf_path)에서 지정한 0-based 페이지들(source_page_indices)을 가져와
        현재 문서의 insert_before_index(0 ~ page_count) 슬롯 위치에 합병(삽입)합니다.
        성공 시 현재 문서 내에서 새로 삽입된 페이지들의 0-based 인덱스 리스트를 반환합니다.
        """
        if not source_pdf_path or not os.path.exists(source_pdf_path):
            return None

        src_doc = None
        try:
            src_doc = fitz.open(source_pdf_path)
            if src_doc.is_encrypted and not src_doc.authenticate(""):
                src_doc.close()
                return None

            src_total = len(src_doc)
            valid_src_pages = [
                p for p in source_page_indices if 0 <= p < src_total
            ]
            if not valid_src_pages:
                src_doc.close()
                return None

            # 현재 열려있는 문서가 없는 경우: 새 문서를 생성하여 합병 페이지들로 구성
            if self.doc is None or len(self.doc) == 0:
                if self.doc is not None:
                    self.doc.close()
                self.doc = fitz.open()
                for p in valid_src_pages:
                    self.doc.insert_pdf(src_doc, from_page=p, to_page=p)
                src_doc.close()
                self.file_path = source_pdf_path
                self._undo_stack.clear()
                self._redo_stack.clear()
                self._state_id = 1
                self._saved_state_id = 0
                return list(range(len(valid_src_pages)))

            # 기존 문서가 열려있는 경우: Undo 스냅샷 저장 후 지정 슬롯에 삽입
            self._push_undo_snapshot()
            cur_total = len(self.doc)
            slot = max(0, min(cur_total, insert_before_index))

            for offset, src_page in enumerate(valid_src_pages):
                target_pos = slot + offset
                start_at = target_pos if target_pos < len(self.doc) else -1
                self.doc.insert_pdf(
                    src_doc,
                    from_page=src_page,
                    to_page=src_page,
                    start_at=start_at,
                )

            src_doc.close()
            self._advance_state()
            return list(range(slot, slot + len(valid_src_pages)))

        except Exception as e:
            print(f"[PdfHandler] 외부 PDF 페이지 합병 오류 ({source_pdf_path}): {e}")
            if src_doc is not None:
                src_doc.close()
            return None

    # -------------------------------------------------------------------------
    # 7. 책갈피(Bookmark / TOC) 조회, 추가, 삭제
    # -------------------------------------------------------------------------
    def get_bookmarks(self) -> List[Tuple[int, str, int]]:
        if self.doc is None:
            return []
        try:
            toc = self.doc.get_toc(simple=True)
            result: List[Tuple[int, str, int]] = []
            for entry in toc:
                if len(entry) >= 3:
                    level = int(entry[0])
                    title = str(entry[1]).strip() or "제목 없음"
                    page_0 = max(0, min(len(self.doc) - 1, int(entry[2]) - 1))
                    result.append((level, title, page_0))
            return result
        except Exception as e:
            print(f"[PdfHandler] 책갈피 로드 오류: {e}")
            return []

    def add_bookmark(self, title: str, page_num: int, level: int = 1) -> bool:
        if not self._validate_page_num(page_num) or not title.strip():
            return False
        try:
            self._push_undo_snapshot()
            toc = self.doc.get_toc(simple=True)
            toc.append([max(1, level), title.strip(), page_num + 1])
            self.doc.set_toc(toc)
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 책갈피 추가 오류: {e}")
            return False

    def remove_bookmark(self, bookmark_index: int) -> bool:
        if self.doc is None:
            return False
        try:
            toc = self.doc.get_toc(simple=True)
            if not (0 <= bookmark_index < len(toc)):
                return False
            self._push_undo_snapshot()
            toc.pop(bookmark_index)
            self.doc.set_toc(toc)
            self._advance_state()
            return True
        except Exception as e:
            print(f"[PdfHandler] 책갈피 삭제 오류: {e}")
            return False

    # -------------------------------------------------------------------------
    # 7-2. 쪽번호 넣기 (형식: -1-, 시작 페이지 지정, 하단 좌/중/우 및 상/하 위치 조정)
    # -------------------------------------------------------------------------
    def insert_page_numbers(
        self,
        start_page_index: int = 0,
        end_page_index: Optional[int] = None,
        start_number: int = 1,
        alignment: str = "center",
        bottom_offset_pt: float = 28.0,
        horizontal_margin_pt: float = 42.0,
        font_size: float = 10.5,
        format_template: str = "-{n}-",
    ) -> List[int]:
        """
        지정한 시작 페이지부터 끝 페이지까지 하단(좌측/중앙/우측) 및 지정한 상·하 오프셋 위치에
        '-1-' 형식의 쪽번호를 일괄 삽입합니다. (Undo/Redo 10단계 스냅샷 지원)
        """
        if self.doc is None or len(self.doc) == 0:
            return []

        total = len(self.doc)
        s_idx = max(0, min(total - 1, int(start_page_index)))
        e_idx = (
            total - 1
            if end_page_index is None
            else max(s_idx, min(total - 1, int(end_page_index)))
        )

        try:
            self._push_undo_snapshot()
            modified_pages: List[int] = []

            for offset, page_idx in enumerate(range(s_idx, e_idx + 1)):
                page = self.doc[page_idx]
                rect = page.rect
                page_num_val = int(start_number) + offset
                text = format_template.format(n=page_num_val)

                text_w = fitz.get_text_length(
                    text, fontname="helv", fontsize=float(font_size)
                )

                if alignment == "left":
                    x = rect.x0 + float(horizontal_margin_pt)
                elif alignment == "right":
                    x = rect.x1 - float(horizontal_margin_pt) - text_w
                else:
                    x = rect.x0 + (rect.width - text_w) / 2.0

                baseline_y = rect.y1 - float(bottom_offset_pt)
                baseline_y = max(
                    rect.y0 + float(font_size) + 4.0,
                    min(rect.y1 - 4.0, baseline_y),
                )

                page.insert_text(
                    fitz.Point(x, baseline_y),
                    text,
                    fontsize=float(font_size),
                    fontname="helv",
                    color=(0.0, 0.0, 0.0),
                )
                modified_pages.append(page_idx)

            self._advance_state()
            return modified_pages
        except Exception as e:
            print(f"[PdfHandler] 쪽번호 삽입 오류: {e}")
            return []

    # -------------------------------------------------------------------------
    # 8. 변경된 문서 저장
    # -------------------------------------------------------------------------
    def save_document(self, output_path: str) -> bool:
        if self.doc is None or not output_path:
            return False

        try:
            if self.file_path and os.path.abspath(output_path) == os.path.abspath(self.file_path):
                temp_path = output_path + ".tmp"
                self.doc.save(temp_path, garbage=4, deflate=True)
                self.doc.close()
                os.replace(temp_path, output_path)
                self.doc = fitz.open(output_path)
            else:
                self.doc.save(output_path, garbage=4, deflate=True)
                self.file_path = output_path

            self._saved_state_id = self._state_id
            return True
        except Exception as e:
            print(f"[PdfHandler] 문서 저장 실패 ({output_path}): {e}")
            return False
