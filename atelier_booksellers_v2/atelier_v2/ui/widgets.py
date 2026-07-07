"""
widgets.py  ·  Andalus Booksellers — reusable UI components
Every component uses exact design tokens. No hardcoded values.
"""

import os
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QScrollArea, QWidget, QSizePolicy,
    QGraphicsDropShadowEffect, QSpinBox, QComboBox, QGridLayout,
    QAbstractItemView, QCompleter, QToolTip, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QPoint, QEvent, pyqtProperty, QRect, QRectF
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QCursor, QPainterPath, QPen, QBrush

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from assets.theme import *


# ── SHADOW ────────────────────────────────────────────────────────────────────

def apply_shadow(w, blur, offset, color):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    offset_x, offset_y = offset
    fx.setOffset(offset_x, offset_y)
    fx.setColor(QColor(color))
    w.setGraphicsEffect(fx)


# ── FONTS ─────────────────────────────────────────────────────────────────────

def font(size, bold=False, italic=False, serif=False):
    family = FONT_SERIF if serif else FONT_SANS
    f = QFont(family, size)
    f.setBold(bold)
    f.setItalic(italic)
    return f


def serif(size, bold=True, italic=False):
    f = QFont(FONT_SERIF, size)
    f.setBold(bold)
    f.setItalic(italic)
    return f


