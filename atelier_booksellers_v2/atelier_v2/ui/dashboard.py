"""dashboard.py  ·  Main Storefront & Analytics Dashboard"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QPushButton, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QCursor
from assets.theme import *
from ui.widgets import StatCard, GenreChip, BookCard, BookGrid, SectionHeader, font, serif, apply_shadow
import utils.database as db

class DashboardScreen(QWidget):
    open_book = pyqtSignal(object)  # Emits book data
    nav_to    = pyqtSignal(str)     # Emits screen name to nav to

    def __init__(self, parent=None):
        super().__init__(parent)
        self._genre_id = None
        self._search_text = ""
        self._chips = {}
        self._build()
        self.refresh()

    def _build(self):
        # Outer layout
        outer_root = QVBoxLayout(self)
        outer_root.setContentsMargins(0, 0, 0, 0)
        outer_root.setSpacing(0)

        # Main scroll area for the whole page
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("background: transparent;")

        # Container for scroll area
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._scroll.setWidget(container)
        outer_root.addWidget(self._scroll)

        # Actual content layout
        root = QVBoxLayout(container)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(0)

        # ── Floating "Back to Top" Button ──
        self._top_btn = QPushButton("Top", self)
        self._top_btn.setFixedSize(70, 70)
        self._top_btn.setCursor(Qt.PointingHandCursor)
        self._top_btn.setFont(serif(16, bold=True, italic=True))
        self._top_btn.setStyleSheet(f"""
            QPushButton {{
                background: {SUCCESS_FG};
                color: {WHITE};
                border-radius: 35px;
                border: 3px solid {WHITE};
            }}
            QPushButton:hover {{
                background: {SUCCESS_FG};
                border-color: {ACCENT};
            }}
        """)
        apply_shadow(self._top_btn, 30, (0, 10), "#19241F33")
        self._top_btn.clicked.connect(self._scroll_to_top)
        self._top_btn.hide()

        # Track scroll to show/hide button
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # ── Welcome Banner ──
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background: {PRIMARY};
                border-radius: {R_LG}px;
            }}
        """)
        banner.setMinimumHeight(140)
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(32, 24, 32, 24)
        
        bc = QVBoxLayout()
        bc.setSpacing(8)
        bc.addStretch()
        bt = QLabel("Andalus Management Console")
        bt.setFont(serif(32, bold=True))
        bt.setStyleSheet(f"color: {WHITE};")
        self._status_line = QLabel("Purveyors of Fine Literature & Timeless Wisdom")
        self._status_line.setFont(font(F_LG, italic=True, serif=True))
        self._status_line.setStyleSheet(f"color: #D1FAE5; opacity: 0.85; letter-spacing: 0.05em;")
        
        bc.addWidget(bt)
        bc.addWidget(self._status_line)
        bc.addStretch()
        bl.addLayout(bc)
        bl.addStretch()
        
        icon_container = QWidget()
        icon_container.setStyleSheet("background: transparent;")
        icl = QVBoxLayout(icon_container)
        icl.setContentsMargins(0,0,0,0)
        
        self._banner_img = QLabel()
        self._banner_img.setFixedSize(140, 180) # Slightly larger but proportional
        self._banner_img.setCursor(QCursor(Qt.PointingHandCursor))
        self._banner_img.setToolTip("Click to change banner image")
        # Removed dashed border and background for a 'boundary-free' look
        self._banner_img.setStyleSheet("background: transparent; border: none;")
        self._banner_img.mousePressEvent = self._change_banner_image
        
        icl.addWidget(self._banner_img)
        bl.addWidget(icon_container)
        bl.addSpacing(16)
        
        self._load_banner_image()
        
        root.addWidget(banner)
        root.addSpacing(SP_8)

        # ── KPI cards ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(SP_4)
        self._c_rev   = StatCard("Today's Revenue",    "Rs. 0", dark=True)
        self._c_books = StatCard("Books in Catalogue", "0", "Total unique titles", bg_color=SUCCESS_TINT, fg_color=SUCCESS_FG)
        self._c_best  = StatCard("Bestseller",         "—", "Top selling title", bg_color=ACCENT_TINT, fg_color=PRIMARY)
        self._c_low   = StatCard("Low Stock",          "0", "Requires restocking", bg_color=DESTRUCTIVE_TINT, fg_color=DESTRUCTIVE)
        for c in (self._c_rev, self._c_books, self._c_best, self._c_low):
            kpi_row.addWidget(c)
        root.addLayout(kpi_row)
        
        root.addSpacing(SP_10)
        hdr = SectionHeader("Your Collection", show_all=True)
        hdr.view_all.connect(lambda: self.nav_to.emit("catalogue"))
        root.addWidget(hdr)
        
        root.addSpacing(SP_3)

        # ── Genre chips ──
        self._chip_row = QHBoxLayout()
        self._chip_row.setSpacing(SP_2)
        self._chip_row.setAlignment(Qt.AlignLeft)
        root.addLayout(self._chip_row)
        
        self._chips = {}
        self._build_genre_chips()
        root.addSpacing(SP_4)

        # ── Book grid ──
        self._grid = BookGrid()
        root.addWidget(self._grid, stretch=1)

    def _build_genre_chips(self):
        while self._chip_row.count():
            item = self._chip_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._chips = {}
        all_chip = GenreChip("All")
        all_chip.setChecked(self._genre_id is None)
        all_chip.clicked.connect(lambda: self._filter(None, all_chip))
        self._chip_row.addWidget(all_chip)
        self._chips[None] = all_chip

        for g in db.get_genres():
            c = GenreChip(g["name"])
            c.setChecked(self._genre_id == g["id"])
            c.clicked.connect(lambda _, gid=g["id"], chip=c: self._filter(gid, chip))
            self._chip_row.addWidget(c)
            self._chips[g["id"]] = c

        self._chip_row.addStretch()

    def _filter(self, genre_id, active):
        for gid, chip in self._chips.items():
            chip.setChecked(gid == genre_id)
        self._genre_id = genre_id
        self._load_books()

    def search(self, text):
        self._search_text = text
        self._load_books()

    def refresh(self):
        s = db.dashboard_stats()
        self._c_rev.set_value(f"Rs. {s['today_rev']:,.0f}")
        self._c_books.set_value(str(s["total_books"]))
        self._c_best.set_value(s["bestseller"] or "—")
        self._c_low.set_value(str(s["low_stock"]))
        
        self._build_genre_chips()
        self._load_books()

    def _load_books(self):
        books = db.get_books(genre_id=self._genre_id, search=self._search_text)
        cards = []
        for b in books:
            card = BookCard(b)
            card.clicked.connect(self.open_book.emit)
            cards.append(card)
        self._grid.populate(cards)

    def _scroll_to_top(self):
        # Create smooth slide animation
        self._scroll_anim = QPropertyAnimation(self._scroll.verticalScrollBar(), b"value")
        self._scroll_anim.setDuration(600)  # Fast but smooth
        self._scroll_anim.setStartValue(self._scroll.verticalScrollBar().value())
        self._scroll_anim.setEndValue(0)
        self._scroll_anim.setEasingCurve(QEasingCurve.OutQuint)
        self._scroll_anim.start()

    def _on_scroll(self, value):
        # Show button if scrolled past 300px
        self._top_btn.setVisible(value > 300)
        self._reposition_btn()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_btn()

    def _reposition_btn(self):
        # Place in bottom right corner
        if hasattr(self, '_top_btn'):
            # Offset from bottom-right (20px margin)
            self._top_btn.move(self.width() - 90, self.height() - 90)

    def _load_banner_image(self):
        path = db.get_setting("banner_image")
        if path and os.path.exists(path):
            original = QPixmap(path)
            # Create a rounded version of the pixmap
            size = self._banner_img.size()
            rounded = QPixmap(size)
            rounded.fill(Qt.transparent)
            
            from PyQt5.QtGui import QPainter, QPainterPath
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            path_obj = QPainterPath()
            path_obj.addRoundedRect(0, 0, size.width(), size.height(), R_MD, R_MD)
            painter.setClipPath(path_obj)
            
            scaled = original.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Center the scaled image
            x = (size.width() - scaled.width()) // 2
            y = (size.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
            
            self._banner_img.setPixmap(rounded)
            self._banner_img.setText("")
            self._banner_img.setStyleSheet("background: transparent; border: none;")
        else:
            self._banner_img.setText("📷\nAdd Pic")
            self._banner_img.setFont(font(F_SM, bold=True))
            self._banner_img.setAlignment(Qt.AlignCenter)
            self._banner_img.setStyleSheet(f"color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.05); border-radius: {R_MD}px;")

    def _change_banner_image(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Select Banner Image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            db.set_setting("banner_image", path)
            self._load_banner_image()
