"""inventory.py  ·  Andalus Booksellers — Inventory screen"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from assets.theme import *
from ui.widgets import (
    SectionHeader, SearchBar, BtnSecondary, BtnPrimary, GenreChip,
    LabeledField, HDivider, TABLE_STYLE, font, serif, apply_shadow
)
import utils.database as db


class InventoryScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._low_only = False
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(SP_5)

        # Top row
        top = QHBoxLayout()
        top.addWidget(SectionHeader("Inventory"))
        top.addStretch()
        self._search = SearchBar("Search inventory…")
        self._search.setMaximumWidth(260)
        self._search.textChanged.connect(lambda t: self.refresh(t or None))
        top.addWidget(self._search)
        self._chip_low = GenreChip("⚠  Low Stock Only")
        self._chip_low.toggled.connect(self._toggle_low)
        top.addWidget(self._chip_low)
        root.addLayout(top)

        # Mini stat cards row
        card_row = QHBoxLayout()
        card_row.setSpacing(SP_3)
        self._mc = {}
        for key, label, bg, fg in [
            ("total",   "Total Titles",  PRIMARY, WHITE),
            ("healthy", "Healthy Stock", SUCCESS_TINT, SUCCESS_FG),
            ("low",     "Low Stock",     DESTRUCTIVE_TINT, DESTRUCTIVE),
            ("out",     "Out of Stock",  "#FEE2E2", "#7F1D1D"),
        ]:
            f = self._mini_card(label, "0", bg, fg)
            self._mc[key] = f
            card_row.addWidget(f)
        root.addLayout(card_row)

        # ── Bulk Restock Bar ──────────────────────────────────────────────────
        self._bulk_bar = QFrame()
        self._bulk_bar.setStyleSheet(f"""
            QFrame {{
                background: {ACCENT_TINT};
                border-radius: {R_MD}px;
                border: 1px solid {ACCENT};
            }}
        """)
        self._bulk_bar.setVisible(False)
        
        bulk_lay = QHBoxLayout(self._bulk_bar)
        bulk_lay.setContentsMargins(SP_4, SP_2, SP_4, SP_2)
        bulk_lay.setSpacing(SP_3)
        
        self._selected_count = QLabel("0 books selected")
        self._selected_count.setFont(font(F_MD, bold=True))
        self._selected_count.setStyleSheet(f"color: {PRIMARY};")
        bulk_lay.addWidget(self._selected_count)
        
        sep = QLabel("│")
        sep.setStyleSheet(f"color: {ACCENT}; font-size: 14pt;")
        bulk_lay.addWidget(sep)
        
        bulk_lay.addWidget(QLabel("Add Qty:"))
        self._bulk_qty = LabeledField.spin(1, 9999)
        self._bulk_qty.setValue(10)
        self._bulk_qty.setFixedWidth(80)
        bulk_lay.addWidget(self._bulk_qty)
        
        btn_apply = BtnPrimary("📦 Bulk Restock")
        btn_apply.clicked.connect(self._bulk_restock)
        bulk_lay.addWidget(btn_apply)
        
        bulk_lay.addStretch()
        
        btn_clear = BtnSecondary("✕ Clear")
        btn_clear.clicked.connect(self._clear_selection)
        bulk_lay.addWidget(btn_clear)
        
        root.addWidget(self._bulk_bar)

        # Table
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(9)  # Added checkbox and discount columns
        self._tbl.setHorizontalHeaderLabels(["", "#", "Title", "Author", "Genre", "Price", "dis%", "Stock", "Add"])
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(False)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tbl.setFocusPolicy(Qt.NoFocus)
        self._tbl.verticalHeader().setDefaultSectionSize(54)
        self._tbl.setStyleSheet(TABLE_STYLE)

        h = self._tbl.horizontalHeader()
        for col, mode in [
            (0, QHeaderView.Fixed),   # Checkbox
            (1, QHeaderView.Fixed),   # #
            (2, QHeaderView.Stretch), # Title
            (3, QHeaderView.Stretch), # Author
            (4, QHeaderView.Stretch), # Genre
            (5, QHeaderView.Fixed),   # Price
            (6, QHeaderView.Fixed),   # Disc %
            (7, QHeaderView.Fixed),   # Stock
            (8, QHeaderView.Fixed),   # Restock
        ]:
            h.setSectionResizeMode(col, mode)
        
        self._tbl.setColumnWidth(0, 30)    # Checkbox
        self._tbl.setColumnWidth(1, 40)    # #
        self._tbl.setColumnWidth(5, 110)   # Price
        self._tbl.setColumnWidth(6, 80)    # Disc %
        self._tbl.setColumnWidth(7, 70)    # Stock
        self._tbl.setColumnWidth(8, 120)    # Restock
        
        root.addWidget(self._tbl, stretch=1)

    def _mini_card(self, label, value, bg, fg):
        f = QFrame()
        f.setMinimumHeight(76)
        f.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: {R_MD}px;
                border: none;
            }}
        """)
        apply_shadow(f, *SHADOW_SM)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(SP_5, SP_3, SP_5, SP_3)
        lay.setSpacing(2)
        lbl = QLabel(label.upper())
        lbl.setFont(font(F_XS, bold=True))
        lbl.setStyleSheet(f"color: {fg}; opacity: 0.75; letter-spacing: 0.02em;")
        val = QLabel(value)
        val.setFont(serif(F_3XL))
        val.setStyleSheet(f"color: {fg};")
        val.setObjectName("val")
        lay.addWidget(lbl)
        lay.addWidget(val)
        return f

    def _get_val(self, card):
        return card.findChild(QLabel, "val")

    # ── Bulk Restock Methods ─────────────────────────────────────────────────
    
    def _clear_selection(self):
        """Clear all checkboxes"""
        for i in range(self._tbl.rowCount()):
            widget = self._tbl.cellWidget(i, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk:
                    chk.setChecked(False)
        self._update_bulk_bar()

    def _update_bulk_bar(self):
        """Update bulk bar visibility and count"""
        selected = self._get_selected_books()
        count = len(selected)
        self._bulk_bar.setVisible(count > 0)
        self._selected_count.setText(f"{count} book{'s' if count != 1 else ''} selected")

    def _get_selected_books(self):
        """Get list of selected books with their data"""
        selected = []
        for i in range(self._tbl.rowCount()):
            widget = self._tbl.cellWidget(i, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    item = self._tbl.item(i, 1)  # # column has book ID
                    if item:
                        book_id = item.data(Qt.UserRole)
                        title_item = self._tbl.item(i, 2)
                        title = title_item.text() if title_item else ""
                        selected.append({'id': book_id, 'title': title})
        return selected

    def _bulk_restock(self):
        """Restock all selected books with the same quantity"""
        selected = self._get_selected_books()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one book.")
            return
        
        add_qty = self._bulk_qty.value()
        
        # Confirmation
        titles = [b['title'][:30] for b in selected[:5]]
        title_preview = ", ".join(titles)
        if len(selected) > 5:
            title_preview += f"\n... and {len(selected) - 5} more"
        
        reply = QMessageBox.question(
            self, "Confirm Bulk Restock",
            f"Add {add_qty} units to {len(selected)} books?\n\n{title_preview}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            for book in selected:
                db.restock(book['id'], add_qty)
            
            self.refresh()
            self._clear_selection()
            self._notify_main_win(f"Restocked {len(selected)} books.")

    def _notify_main_win(self, msg):
        p = self.parent()
        while p:
            if hasattr(p, 'show_toast'):
                p.show_toast(msg)
                break
            p = p.parent() if hasattr(p, 'parent') else None

    # ── Refresh ──────────────────────────────────────────────────────────────

    def refresh(self, search=None):
        books = db.get_books(search=search)
        healthy = sum(1 for b in books if b["quantity"] > STOCK_THRESHOLD)
        low     = sum(1 for b in books if 0 < b["quantity"] <= STOCK_THRESHOLD)
        out     = sum(1 for b in books if b["quantity"] == 0)
        self._get_val(self._mc["total"]).setText(str(len(books)))
        self._get_val(self._mc["healthy"]).setText(str(healthy))
        self._get_val(self._mc["low"]).setText(str(low))
        self._get_val(self._mc["out"]).setText(str(out))

        display = [b for b in books if b["quantity"] < 5] if self._low_only else books
        self._tbl.setRowCount(0)
        
        for i, b in enumerate(display):
            self._tbl.insertRow(i)
            
            # Column 0: Checkbox
            chk_widget = QWidget()
            chk_widget.setStyleSheet("background: transparent;")
            chk_lay = QHBoxLayout(chk_widget)
            chk_lay.setContentsMargins(0, 0, 0, 0)
            chk_lay.setAlignment(Qt.AlignCenter)
            chk = QCheckBox()
            chk.stateChanged.connect(self._update_bulk_bar)
            chk_lay.addWidget(chk)
            self._tbl.setCellWidget(i, 0, chk_widget)
            
            # Column 1: # (with book ID stored)
            n = QTableWidgetItem(str(i+1))
            n.setTextAlignment(Qt.AlignCenter)
            n.setFont(font(F_SM))
            n.setForeground(QColor(FG_MUTED))
            n.setData(Qt.UserRole, b["id"])
            self._tbl.setItem(i, 1, n)

            # Column 2: Title
            ti = QTableWidgetItem(b["title"])
            ti.setFont(serif(F_MD))
            self._tbl.setItem(i, 2, ti)
            
            # Column 3: Author
            ai = QTableWidgetItem(b["author"])
            ai.setFont(font(F_MD, italic=True))
            ai.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 3, ai)

            # Column 4: Genre pill
            genre_name = b.get("genre") or "—"
            gw = QLabel(genre_name)
            gw.setAlignment(Qt.AlignCenter)
            gw.setFont(serif(10, bold=False, italic=True))
            gw.setWordWrap(False)
            gw.setMinimumWidth(130)
            gw.setStyleSheet(f"""
                background: #F0F4F1; 
                color: {PRIMARY}; 
                border: 1px solid #D2DDD6;
                border-top-left-radius: 12px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 12px;
                border-bottom-left-radius: 4px;
                padding: 2px 8px;
            """)
            self._tbl.setCellWidget(i, 4, self._wrap(gw))
            
            # Column 5: Price (Professional strikethrough)
            price = b['price']
            disc_pct = b.get('discount_percent', 0)
            
            pl = QLabel()
            pl.setAlignment(Qt.AlignCenter)
            if disc_pct > 0:
                disc_price = price * (1 - disc_pct / 100)
                pl.setText(f"""
                    <div style='color: {DESTRUCTIVE}; font-weight: bold;'>Rs. {disc_price:,.0f}</div>
                    <div style='color: {FG_MUTED}; text-decoration: line-through; font-size: 9pt;'>Rs. {price:,.0f}</div>
                """)
            else:
                pl.setText(f"<div style='color: {FG};'>Rs. {price:,.0f}</div>")
            
            pl.setFont(font(F_MD))
            self._tbl.setCellWidget(i, 5, self._wrap(pl))

            # Column 6: Discount %
            disc_pct = b.get('discount_percent', 0)
            di = QTableWidgetItem(f"{disc_pct:.0f}%" if disc_pct > 0 else "—")
            di.setTextAlignment(Qt.AlignCenter)
            if disc_pct > 0:
                di.setForeground(QColor(DESTRUCTIVE))
                di.setFont(font(F_SM, bold=True))
            else:
                di.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 6, di)

            # Column 7: Stock pill
            qty = b["quantity"]
            if qty == 0:
                sw = QLabel("Out")
                sw.setAlignment(Qt.AlignCenter)
                sw.setFont(font(8, bold=True))
                sw.setStyleSheet(f"background:{DESTRUCTIVE_TINT}; color:{DESTRUCTIVE}; border-radius:8px; padding:2px 6px;")
            elif qty <= STOCK_THRESHOLD:
                sw = QLabel("▼" + str(qty))
                sw.setAlignment(Qt.AlignCenter)
                sw.setFont(font(9, bold=True))
                sw.setStyleSheet(f"""
                    background: {DESTRUCTIVE_TINT}; 
                    color: {DESTRUCTIVE}; 
                    border-radius: 8px; 
                    padding: 2px 6px;
                """)
            else:
                sw = QLabel(str(qty))
                sw.setAlignment(Qt.AlignCenter)
                sw.setFont(font(9, bold=True))
                sw.setStyleSheet(f"background:{SUCCESS_TINT}; color:{SUCCESS_FG}; border-radius:8px; padding:2px 8px;")

            sw.setFixedHeight(22)
            self._tbl.setCellWidget(i, 7, self._wrap(sw))

            # Column 8: Individual Restock button
            btn = BtnSecondary("+")
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, bid=b["id"], ttl=b["title"], q=qty: self._restock(bid, ttl, q))
            self._tbl.setCellWidget(i, 8, self._wrap(btn))
        
        self._update_bulk_bar()

    def _wrap(self, w):
        c = QWidget()
        c.setStyleSheet("background: transparent;")
        l = QHBoxLayout(c)
        l.setContentsMargins(4, 0, 4, 0)
        l.addStretch()
        l.addWidget(w)
        l.addStretch()
        return c

    def _toggle_low(self, checked):
        self._low_only = checked
        self.refresh()

    def _restock(self, book_id, title, current):
        dlg = _RestockDialog(title, current, self)
        if dlg.exec_():
            db.restock(book_id, dlg.added)
            self.refresh()
            self._notify_main_window()

    def _notify_main_window(self):
        """Tell main window to refresh all screens"""
        p = self.parent()
        while p:
            if hasattr(p, '_on_sale_done'):
                p._on_sale_done()
                break
            p = p.parent()


class _RestockDialog(QDialog):
    def __init__(self, title, current, parent=None):
        super().__init__(parent)
        self.added = 0
        self.setWindowTitle("Restock")
        self.setFixedWidth(340)
        self.setStyleSheet(f"background: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_8, SP_8, SP_8, SP_6)
        lay.setSpacing(SP_4)
        t = QLabel(f"Restock: {title}")
        t.setFont(serif(F_XL))
        t.setStyleSheet(f"color: {FG};")
        t.setWordWrap(True)
        lay.addWidget(t)
        c = QLabel(f"Current stock: {current}")
        c.setFont(font(F_MD))
        c.setStyleSheet(f"color: {FG_MUTED};")
        lay.addWidget(c)
        self._spin = LabeledField.spin(1, 9999)
        self._spin.setValue(10)
        lay.addWidget(LabeledField("Add Quantity", self._spin))
        row = QHBoxLayout()
        row.addStretch()
        cancel = BtnSecondary("Cancel")
        cancel.clicked.connect(self.reject)
        ok = BtnPrimary("Add Stock")
        ok.clicked.connect(self._ok)
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addLayout(row)

    def _ok(self):
        self.added = self._spin.value()
        self.accept()