# ── STAT CARD ─────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label, value, sub="", dark=False, bg_color=None, fg_color=None, parent=None):
        super().__init__(parent)
        self.dark = dark
        self.bg_color = bg_color
        self.fg_color = fg_color
        self._val_lbl = None
        self._sub_lbl = None
        self._init(label, value, sub)

    def _init(self, label, value, sub):
        bg  = PRIMARY      if self.dark else CARD
        fg  = WHITE        if self.dark else FG
        sub_c = "#8AA898"  if self.dark else FG_MUTED
        
        if self.bg_color: bg = self.bg_color
        if self.fg_color:
            fg = self.fg_color
            sub_c = self.fg_color

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: {R_MD}px;
                border: none;
            }}
        """)

        self.setMinimumHeight(118)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if self.dark:
            apply_shadow(self, *SHADOW_LG)
        else:
            apply_shadow(self, *SHADOW_SM)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_5, SP_5, SP_5, SP_5)
        lay.setSpacing(SP_1)

        top = QHBoxLayout()
        lbl = QLabel(label.upper())
        lbl.setFont(font(F_XS, bold=True))
        lbl.setStyleSheet(f"color: {sub_c}; letter-spacing: 0.18em;")
        top.addWidget(lbl)
        top.addStretch()
        lay.addLayout(top)

        lay.addSpacing(SP_2)

        self._val_lbl = QLabel(str(value))
        self._val_lbl.setFont(serif(F_4XL))
        self._val_lbl.setStyleSheet(f"color: {fg};")
        lay.addWidget(self._val_lbl)

        if sub:
            self._sub_lbl = QLabel(sub)
            self._sub_lbl.setFont(font(F_SM))
            self._sub_lbl.setStyleSheet(f"color: {sub_c};")
            lay.addWidget(self._sub_lbl)

        lay.addStretch()

    def set_value(self, v):
        if self._val_lbl:
            self._val_lbl.setText(str(v))

    def set_sub(self, v):
        if self._sub_lbl:
            self._sub_lbl.setText(str(v))
        else:
            self._sub_lbl = QLabel(str(v))
            self._sub_lbl.setFont(font(F_SM))
            sub_c = "#8AA898" if self.dark else FG_MUTED
            self._sub_lbl.setStyleSheet(f"color: {sub_c};")
            self.layout().addWidget(self._sub_lbl)


# ── COVER LABEL (WITH DULL DIAGONAL FLASH) ────────────────────────────────────

class CoverLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._flash_pos = -600
        self._flash_anim = None

    def get_flash_pos(self):
        return self._flash_pos

    def set_flash_pos(self, pos):
        self._flash_pos = pos
        self.update()

    flash_pos = pyqtProperty(float, get_flash_pos, set_flash_pos)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._flash_pos > -600 and self._flash_pos < self.width() + 600:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            
            slash_width = 400
            gap = 50
            
            for i in range(3):
                x = self._flash_pos + i * (slash_width + gap)
                
                if x + slash_width > -100 and x < self.width() + 100:
                    grad = QLinearGradient(x, 0, x + slash_width, 0)
                    grad.setColorAt(0.0, QColor(255, 255, 255, 0))
                    grad.setColorAt(0.2, QColor(255, 255, 255, 40))
                    grad.setColorAt(0.4, QColor(255, 255, 255, 90))
                    grad.setColorAt(0.6, QColor(255, 255, 255, 90))
                    grad.setColorAt(0.8, QColor(255, 255, 255, 40))
                    grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                    
                    p.save()
                    p.translate(x, 0)
                    p.shear(0.6, 0)
                    p.setBrush(grad)
                    p.drawRect(-20, -50, slash_width, self.height() + 100)
                    p.restore()
            
            p.end()

    def start_flash(self):
        if self._flash_anim:
            self._flash_anim.stop()
        self._flash_pos = -600
        self._flash_anim = QPropertyAnimation(self, b"flash_pos")
        self._flash_anim.setDuration(1300)
        self._flash_anim.setStartValue(-600)
        self._flash_anim.setEndValue(self.width() + 600)
        self._flash_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._flash_anim.start()


# ── BOOK CARD ─────────────────────────────────────────────────────────────────

class BookCard(QFrame):
    clicked = pyqtSignal(int)

    _GENRE_PALETTES = {
        "Literary Fiction": ("#1E3D2F", "#C99A3D"),
        "Mystery":          ("#1A1A2E", "#C99A3D"),
        "Poetry":           ("#2D1A3E", "#C99A3D"),
        "Philosophy":       ("#2B1F0E", "#C99A3D"),
        "Biography":        ("#172F24", "#8AA898"),
        "History":          ("#251A10", "#C99A3D"),
        "Science Fiction":  ("#0D1B2A", "#7EC8E3"),
        "Romance":          ("#2D1018", "#E8A0C0"),
        "Self-Help":        ("#1A2E1E", "#C99A3D"),
    }

    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.book_id = book["id"]
        self._hovered = False
        self._original_pos = None
        self._build(book)

    def _build(self, book):
        self.setFixedWidth(260)
        self.setMinimumHeight(560)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._update_style()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Cover ──
        self._cover = CoverLabel()
        self._cover.setFixedSize(260, 400)
        self._cover.setAlignment(Qt.AlignCenter)
        self._cover.setStyleSheet(f"background: {SECONDARY}; border-radius: {R_MD}px {R_MD}px 0 0;")
        self._load_cover(book.get("image_path",""), book.get("genre",""))
        lay.addWidget(self._cover)

        # ── Discount Badge on Cover ──
        discount_pct = book.get("discount_percent", 0)
        if discount_pct > 0:
            discount_badge = QLabel(f"−{int(discount_pct)}% OFF")
            discount_badge.setFont(font(9, bold=True))
            discount_badge.setStyleSheet(f"""
                background: {DESTRUCTIVE};
                color: white;
                border-radius: 4px;
                padding: 4px 8px;
            """)
            discount_badge.adjustSize()
            discount_badge.setParent(self._cover)
            discount_badge.move(8, 8)
            discount_badge.show()

        # ── Body ──
        body = QWidget()
        body.setMinimumHeight(160)
        body.setStyleSheet(f"background: {CARD}; border-radius: 0 0 {R_MD}px {R_MD}px;")
    
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(SP_3, SP_2, SP_3, SP_3)
        body_lay.setSpacing(2)

        # Stock badge
        qty = book.get("quantity", 0)
        if qty == 0:
            bdg_bg, bdg_fg, bdg_txt = DESTRUCTIVE_TINT, DESTRUCTIVE, "OUT"
        elif qty <= STOCK_THRESHOLD:
            bdg_bg, bdg_fg, bdg_txt = DESTRUCTIVE_TINT, DESTRUCTIVE, f"LOW · {qty}"
        else:
            bdg_bg, bdg_fg, bdg_txt = SUCCESS_TINT, SUCCESS_FG, f"{qty} IN STOCK"

        badge = QLabel(bdg_txt)
        badge.setFont(font(8, bold=True))
        badge.setStyleSheet(f"background: {bdg_bg}; color: {bdg_fg}; border-radius: 10px; padding: 2px 8px;")
        badge.setAlignment(Qt.AlignCenter)
        badge.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    
        badge_container = QWidget()
        badge_container.setStyleSheet("background: transparent;")
        badge_layout = QHBoxLayout(badge_container)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.addWidget(badge)
        badge_layout.addStretch()
        body_lay.addWidget(badge_container)

        # Genre
        genre_name = book.get("genre") or ""
        if genre_name:
            genre_lbl = QLabel(genre_name.upper())
            genre_lbl.setFont(font(7, bold=True))
            genre_lbl.setStyleSheet(f"color: #8A7E6B; letter-spacing: 0.05em;")
            body_lay.addWidget(genre_lbl)

        # Title
        title = book.get("title","")
        t_lbl = QLabel(title if len(title)<=55 else title[:52]+"…")
        t_lbl.setFont(serif(14))
        t_lbl.setStyleSheet(f"color: {FG};")
        t_lbl.setWordWrap(True)
        t_lbl.setToolTip(title)
        body_lay.addWidget(t_lbl)

        # Author
        author = book.get("author","")
        a_lbl = QLabel(author if len(author)<=34 else author[:32]+"…")
        a_lbl.setFont(font(10, italic=True))
        a_lbl.setStyleSheet(f"color: {FG_MUTED};")
        a_lbl.setToolTip(author)
        body_lay.addWidget(a_lbl)

        body_lay.addStretch()

        # Price row
        original_price = book.get('price', 0)
        if discount_pct > 0:
            discounted_price = original_price * (1 - discount_pct / 100)
            
            price_row = QHBoxLayout()
            price_row.setContentsMargins(0,0,0,0)
            
            old_price_lbl = QLabel(f"Rs. {original_price:,.0f}")
            old_price_lbl.setFont(font(10))
            old_price_lbl.setStyleSheet(f"color: {FG_MUTED}; text-decoration: line-through;")
            price_row.addWidget(old_price_lbl)
            
            new_price_lbl = QLabel(f"Rs. {discounted_price:,.0f}")
            new_price_lbl.setFont(font(12, bold=True))
            new_price_lbl.setStyleSheet(f"color: {DESTRUCTIVE};")
            price_row.addWidget(new_price_lbl)
            
            price_row.addStretch()
            body_lay.addLayout(price_row)
        else:
            price_row = QHBoxLayout()
            price_row.setContentsMargins(0,0,0,0)
            p_lbl = QLabel(f"Rs. {original_price:,.0f}")
            p_lbl.setFont(font(13, bold=True))
            p_lbl.setStyleSheet(f"color: {PRIMARY};")
            price_row.addWidget(p_lbl)
            price_row.addStretch()
            body_lay.addLayout(price_row)

        lay.addWidget(body)

    def _update_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border-radius: {R_MD}px;
                border: none;
            }}
        """)

    def _load_cover(self, path, genre):
        if path and os.path.exists(path):
            pix = QPixmap(path).scaled(260, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            result = QPixmap(260, 400)
            result.fill(Qt.transparent)
            p = QPainter(result)
            p.setRenderHint(QPainter.Antialiasing)
            x = (260 - pix.width()) // 2
            y = (400 - pix.height()) // 2
            p.drawPixmap(x, y, pix)
            p.end()
            self._cover.setPixmap(result)
            return
        self._draw_placeholder(genre)

    def _draw_placeholder(self, genre):
        bg, fg = self._GENRE_PALETTES.get(genre, (PRIMARY, ACCENT))
        pix = QPixmap(260, 400)
        pix.fill(QColor(bg))
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        grad = QLinearGradient(0, 0, 0, 400)
        grad.setColorAt(0.0, QColor(255,255,255,18))
        grad.setColorAt(1.0, QColor(0,0,0,40))
        p.fillRect(0, 0, 260, 400, grad)

        p.setPen(QColor(fg+"28"))
        for i in range(20, 400, 24):
            p.drawLine(20, i, 240, i)

        p.setFont(QFont(FONT_SERIF, 48))
        p.setPen(QColor(fg+"DD"))
        p.drawText(0, 0, 260, 400, Qt.AlignCenter, "📖")
        p.end()
        self._cover.setPixmap(pix)

    def _animate_lift(self, lift_up=True):
        if self._original_pos is None:
            self._original_pos = self.pos()
        
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(80)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        
        if lift_up:
            new_pos = QPoint(self._original_pos.x(), self._original_pos.y() - 5)
        else:
            new_pos = self._original_pos
        
        anim.setEndValue(new_pos)
        anim.start()

    def enterEvent(self, e):
        self._hovered = True
        if self._original_pos is None:
            self._original_pos = self.pos()
        self._animate_lift(True)
        self._cover.start_flash()
        apply_shadow(self, *SHADOW_LG)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._animate_lift(False)
        apply_shadow(self, *SHADOW_SM)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.book_id)
        super().mousePressEvent(e)


