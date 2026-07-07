"""insights.py  ·  Andalus Booksellers — Analytics & Insights"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt

from assets.theme import *
from ui.widgets import StatCard, SectionHeader, HDivider, font, serif, apply_shadow
import utils.database as db

try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class InsightsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area - THIS IS KEY
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {BG};
                border: none;
            }}
        """)
        
        # Content widget inside scroll area
        self._content = QWidget()
        self._content.setStyleSheet(f"background: {BG};")
        self._scroll.setWidget(self._content)
        
        # Content layout - VERTICAL with NO height restrictions
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(SP_10, SP_6, SP_10, SP_10)
        self._layout.setSpacing(SP_8)
        
        main_layout.addWidget(self._scroll)
        
        self.refresh()

    def refresh(self):
        # Clear layout
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        # Header
        self._layout.addWidget(SectionHeader("Sales Insights"))

        # KPI row
        kpi = QHBoxLayout()
        kpi.setSpacing(SP_4)
        s = db.dashboard_stats()
        
        # 1. All-Time Revenue (Dark Theme)
        kpi.addWidget(StatCard("All-Time Revenue", f"Rs. {db.alltime_revenue():,.0f}", dark=True))
        
        # 2. Total Books Sold (Success Green)
        kpi.addWidget(StatCard("Total Books Sold", f"{db.total_books_sold():,}", 
                               bg_color=SUCCESS_TINT, fg_color=SUCCESS_FG))
        
        # 3. Today's Revenue (Gold/Accent)
        kpi.addWidget(StatCard("Today's Revenue", f"Rs. {s['today_rev']:,.0f}", 
                               bg_color=ACCENT_TINT, fg_color=PRIMARY))
        
        # 4. Low Stock Alerts (Destructive Burgundy)
        kpi.addWidget(StatCard("Low Stock", str(s['low_stock']), 
                               bg_color=DESTRUCTIVE_TINT, fg_color=DESTRUCTIVE))
        
        self._layout.addLayout(kpi)

        if not HAS_MPL:
            note = QLabel("Install matplotlib for charts:\n  pip install matplotlib")
            note.setAlignment(Qt.AlignCenter)
            note.setFont(font(14, italic=True))
            note.setStyleSheet(f"color: {FG_MUTED}; padding: 60px;")
            self._layout.addWidget(note)
            self._layout.addStretch()
            return

        # Top 5 Books - Full size, natural height
        self._layout.addWidget(self._top_books_bar())
        
        # Revenue Trend - Full size, natural height
        self._layout.addWidget(self._revenue_trend())
        
        # Bottom row - Side by side
        bottom = QHBoxLayout()
        bottom.setSpacing(SP_5)
        bottom.addWidget(self._genre_pie(), stretch=1)
        bottom.addWidget(self._top_three_list(), stretch=1)
        self._layout.addLayout(bottom)
        
        # Push everything up, allow scrolling
        self._layout.addStretch()

    def _chart_card(self, title):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border-radius: {R_MD}px;
                border: 1px solid {BORDER};
            }}
        """)
        apply_shadow(card, *SHADOW_SM)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SP_6, SP_6, SP_6, SP_6)
        layout.setSpacing(SP_4)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(serif(18))
        title_lbl.setStyleSheet(f"color: {FG};")
        layout.addWidget(title_lbl)
        
        return card, layout

    def _top_books_bar(self):
        card, layout = self._chart_card("Top 5 Bestsellers")
        
        data = db.top_books(5)
        if not data:
            lbl = QLabel("No sales data yet")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(font(12, italic=True))
            lbl.setStyleSheet(f"color: {FG_MUTED}; padding: 60px;")
            layout.addWidget(lbl)
            return card
        
        titles = [d["title"][:20] + "…" if len(d["title"]) > 20 else d["title"] for d in data]
        sold = [d["total_sold"] for d in data]
        
        # Natural size - will expand to fit width
        fig = Figure(figsize=(10, 5), facecolor=CARD)
        ax = fig.add_subplot(111)
        
        colors = [PRIMARY, PRIMARY_H, "#4A7A62", "#6A9A82", ACCENT]
        bars = ax.barh(titles[::-1], sold[::-1], color=colors[::-1], height=0.65)
        
        ax.set_facecolor(CARD)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(BORDER)
        ax.tick_params(axis='x', colors=FG_MUTED, labelsize=12)
        ax.tick_params(axis='y', colors=FG, labelsize=13)
        ax.set_xlabel("Copies Sold", fontsize=13, color=FG_MUTED)
        
        for bar, val in zip(bars, sold[::-1]):
            ax.text(val + (max(sold) * 0.02), bar.get_y() + bar.get_height()/2, 
                   f"{val}", va='center', fontsize=13, color=FG, fontweight='bold')
        
        fig.subplots_adjust(left=0.28, right=0.95, top=0.92, bottom=0.12)
        
        canvas = Canvas(fig)
        canvas.setMinimumHeight(300)
        layout.addWidget(canvas)
        return card

    def _revenue_trend(self):
        card, layout = self._chart_card("Revenue Trend — Last 7 Days")
        
        data = db.daily_revenue(7)
        if not data:
            lbl = QLabel("No revenue data yet")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(font(12, italic=True))
            lbl.setStyleSheet(f"color: {FG_MUTED}; padding: 60px;")
            layout.addWidget(lbl)
            return card
        
        dates = [d["sale_date"][-5:] for d in data]
        revenue = [d["revenue"] for d in data]
        
        fig = Figure(figsize=(10, 4.5), facecolor=CARD)
        ax = fig.add_subplot(111)
        
        ax.fill_between(range(len(dates)), revenue, alpha=0.2, color=PRIMARY)
        ax.plot(range(len(dates)), revenue, color=PRIMARY, linewidth=3, marker='o', 
               markersize=12, markerfacecolor=CARD, markeredgecolor=PRIMARY, markeredgewidth=2.5)
        
        ax.set_facecolor(CARD)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(BORDER)
        ax.spines['bottom'].set_color(BORDER)
        ax.tick_params(colors=FG_MUTED, labelsize=12)
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, fontsize=12)
        ax.set_ylabel("Revenue (Rs.)", fontsize=13, color=FG_MUTED)
        
        for x, y in zip(range(len(dates)), revenue):
            ax.annotate(f"Rs.{y:,.0f}", (x, y), textcoords="offset points", 
                       xytext=(0, 16), ha='center', fontsize=12, color=FG, fontweight='bold')
        
        fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.12)
        
        canvas = Canvas(fig)
        canvas.setMinimumHeight(280)
        layout.addWidget(canvas)
        return card

    def _genre_pie(self):
        card, layout = self._chart_card("Sales by Genre")
        
        data = db.sales_by_genre()
        data = [d for d in data if d["revenue"] > 0]
        
        if not data:
            lbl = QLabel("No genre data yet")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(font(12, italic=True))
            lbl.setStyleSheet(f"color: {FG_MUTED}; padding: 60px;")
            layout.addWidget(lbl)
            return card
        
        labels = [d["name"] for d in data]
        sizes = [d["revenue"] for d in data]
        colors = [PRIMARY, PRIMARY_H, ACCENT, "#4A7A62", "#6A9A82", "#8AA898"]
        
        fig = Figure(figsize=(6, 5), facecolor=CARD)
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=None, autopct='%1.0f%%',
            colors=colors[:len(sizes)],
            startangle=90,
            wedgeprops={'edgecolor': CARD, 'linewidth': 2},
            textprops={'fontsize': 13, 'color': WHITE, 'fontweight': 'bold'}
        )
        
        ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(0.9, 0.5),
                 fontsize=12, frameon=False, labelcolor=FG)
        
        fig.subplots_adjust(left=0.05, right=0.7, top=0.95, bottom=0.05)
        
        canvas = Canvas(fig)
        canvas.setMinimumHeight(280)
        layout.addWidget(canvas)
        return card

    def _top_three_list(self):
        card, layout = self._chart_card("Top 3 Favourites")
        
        data = db.top_books(3)
        if not data:
            lbl = QLabel("No sales data yet")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(font(12, italic=True))
            lbl.setStyleSheet(f"color: {FG_MUTED}; padding: 60px;")
            layout.addWidget(lbl)
            return card
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, book in enumerate(data):
            row = QHBoxLayout()
            row.setSpacing(SP_4)
            
            medal = QLabel(medals[i])
            medal.setFont(font(28))
            medal.setFixedWidth(50)
            medal.setAlignment(Qt.AlignCenter)
            row.addWidget(medal)
            
            info = QVBoxLayout()
            info.setSpacing(3)
            title = QLabel(book["title"])
            title.setFont(serif(16))
            title.setStyleSheet(f"color: {FG};")
            title.setWordWrap(True)
            author = QLabel(book["author"])
            author.setFont(font(12, italic=True))
            author.setStyleSheet(f"color: {FG_MUTED};")
            info.addWidget(title)
            info.addWidget(author)
            row.addLayout(info, stretch=1)
            
            sold = QLabel(f"{book['total_sold']}")
            sold.setFont(serif(26))
            sold.setStyleSheet(f"color: {ACCENT};")
            row.addWidget(sold)
            
            layout.addLayout(row)
            
            if i < len(data) - 1:
                layout.addWidget(HDivider())
        
        layout.addStretch()
        return card