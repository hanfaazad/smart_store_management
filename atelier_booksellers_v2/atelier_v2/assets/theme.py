"""
theme.py  ·  Andalus Booksellers design system
Exact spec tokens + smart cross-platform font resolver.
"""

import sys
import os

# ── PALETTE ───────────────────────────────────────────────────────────────────
BG           = "#F7F4ED"   # Ivory canvas
FG           = "#19241F"   # Forest ink
CARD         = "#FBF8F1"   # Warm card surface
PRIMARY      = "#1E3D2F"   # Deep forest
PRIMARY_H    = "#345C48"   # Hover glow
SECONDARY    = "#F3F0E8"   # Parchment inputs/pills
MUTED        = "#F8F5EE"   # Subtle bg
FG_MUTED     = "#5A6862"   # Caption text
ACCENT       = "#C99A3D"   # Gold
DESTRUCTIVE  = "#B83D2E"   # Burgundy
BORDER       = "#DCD5C5"
SIDEBAR      = "#172F24"   # Left nav
SIDEBAR_FG   = "#E5DDC9"   # Nav label text
SIDEBAR_SUB  = "#7A9E8A"   # Nav section label
SIDEBAR_ACT  = "#1E3D2F"   # Active row bg
WHITE        = "#FFFFFF"
GENRE_MUTED  = "#8A7E6B"   # Subtle warm gray instead of bright gold
STOCK_THRESHOLD = 4

# Derived
ACCENT_TINT  = "#F5EDD6"   # Gold light tint
DESTRUCTIVE_TINT = "#FDECEA"
DESTRUCTIVE_BORDER = "#F5C6C0"
SUCCESS_TINT = "#E4F0E8"
SUCCESS_FG   = "#1E3D2F"
CARD_HOVER   = "#FCFAF5"

# ── RADIUS ────────────────────────────────────────────────────────────────────
R_XS   = 4
R_SM   = 6
R_MD   = 10
R_LG   = 14
R_PILL = 999

# ── SPACING ───────────────────────────────────────────────────────────────────
SP_1  = 4
SP_2  = 8
SP_3  = 12
SP_4  = 16
SP_5  = 20
SP_6  = 24
SP_8  = 32
SP_10 = 40

# ── LAYOUT ────────────────────────────────────────────────────────────────────
SIDEBAR_W = 256
CART_W    = 292
HEADER_H  = 68

# ── SHADOWS (spec-exact) ──────────────────────────────────────────────────────
SHADOW_SM  = (8,  (0, 2),  "#19241F14")
SHADOW_MD  = (20, (0, 6),  "#19241F12")
SHADOW_LG  = (40, (0, 10), "#1E3D2F26")
SHADOW_GOLD= (24, (0, 8),  "#C99A3D59")

# ── FONT SIZES (pt) ───────────────────────────────────────────────────────────
F_XS   = 8
F_SM   = 9
F_BASE = 10
F_MD   = 11
F_LG   = 13
F_XL   = 15
F_2XL  = 18
F_3XL  = 22
F_4XL  = 28

# ── FONT FAMILIES ─────────────────────────────────────────────────────────────
def _resolve_fonts():
    """
    Pick the best available serif + sans-serif on this machine.
    Priority order per platform. Falls back gracefully — never crashes.
    """
    try:
        from PyQt5.QtGui import QFontDatabase
        from PyQt5.QtWidgets import QApplication
        import sys
        if not QApplication.instance():
            _app = QApplication(sys.argv)
        db = QFontDatabase()
        available = set(db.families())

        # Check if custom fonts were registered from /fonts dir
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
        if os.path.isdir(fonts_dir):
            for fn in os.listdir(fonts_dir):
                if fn.lower().endswith((".ttf", ".otf")):
                    fid = db.addApplicationFont(os.path.join(fonts_dir, fn))
                    if fid >= 0:
                        for fam in db.applicationFontFamilies(fid):
                            available.add(fam)

        SERIF_CANDIDATES = [
            "Playfair Display", "Palatino Linotype", "Palatino",
            "Book Antiqua", "Georgia", "Times New Roman",
        ]
        SANS_CANDIDATES = [
            "Inter", "Segoe UI", "SF Pro Display", "Helvetica Neue",
            "Calibri", "Trebuchet MS", "Arial",
        ]
        MONO_CANDIDATES = [
            "JetBrains Mono", "Cascadia Code", "Consolas",
            "Courier New", "Monaco", "Courier",
        ]

        serif = next((f for f in SERIF_CANDIDATES if f in available), "Georgia")
        sans  = next((f for f in SANS_CANDIDATES  if f in available), "Arial")
        mono  = next((f for f in MONO_CANDIDATES  if f in available), "Courier New")
        return serif, sans, mono
    except Exception:
        return "Georgia", "Arial", "Courier New"


_SERIF, _SANS, _MONO = _resolve_fonts()

FONT_SERIF = _SERIF
FONT_SANS  = _SANS
FONT_MONO  = _MONO
FONT_FAMILY = _SERIF   # legacy alias


# ── GLOBAL STYLESHEET ─────────────────────────────────────────────────────────
def get_global_stylesheet():
    return f"""
    QMainWindow, QDialog {{
        background: {BG};
    }}
    QWidget {{
        font-family: "{FONT_SANS}", "Segoe UI", Arial;
        font-size: {F_MD}pt;
        color: {FG};
        background: transparent;
    }}
    /* ── Scrollbars ── */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {FG_MUTED}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 4px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    /* ── Tooltips ── */
    QToolTip {{
        background: {FG};
        color: {WHITE};
        border: none;
        padding: 5px 10px;
        border-radius: {R_SM}px;
        font-size: {F_SM}pt;
    }}
    /* ── Message boxes ── */
    QMessageBox {{
        background: {CARD};
    }}
    QMessageBox QLabel {{
        color: {FG};
        font-size: {F_MD}pt;
        background: transparent;
        padding: 10px;
    }}
    QMessageBox QPushButton {{
        background: {SECONDARY};
        color: {FG};
        border: 1px solid {BORDER};
        border-radius: {R_SM}px;
        padding: 8px 24px;
        font-size: {F_MD}pt;
        font-weight: bold;
        min-width: 90px;
    }}
    QMessageBox QPushButton:hover {{
        background: {MUTED};
        border-color: {FG_MUTED};
    }}
    """