# ── SIDEBAR NAV BUTTON ────────────────────────────────────────────────────────

class NavButton(QPushButton):
    def __init__(self, label, emoji="", parent=None):
        super().__init__(parent)
        self.setText(f"  {emoji}   {label}" if emoji else f"     {label}")
        self.setFont(font(F_MD))
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {SIDEBAR_FG};
                text-align: left;
                padding: 0 14px;
                border: none;
                border-radius: {R_SM}px;
                border-left: 3px solid transparent;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.07);
                color: {WHITE};
            }}
            QPushButton:checked {{
                background: rgba(255,255,255,0.09);
                color: {WHITE};
                border-left: 3px solid {ACCENT};
                font-weight: bold;
            }}
        """)


# ── SEARCH BAR ────────────────────────────────────────────────────────────────

class SearchBar(QLineEdit):
    def __init__(self, ph="Search titles, authors…", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(ph)
        self.setMinimumHeight(38)
        self.setFont(font(F_MD))
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {SECONDARY};
                border: 1px solid {BORDER};
                border-radius: {R_SM}px;
                padding: 0 14px;
                color: {FG};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {PRIMARY};
                background: {CARD};
            }}
        """)


# ── BUTTONS ───────────────────────────────────────────────────────────────────

class BtnPrimary(QPushButton):
    def __init__(self, text, emoji="", parent=None):
        super().__init__(f"{emoji}  {text}" if emoji else text, parent)
        self.setFont(font(F_MD, bold=True))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(40)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY};
                color: {WHITE};
                border: none;
                border-radius: {R_SM}px;
                padding: 0 22px;
            }}
            QPushButton:hover {{ background: {PRIMARY_H}; }}
            QPushButton:pressed {{ background: {SIDEBAR}; }}
        """)
        apply_shadow(self, *SHADOW_MD) 


class BtnSecondary(QPushButton):
    def __init__(self, text, emoji="", parent=None):
        super().__init__(f"{emoji}  {text}" if emoji else text, parent)
        self.setFont(font(F_MD))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(38)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {SECONDARY};
                color: {FG};
                border: 1px solid {BORDER};
                border-radius: {R_SM}px;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background: {MUTED};
                border-color: {FG_MUTED};
            }}
        """)


