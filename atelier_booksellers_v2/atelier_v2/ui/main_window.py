"""main_window.py  ·  Andalus Booksellers — Application shell"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.isbn_lookup import ISBNLookupScreen

from ui.requests import CustomerRequestsScreen


from ui.management import GenresScreen, SuppliersScreen, SalesHistoryScreen

from ui.management import CouponScreen
from ui.requests import CustomerRequestsScreen

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QStackedWidget, QSizePolicy, QPushButton
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QColor

from assets.theme import *
from ui.widgets import NavButton, SearchBar, BtnPrimary, font, serif, apply_shadow, ToastNotification

from ui.dashboard    import DashboardScreen
from ui.catalogue    import CatalogueScreen
from ui.sales        import SalesScreen
from ui.inventory    import InventoryScreen
from ui.insights     import InsightsScreen
from ui.management   import GenresScreen, SuppliersScreen, SalesHistoryScreen
import utils.database as db

# Page index constants
P_DASH  = 0; P_CAT  = 1; P_GENRE = 2; P_SUP  = 3
P_SALE  = 4; P_HIST = 5; P_INV   = 6; P_INS  = 7
P_SCAN  = 8; P_COUPON = 9; P_REQS = 10


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Andalus Booksellers")
        self.setMinimumSize(1300, 800)
        self.resize(1500, 880)

        root = QWidget()
        self.setCentralWidget(root)
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(0)

        self._sidebar = self._build_sidebar()
        lay.addWidget(self._sidebar)

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0,0,0,0)
        cl.setSpacing(0)
        cl.addWidget(self._build_header())

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {BORDER}; border: none;")
        cl.addWidget(div)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {BG};")

        self._screens = [
            DashboardScreen(),    # 0
            CatalogueScreen(),    # 1
            GenresScreen(),       # 2
            SuppliersScreen(),    # 3
            SalesScreen(),        # 4
            SalesHistoryScreen(), # 5
            InventoryScreen(),    # 6
            InsightsScreen(),     # 7
            ISBNLookupScreen(),   # 8
            CouponScreen(),       # 9
            CustomerRequestsScreen(), # 10
        ]
        for s in self._screens:
            self._stack.addWidget(s)

        cl.addWidget(self._stack, stretch=1)
        lay.addWidget(content, stretch=1)

        # Wire signals
        self._screens[P_DASH].open_book.connect(self._open_book_for_sale)
        self._screens[P_DASH].nav_to.connect(self._nav_to)
        self._screens[P_SALE].completed.connect(self._on_sale_done)

        self._update_notifications()
        self._go(P_DASH)
        
        # Force dashboard to fully render after launch
        QTimer.singleShot(150, self._force_dashboard_render)

    def _force_dashboard_render(self):
        """Force all book cards to repaint properly"""
        dashboard = self._screens[P_DASH]
        dashboard.update()
        dashboard.repaint()
        # Also refresh the grid to ensure all cards are visible
        if hasattr(dashboard, '_grid'):
            dashboard._grid.update()

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = QWidget()
        sb.setFixedWidth(SIDEBAR_W)
        sb.setStyleSheet(f"background: {SIDEBAR};")

        lay = QVBoxLayout(sb)
        lay.setContentsMargins(SP_2, SP_6, SP_2, SP_6)
        lay.setSpacing(2)

        # Logo
        logo = QWidget()
        logo.setStyleSheet("background: transparent;")
        ll = QHBoxLayout(logo)
        ll.setContentsMargins(SP_3, 0, 0, SP_5)
        ll.setSpacing(SP_3)
        icon = QLabel("📖")
        icon.setFont(font(22))
        icon.setStyleSheet("color: white;")
        col = QVBoxLayout()
        col.setSpacing(0)
        nm = QLabel("Andalus")
        nm.setFont(serif(F_XL, bold=True))
        nm.setStyleSheet(f"color: {SIDEBAR_FG};")
        sub = QLabel("BOOKSELLERS")
        sub.setFont(font(F_XS, bold=True))
        sub.setStyleSheet(f"color: {SIDEBAR_SUB}; letter-spacing: 0.22em;")
        col.addWidget(nm)
        col.addWidget(sub)
        ll.addWidget(icon)
        ll.addLayout(col)
        ll.addStretch()
        
        from PyQt5.QtGui import QCursor
        self._close_sidebar_btn = QPushButton("☰")
        self._close_sidebar_btn.setFixedSize(32, 32)
        self._close_sidebar_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._close_sidebar_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {SIDEBAR_FG};
                font-size: 20px;
            }}
            QPushButton:hover {{ color: {WHITE}; }}
        """)
        self._close_sidebar_btn.clicked.connect(self._toggle_sidebar)
        ll.addWidget(self._close_sidebar_btn)
        
        lay.addWidget(logo)

        # Nav sections
        self._btns = []
        self._active_btn = None

        def section(text):
            lbl = QLabel(text)
            lbl.setFont(font(F_XS, bold=True))
            lbl.setStyleSheet(
                f"color: {SIDEBAR_SUB}; letter-spacing: 0.22em; "
                f"padding: 14px 12px 4px; background: transparent;"
            )
            lay.addWidget(lbl)

        def nav(label, emoji, page):
            btn = NavButton(label, emoji)
            btn.clicked.connect(lambda: self._go(page))
            lay.addWidget(btn)
            self._btns.append((page, btn))
            return btn

        section("MANAGE")
        nav("Dashboard",     "⊞", P_DASH)
        nav("Catalogue",     "📚", P_CAT)
        nav("ISBN Lookup",    "📖", P_SCAN)
        nav("Genres",        "🏷",  P_GENRE)
        nav("Suppliers",     "🏭",  P_SUP)
        nav("Coupons", "🎫", P_COUPON)
        nav("Requests", "✨", P_REQS)

        section("SALES")
        nav("New Sale",      "💳",  P_SALE) 
        nav("Sales History", "📋",  P_HIST)
        nav("Inventory",     "📦",  P_INV)
        nav("Insights",      "📊",  P_INS)

        lay.addStretch()

        # Employee footer
        emp = db.get_employee()
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.07);
                border-radius: {R_SM}px;
                border: 1px solid rgba(255,255,255,0.08);
            }}
        """)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(SP_3, SP_2, SP_3, SP_2)
        fl.setSpacing(SP_3)

        av = QLabel(emp["name"][0].upper())
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignCenter)
        av.setFont(font(F_LG, bold=True))
        av.setStyleSheet(f"background: {PRIMARY_H}; color: white; border-radius: 17px;")

        ec = QVBoxLayout()
        ec.setSpacing(0)
        en = QLabel(emp["name"])
        en.setFont(font(F_SM, bold=True))
        en.setStyleSheet(f"color: {SIDEBAR_FG};")
        er = QLabel(emp["role"])
        er.setFont(font(F_XS))
        er.setStyleSheet(f"color: {SIDEBAR_SUB};")
        ec.addWidget(en)
        ec.addWidget(er)

        fl.addWidget(av)
        fl.addLayout(ec)
        fl.addStretch()
        gear = QLabel("⚙")
        gear.setFont(font(14))
        gear.setStyleSheet(f"color: {SIDEBAR_SUB};")
        fl.addWidget(gear)
        lay.addWidget(footer)
        return sb

    # ── Header ────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = QWidget()
        hdr.setFixedHeight(HEADER_H)
        hdr.setStyleSheet(f"background: {BG};")

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(SP_10, 0, SP_10, 0)
        lay.setSpacing(SP_4)

        from PyQt5.QtGui import QCursor
        self._toggle_btn = QPushButton("☰")
        self._toggle_btn.setFixedSize(38, 38)
        self._toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {FG};
                font-size: 24px;
            }}
            QPushButton:hover {{ color: {PRIMARY}; }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        self._toggle_btn.setVisible(False)
        lay.addWidget(self._toggle_btn)

        self._home_btn = QPushButton("←")
        self._home_btn.setFixedSize(38, 38)
        self._home_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._home_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {FG};
                font-size: 24px;
            }}
            QPushButton:hover {{ color: {PRIMARY}; }}
        """)
        self._home_btn.clicked.connect(lambda: self._go(P_DASH))
        self._home_btn.setToolTip("Back to Dashboard")
        lay.addWidget(self._home_btn)

        today = QDate.currentDate()
        dc = QVBoxLayout()
        dc.setSpacing(1)
        dl = QLabel(today.toString("dddd, d MMMM").upper())
        dl.setFont(font(F_XS, bold=True))
        dl.setStyleSheet(f"color: {FG_MUTED}; letter-spacing: 0.18em;")
        h = __import__("datetime").datetime.now().hour
        greet = "Good morning" if h < 12 else ("Good afternoon" if h < 17 else "Good evening")
        emp = db.get_employee()
        gl = QLabel(f"{greet}, {emp['name'].split()[0]}")
        gl.setFont(serif(F_2XL))
        gl.setStyleSheet(f"color: {FG};")
        dc.addWidget(dl)
        dc.addWidget(gl)
        lay.addLayout(dc)
        lay.addStretch()

        self._gsearch = SearchBar()
        self._gsearch.setFixedWidth(320)
        self._gsearch.setFixedHeight(38)
        self._gsearch.textChanged.connect(self._global_search)
        lay.addWidget(self._gsearch)

        self._notif_btn = QPushButton("🔔")
        self._notif_btn.setFixedSize(60, 38)
        self._notif_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._notif_btn.clicked.connect(self._show_notifications)
        lay.addWidget(self._notif_btn)

        btn = BtnPrimary("+ New Sale")
        btn.setFixedHeight(38)
        btn.clicked.connect(lambda: self._go(P_SALE))
        lay.addWidget(btn)
        return hdr

    def show_toast(self, message, success=True):
        """Show a non-blocking toast notification"""
        ToastNotification(message, success, self)

    # ── Navigation ────────────────────────────────────────────────────────

    def _toggle_sidebar(self):
        is_visible = self._sidebar.isVisible()
        self._sidebar.setVisible(not is_visible)
        self._toggle_btn.setVisible(is_visible)

    def _go(self, page):
        for pg, btn in self._btns:
            btn.setChecked(pg == page)
        self._stack.setCurrentIndex(page)
        
        if hasattr(self, '_home_btn'):
            self._home_btn.setVisible(page != P_DASH)
            
        screen = self._screens[page]
        if hasattr(screen, 'refresh'):
            # Delay refresh slightly to allow the UI to switch instantly
            # without a 'jarring' hang.
            QTimer.singleShot(10, screen.refresh)

    def _nav_to(self, name):
        if name == "catalogue":
            self._go(P_CAT)

    def _open_book_for_sale(self, book_id):
        self._go(P_SALE)
        # We must call pre_select_book AFTER the screen has had a chance to refresh
        # or we just rely on pre_select_book doing its own refresh.
        # To be safe and smooth, we'll delay it slightly.
        QTimer.singleShot(20, lambda: self._screens[P_SALE].pre_select_book(book_id))

    def _global_search(self, text):
        if self._stack.currentIndex() != P_DASH:
            self._go(P_DASH)
        # Directly call search on the dashboard screen without full refresh
        self._screens[P_DASH].search(text)

    def _on_sale_done(self):
        """Refresh all data-bound screens after a confirmed sale."""
        self._screens[P_DASH].refresh()
        self._screens[P_CAT].refresh() 
        self._screens[P_INV].refresh()
        self._screens[P_HIST].refresh()
        self._screens[P_INS].refresh()
        self._update_notifications()
        self.show_toast("Sale recorded successfully ✓")

    def _update_notifications(self):
        stats = db.dashboard_stats()
        low = stats.get("low_stock", 0)
        if low > 0:
            self._notif_btn.setText(f"🔔 {low}")
            self._notif_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {DESTRUCTIVE_TINT};
                    border: 1px solid {DESTRUCTIVE_BORDER};
                    border-radius: {R_SM}px;
                    color: {DESTRUCTIVE};
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: #FAD4CF; }}
            """)
            self._notif_btn.setToolTip(f"{low} book(s) need restocking")
        else:
            self._notif_btn.setText("🔔")
            self._notif_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {BORDER};
                    border-radius: {R_SM}px;
                    color: {FG_MUTED};
                    font-size: 16px;
                }}
                QPushButton:hover {{ background: rgba(0,0,0,0.05); }}
            """)
            self._notif_btn.setToolTip("Stock levels healthy")

    def _show_notifications(self):
        low_stock_books = [b for b in db.get_books() if b['quantity'] < 5]
        from PyQt5.QtWidgets import QMessageBox
        if not low_stock_books:
            QMessageBox.information(self, "Stock Levels", "All books have healthy stock levels!")
            return
            
        msg = "These books need to fill:\n\n"
        for b in low_stock_books:
            msg += f"• {b['title']} (Current stock: {b['quantity']})\n"
            
        QMessageBox.warning(self, "Restock Required", msg)