class BtnDanger(QPushButton):
    def __init__(self, text, emoji="", parent=None):
        super().__init__(f"{emoji}  {text}" if emoji else text, parent)
        self.setFont(font(F_MD))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(38)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {DESTRUCTIVE_TINT};
                color: {DESTRUCTIVE};
                border: 1px solid {DESTRUCTIVE_BORDER};
                border-radius: {R_SM}px;
                padding: 0 18px;
            }}
            QPushButton:hover {{
                background: #FAD4CF;
                border-color: {DESTRUCTIVE};
            }}
        """)


class BtnGold(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(font(F_LG, bold=True))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(48)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: {WHITE};
                border: none;
                border-radius: {R_SM}px;
                padding: 0 22px;
                letter-spacing: 0.04em;
            }}
            QPushButton:hover {{ background: #B8892E; }}
            QPushButton:pressed {{ background: #A07828; }}
        """)
        apply_shadow(self, *SHADOW_GOLD)


# ── GENRE CHIP ────────────────────────────────────────────────────────────────

class GenreChip(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFont(serif(F_MD, bold=False, italic=True))
        self.setMinimumHeight(32)
        self.setStyleSheet(f"""
            QPushButton {{
                background: #F0F4F1;
                color: {PRIMARY};
                border: 1px solid #D2DDD6;
                border-top-left-radius: 14px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 14px;
                border-bottom-left-radius: 4px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ 
                background: #E2EBE5; 
                border-color: #B4C6BC;
            }}
            QPushButton:checked {{
                background: {PRIMARY};
                color: {WHITE};
                border: 1px solid {PRIMARY};
            }}
        """)


# ── SECTION HEADER ────────────────────────────────────────────────────────────

class SectionHeader(QWidget):
    view_all = pyqtSignal()

    def __init__(self, title, show_all=False, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lbl = QLabel(title)
        lbl.setFont(serif(F_2XL))
        lbl.setStyleSheet(f"color: {FG};")
        lay.addWidget(lbl)
        lay.addStretch()
        if show_all:
            btn = QPushButton("View all →")
            btn.setFont(font(F_SM))
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {FG_MUTED}; border: none; }}
                QPushButton:hover {{ color: {PRIMARY}; }}
            """)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(self.view_all)
            lay.addWidget(btn)


# ── BOOK GRID (responsive) ────────────────────────────────────────────────────

class BookGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cols = 5
        self._grid = None
        self.setStyleSheet("background: transparent;")

    def resizeEvent(self, e):
        w = self.width()
        cols = max(1, min(5, w // 280))
        if cols != self._cols:
            self._cols = cols
        super().resizeEvent(e)

    def populate(self, cards):
        if self._grid:
            while self._grid.count():
                item = self._grid.takeAt(0)
                if item and item.widget():
                    w = item.widget()
                    w.setParent(None)
                    w.deleteLater()
            
            for i in range(self._grid.rowCount()):
                self._grid.setRowStretch(i, 0)
        else:
            self._grid = QGridLayout(self)
            self._grid.setHorizontalSpacing(SP_6)
            self._grid.setVerticalSpacing(SP_10)
            self._grid.setContentsMargins(SP_10, SP_5, SP_10, SP_5)

        if not cards:
            return

        for i, card in enumerate(cards):
            r, c = divmod(i, self._cols)
            self._grid.addWidget(card, r, c)
        
        last_row = (len(cards) - 1) // self._cols if cards else 0
        self._grid.setRowStretch(last_row + 1, 1)


# ── CART ROW ──────────────────────────────────────────────────────────────────

class CartRow(QFrame):
    removed     = pyqtSignal(int)
    qty_changed = pyqtSignal(int, int)

    def __init__(self, book_id, title, price, qty=1, discount_pct=0, parent=None):
        super().__init__(parent)
        self.book_id = book_id
        self.price   = price
        self._build(title, price, qty, discount_pct)

    def _build(self, title, price, qty, discount_pct):
        self.setFixedHeight(84) # Slightly taller for discount info
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border-radius: {R_SM}px;
                border: 1px solid {BORDER if discount_pct == 0 else DESTRUCTIVE_TINT};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(SP_3, SP_2, SP_3, SP_2)
        lay.setSpacing(SP_2)
        
        # Leading discount bar
        if discount_pct > 0:
            bar = QFrame()
            bar.setFixedWidth(4)
            bar.setStyleSheet(f"background: {DESTRUCTIVE}; border-radius: 2px;")
            lay.addWidget(bar)

        col = QVBoxLayout(); col.setSpacing(1)
        t = QLabel(title if len(title)<=24 else title[:22]+"…")
        t.setFont(font(F_SM, bold=True))
        t.setStyleSheet(f"color: {FG};")
        
        p_lay = QHBoxLayout()
        p = QLabel(f"Rs. {price:,.0f}")
        p.setFont(font(F_SM, bold=discount_pct > 0))
        p.setStyleSheet(f"color: {DESTRUCTIVE if discount_pct > 0 else FG_MUTED};")
        p_lay.addWidget(p)
        
        if discount_pct > 0:
            tag = QLabel(f"−{int(discount_pct)}%")
            tag.setFont(font(7, bold=True))
            tag.setStyleSheet(f"background: {DESTRUCTIVE}; color: white; border-radius: 3px; padding: 1px 4px;")
            p_lay.addWidget(tag)
        
        p_lay.addStretch()
        
        col.addWidget(t)
        col.addLayout(p_lay)
        lay.addLayout(col); lay.addStretch()

        self._spin = QSpinBox()
        self._spin.setRange(1, 999)
        self._spin.setValue(qty)
        self._spin.setButtonSymbols(QSpinBox.NoButtons)
        self._spin.setFixedSize(40, 26)
        self._spin.setAlignment(Qt.AlignCenter)
        self._spin.setStyleSheet(f"""
            QSpinBox {{
                border: 1px solid {BORDER};
                border-radius: {R_XS}px;
                background: {BG};
                color: {FG};
                font-size: {F_SM}pt;
            }}
        """)

        def _mk_step(symbol):
            b = QPushButton(symbol)
            b.setFixedSize(26, 26)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {SECONDARY};
                    border: 1px solid {BORDER};
                    border-radius: {R_XS}px;
                    color: {FG};
                    font-weight: bold;
                    font-size: {F_MD}pt;
                }}
                QPushButton:hover {{ background: {MUTED}; }}
            """)
            return b

        bm = _mk_step("−"); bp = _mk_step("+")
        bm.clicked.connect(lambda: self._spin.setValue(max(1, self._spin.value()-1)))
        bp.clicked.connect(lambda: self._spin.setValue(self._spin.value()+1))
        self._spin.valueChanged.connect(lambda v: self.qty_changed.emit(self.book_id, v))

        for w in (bm, self._spin, bp):
            lay.addWidget(w)

        rm = QPushButton("✕")
        rm.setFixedSize(22, 22)
        rm.setCursor(QCursor(Qt.PointingHandCursor))
        rm.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {FG_MUTED}; font-size: {F_SM}pt; }}
            QPushButton:hover {{ color: {DESTRUCTIVE}; }}
        """)
        rm.clicked.connect(lambda: self.removed.emit(self.book_id))
        lay.addWidget(rm)


# ── FORM HELPERS ──────────────────────────────────────────────────────────────

def _input_style():
    return f"""
        background: {SECONDARY};
        border: 1px solid {BORDER};
        border-radius: {R_SM}px;
        padding: 0 12px;
        color: {FG};
        font-family: "{FONT_SANS}";
        font-size: {F_MD}pt;
    """

def _input_focus():
    return f"border: 1.5px solid {PRIMARY}; background: {CARD};"


class LabeledField(QWidget):
    def __init__(self, label, widget, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(5)
        lbl = QLabel(label)
        lbl.setFont(font(F_SM, bold=True))
        lbl.setStyleSheet(f"color: {FG_MUTED}; letter-spacing: 0.06em;")
        lay.addWidget(lbl)
        lay.addWidget(widget)

    @staticmethod
    def edit(ph=""):
        e = QLineEdit()
        e.setPlaceholderText(ph)
        e.setMinimumHeight(38)
        e.setFont(font(F_MD))
        e.setStyleSheet(f"QLineEdit {{ {_input_style()} }} QLineEdit:focus {{ {_input_focus()} }}")
        return e

    @staticmethod
    def combo():
        c = QComboBox()
        c.setMinimumHeight(38)
        c.setFont(font(F_MD))
        c.setStyleSheet(f"""
            QComboBox {{ {_input_style()} }}
            QComboBox:focus {{ {_input_focus()} }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QComboBox QAbstractItemView {{
                background: {CARD}; border: 1px solid {BORDER};
                selection-background-color: {ACCENT_TINT};
                selection-color: {PRIMARY}; color: {FG};
            }}
        """)
        return c

    @staticmethod
    def spin(lo=0, hi=99999):
        s = QSpinBox()
        s.setRange(lo, hi)
        s.setMinimumHeight(38)
        s.setFont(font(F_MD))
        s.setStyleSheet(f"QSpinBox {{ {_input_style()} }} QSpinBox:focus {{ {_input_focus()} }}")
        return s



# ── DIVIDER ───────────────────────────────────────────────────────────────────

class HDivider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BORDER}; border: none;")




# ── TABLE HELPERS ─────────────────────────────────────────────────────────────

TABLE_STYLE = f"""
    QTableWidget {{
        background: {CARD};
        border: none;
        border-radius: {R_MD}px;
        gridline-color: transparent;
        outline: none;
    }}
    QTableWidget::item {{
        padding: 0 10px;
        color: {FG};
        border-bottom: 1px solid {BORDER};
    }}
    QTableWidget::item:selected {{
        background: {ACCENT_TINT};
        color: {PRIMARY};
    }}
    QTableWidget::item:alternate {{
        background: #FCFCFA;
    }}
    QHeaderView::section {{
        background: {BG};
        color: {FG_MUTED};
        font-family: "{FONT_SANS}";
        font-size: {F_XS}pt;
        font-weight: bold;
        letter-spacing: 0.14em;
        padding: 0 10px;
        border: none;
        border-bottom: 2px solid {BORDER};
        height: 38px;
        text-transform: uppercase;
    }}
    QHeaderView::section:first {{ border-radius: {R_MD}px 0 0 0; }}
    QHeaderView::section:last  {{ border-radius: 0 {R_MD}px 0 0; }}
"""


# ── TOAST NOTIFICATION ────────────────────────────────────────────────────────

class ToastNotification(QFrame):
    """Non-blocking, auto-fading notification overlay"""
    def __init__(self, message, success=True, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setFixedHeight(60)
        
        bg = SUCCESS_FG if success else DESTRUCTIVE
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                color: {WHITE};
                border-radius: {R_MD}px;
                border: none;
            }}
        """)
        apply_shadow(self, 20, (0, 8), "rgba(0,0,0,0.25)")
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(15)
        
        icon = QLabel("✓" if success else "⚠")
        icon.setFont(font(18, bold=True))
        icon.setStyleSheet(f"color: {WHITE};")
        lay.addWidget(icon)
        
        msg = QLabel(message)
        msg.setFont(font(F_MD, bold=True))
        msg.setStyleSheet(f"color: {WHITE};")
        msg.setWordWrap(True)
        lay.addWidget(msg, stretch=1)
        
        # Position it
        if parent:
            self.move((parent.width() - self.width()) // 2, 40)
        
        # Animations
        self.setWindowOpacity(0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(400)
        self._anim.setStartValue(0)
        self._anim.setEndValue(1)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(10, self._start)
        QTimer.singleShot(3500, self._fade_out)

    def _start(self):
        self.show()
        self._anim.start()

    def _fade_out(self):
        self._anim.setDirection(QPropertyAnimation.Backward)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()


class StatusLabel(QLabel):
    """In-UI feedback label for errors/successes without popups"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(font(F_SM, italic=True))
        self.hide()
        
    def show_msg(self, text, is_error=True):
        self.setText(text)
        self.setStyleSheet(f"color: {DESTRUCTIVE if is_error else SUCCESS_FG}; background: transparent; padding: 4px;")
        self.show()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(5000, self.hide)

