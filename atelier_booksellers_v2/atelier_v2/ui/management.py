"""management.py  ·  Genres, Suppliers, Sales History, Coupons screens"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QInputDialog, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from assets.theme import *
from ui.widgets import (
    SectionHeader, SearchBar, BtnPrimary, BtnSecondary, BtnDanger,
    LabeledField, HDivider, TABLE_STYLE, font, serif, apply_shadow
)
import utils.database as db
import csv


# ── GENRES ────────────────────────────────────────────────────────────────────

LIST_STYLE = f"""
    QListWidget {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: {R_MD}px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 12px 18px;
        border-bottom: 1px solid {BORDER};
        color: {FG};
        font-size: {F_MD}pt;
    }}
    QListWidget::item:selected {{
        background: {ACCENT_TINT};
        color: {PRIMARY};
    }}
    QListWidget::item:hover {{ background: {MUTED}; }}
"""


class GenresScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(SP_5)

        top = QHBoxLayout()
        top.addWidget(SectionHeader("Genres"))
        top.addStretch()
        btn = BtnPrimary("Add Genre", "＋")
        btn.clicked.connect(self._add)
        top.addWidget(btn)
        root.addLayout(top)

        info = QLabel("Genres categorise your catalogue and power the filter system.")
        info.setFont(font(F_MD, italic=True))
        info.setStyleSheet(f"color: {FG_MUTED};")
        root.addWidget(info)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._list.setStyleSheet(LIST_STYLE)
        root.addWidget(self._list, stretch=1)

        btn_row = QHBoxLayout()
        self._delete_btn = BtnDanger("Delete Selected")
        self._delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        btn_select_all = BtnSecondary("Select All")
        btn_select_all.clicked.connect(self._select_all)
        btn_row.addWidget(btn_select_all)
        btn_clear = BtnSecondary("Clear")
        btn_clear.clicked.connect(self._clear_selection)
        btn_row.addWidget(btn_clear)
        root.addLayout(btn_row)

    def refresh(self):
        self._list.clear()
        for g in db.get_genres():
            item = QListWidgetItem(f"  {g['name']}")
            item.setData(Qt.UserRole, g["id"])
            item.setFont(serif(F_LG))
            self._list.addItem(item)

    def _add(self):
        dlg = _InputDialog("Add Genre", "Genre Name:", self)
        if dlg.exec_() and dlg.value().strip():
            try:
                db.add_genre(dlg.value().strip())
                self.refresh()
                self._notify_main_window()
            except ValueError as e:
                QMessageBox.warning(self, "Duplicate", str(e))

    def _notify_main_window(self):
        p = self.parent()
        while p:
            if hasattr(p, "_on_sale_done"):
                p._on_sale_done()
                break
            p = p.parent() if hasattr(p, "parent") else None

    def _delete_selected(self):
        items = self._list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Select Genres", "Please select at least one genre.")
            return
        count = len(items)
        names = [item.text().strip() for item in items[:5]]
        name_preview = ", ".join(names)
        if count > 5:
            name_preview += f"... and {count - 5} more"
        reply = QMessageBox.question(
            self, "Delete Genres",
            f"Delete {count} genre(s)?\n\n{name_preview}\n\nBooks in these genres will lose their genre tag.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for item in items:
                db.delete_genre(item.data(Qt.UserRole))
            self.refresh()
            self._notify_main_win(f"{count} genre(s) deleted.")

    def _notify_main_win(self, msg):
        p = self.parent()
        while p:
            if hasattr(p, 'show_toast'):
                p.show_toast(msg)
                break
            p = p.parent() if hasattr(p, 'parent') else None

    def _select_all(self):
        self._list.selectAll()

    def _clear_selection(self):
        self._list.clearSelection()


# ── SUPPLIERS ─────────────────────────────────────────────────────────────────

class SuppliersScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(SP_5)

        top = QHBoxLayout()
        top.addWidget(SectionHeader("Suppliers"))
        top.addStretch()
        btn = BtnPrimary("Add Supplier", "＋")
        btn.clicked.connect(self._add)
        top.addWidget(btn)
        root.addLayout(top)

        self._list = QListWidget()
        self._list.setStyleSheet(LIST_STYLE)
        root.addWidget(self._list, stretch=1)

        del_btn = BtnDanger("Delete Selected Supplier")
        del_btn.clicked.connect(self._delete)
        root.addWidget(del_btn)

    def refresh(self):
        self._list.clear()
        for s in db.get_suppliers():
            item = QListWidgetItem(f"  {s['name']}   ·   {s['contact'] or '—'}")
            item.setData(Qt.UserRole, s["id"])
            item.setFont(font(F_LG))
            self._list.addItem(item)

    def _add(self):
        dlg = _SupplierDialog(self)
        if dlg.exec_():
            n, c = dlg.values()
            if n.strip():
                db.add_supplier(n.strip(), c.strip())
                self.refresh()

    def _delete(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "Select Supplier", "Please select a supplier first.")
            return
        if QMessageBox.question(self, "Delete Supplier",
            "Delete this supplier?\nLinked books will lose their supplier tag.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            db.delete_supplier(item.data(Qt.UserRole))
            self.refresh()


# ── SALES HISTORY ─────────────────────────────────────────────────────────────

class SalesHistoryScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(SP_5)

        top = QHBoxLayout()
        top.addWidget(SectionHeader("Sales History"))
        top.addStretch()
        self._search = SearchBar("Search by book title…")
        self._search.setMaximumWidth(260)
        self._search.textChanged.connect(lambda t: self.refresh(t or None))
        top.addWidget(self._search)
        btn_csv = BtnSecondary("⬇ Export CSV")
        btn_csv.clicked.connect(self._export_csv)
        top.addWidget(btn_csv)
        btn_return = BtnPrimary("↩ Process Return")
        btn_return.clicked.connect(self._process_selected_return)
        top.addWidget(btn_return)
        root.addLayout(top)

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(8)
        self._tbl.setHorizontalHeaderLabels(["#", "Title", "Author", "Qty", "Price", "Total", "Date", ""])
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(False)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tbl.setFocusPolicy(Qt.NoFocus)
        self._tbl.verticalHeader().setDefaultSectionSize(50)
        self._tbl.setStyleSheet(TABLE_STYLE)

        h = self._tbl.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        for i in [3, 4, 5, 6, 7]:
            h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self._tbl.setColumnWidth(0, 44)
        self._tbl.setColumnWidth(7, 60)
        root.addWidget(self._tbl, stretch=1)

        self._summary = QLabel()
        self._summary.setFont(font(F_MD))
        self._summary.setStyleSheet(f"color: {FG_MUTED};")
        root.addWidget(self._summary)

    def _export_csv(self):
        sales = db.get_sales(limit=10000)
        if not sales:
            QMessageBox.information(self, "No Data", "No sales records to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Sales CSV", "andalus_sales.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Title', 'Author', 'Qty', 'Unit Price', 'Total', 'Date', 'Time'])
                for s in sales:
                    writer.writerow([s['id'], s['title'], s['author'], s['qty_sold'], s['unit_price'], s['total'], s['sale_date'], s['sale_time']])
            self._notify_main_win(f"Exported to {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def refresh(self, search=None):
        sales = db.get_sales(search=search)
        pos = [s for s in sales if s["qty_sold"] > 0]
        neg = [s for s in sales if s["qty_sold"] < 0]
        gross = sum(s["total"] for s in pos)
        refunds = sum(abs(s["total"]) for s in neg)
        net = gross - refunds
        self._summary.setText(f"  {len(pos)} sales  ·  {len(neg)} returns  ·  Gross: Rs. {gross:,.0f}  ·  Refunds: Rs. {refunds:,.0f}  ·  Net: Rs. {net:,.0f}")

        self._tbl.setRowCount(0)
        for i, s in enumerate(sales):
            self._tbl.insertRow(i)
            is_return = s["qty_sold"] < 0
            item = QTableWidgetItem(str(i + 1))
            item.setData(Qt.UserRole, s["id"])
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(font(F_SM))
            item.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 0, item)
            title_text = ("↩ " if is_return else "") + s["title"]
            ti = QTableWidgetItem(title_text)
            ti.setFont(serif(F_MD))
            ti.setForeground(QColor(DESTRUCTIVE if is_return else FG))
            self._tbl.setItem(i, 1, ti)
            ai = QTableWidgetItem(s["author"])
            ai.setFont(font(F_MD, italic=True))
            ai.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 2, ai)
            qty_text = str(abs(s["qty_sold"]))
            qi = QTableWidgetItem(qty_text)
            qi.setTextAlignment(Qt.AlignCenter)
            if is_return:
                qi.setForeground(QColor(DESTRUCTIVE))
            self._tbl.setItem(i, 3, qi)
            self._tbl.setItem(i, 4, QTableWidgetItem(f"Rs. {s['unit_price']:,.0f}"))
            total_val = abs(s["total"])
            prefix = "-" if is_return else ""
            tot = QTableWidgetItem(f"{prefix}Rs. {total_val:,.0f}")
            tot.setFont(font(F_MD, bold=True))
            tot.setForeground(QColor(DESTRUCTIVE if is_return else ACCENT))
            self._tbl.setItem(i, 5, tot)
            di = QTableWidgetItem(s["sale_date"])
            di.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 6, di)
            if not is_return:
                btn = QPushButton("↩")
                btn.setFixedSize(28, 28)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(f"background:{DESTRUCTIVE_TINT}; color:{DESTRUCTIVE}; border:none; border-radius:4px; font-weight:bold; font-size:12pt;")
                btn.clicked.connect(lambda _, sid=s["id"]: self._do_return(sid))
                self._tbl.setCellWidget(i, 7, self._center_widget(btn))

    def _center_widget(self, w):
        c = QWidget()
        c.setStyleSheet("background: transparent;")
        l = QHBoxLayout(c)
        l.setContentsMargins(0, 0, 0, 0)
        l.addStretch()
        l.addWidget(w)
        l.addStretch()
        return c

    def _process_selected_return(self):
        row = self._tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Row", "Please select a sale row first.")
            return
        item = self._tbl.item(row, 0)
        if not item:
            return
        self._do_return(item.data(Qt.UserRole))

    def _do_return(self, sale_id):
        sale = db.get_sale_by_id(sale_id)
        if not sale:
            QMessageBox.warning(self, "Error", f"Sale #{sale_id} not found.")
            return
        if sale["qty_sold"] <= 0:
            QMessageBox.warning(self, "Error", "Cannot return a return record.")
            return
        qty, ok = QInputDialog.getInt(self, "Return Quantity", f"How many copies of:\n\n\"{sale['title']}\"\n\nOriginally sold: {sale['qty_sold']}\nUnit price: Rs. {sale['unit_price']:,.0f}", value=1, min=1, max=sale["qty_sold"])
        if not ok:
            return
        try:
            result = db.process_return(sale_id, qty)
            QMessageBox.information(self, "Return Successful ✓", f"Returned {qty} cop{'y' if qty == 1 else 'ies'} of:\n\"{result['title']}\"\n\nRefund amount: Rs. {result['refund']:,.0f}\nStock has been updated.")
            self.refresh()
            p = self.parent()
            while p:
                if hasattr(p, "_on_sale_done"):
                    p._on_sale_done()
                    break
                p = p.parent() if hasattr(p, "parent") else None
        except ValueError as e:
            QMessageBox.critical(self, "Return Failed", str(e))


# ── COUPON MANAGEMENT ──────────────────────────────────────────────────────────

class CouponScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(SP_5)

        top = QHBoxLayout()
        top.addWidget(SectionHeader("Discount Coupons"))
        top.addStretch()
        btn_add = BtnPrimary("Create Coupon", "＋")
        btn_add.clicked.connect(self._add_coupon)
        top.addWidget(btn_add)
        root.addLayout(top)

        info = QLabel("Create coupon codes that customers can use at checkout.")
        info.setFont(font(F_MD, italic=True))
        info.setStyleSheet(f"color: {FG_MUTED};")
        root.addWidget(info)

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(7)
        self._tbl.setHorizontalHeaderLabels(["", "Code", "Discount", "Used", "Max Uses", "Status", "Actions"])
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(False)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tbl.setFocusPolicy(Qt.NoFocus)
        self._tbl.setStyleSheet(TABLE_STYLE)

        h = self._tbl.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        self._tbl.setColumnWidth(0, 40)
        for i in [2, 3, 4, 5, 6]:
            h.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        root.addWidget(self._tbl, stretch=1)
        
        # Bulk actions
        bulk = QHBoxLayout()
        bulk.setSpacing(SP_3)
        
        btn_act = BtnPrimary("Activate Selected", "✓")
        btn_act.clicked.connect(lambda: self._bulk_toggle(True))
        bulk.addWidget(btn_act)
        
        btn_deact = BtnSecondary("Deactivate Selected", "⊘")
        btn_deact.clicked.connect(lambda: self._bulk_toggle(False))
        bulk.addWidget(btn_deact)
        
        btn_bulk_del = BtnDanger("Delete Selected", "✕")
        btn_bulk_del.clicked.connect(self._bulk_delete)
        bulk.addWidget(btn_bulk_del)
        
        bulk.addStretch()
        
        btn_all = BtnSecondary("Select All", "⚀")
        btn_all.clicked.connect(self._select_all_checks)
        bulk.addWidget(btn_all)
        
        btn_none = BtnSecondary("Clear", "✕")
        btn_none.clicked.connect(self._clear_all_checks)
        bulk.addWidget(btn_none)
        
        root.addLayout(bulk)

    def refresh(self):
        coupons = db.get_all_discounts()
        self._tbl.setRowCount(0)
        for i, c in enumerate(coupons):
            self._tbl.insertRow(i)
            
            # Checkbox
            ck = QTableWidgetItem()
            ck.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            ck.setCheckState(Qt.Unchecked)
            self._tbl.setItem(i, 0, ck)

            code_item = QTableWidgetItem(c["code"])
            code_item.setData(Qt.UserRole, c["id"]) # Store ID here for bulk actions
            code_item.setFont(font(F_MD, bold=True))
            code_item.setForeground(QColor(PRIMARY))
            self._tbl.setItem(i, 1, code_item)
            
            self._tbl.setItem(i, 2, QTableWidgetItem(f"{c['percent']:.0f}%"))
            self._tbl.setItem(i, 3, QTableWidgetItem(str(c["used_count"])))
            
            max_uses = str(c["max_uses"]) if c["max_uses"] > 0 else "∞"
            self._tbl.setItem(i, 4, QTableWidgetItem(max_uses))
            
            # Professional Status Logic
            is_depleted = c["max_uses"] > 0 and c["used_count"] >= c["max_uses"]
            
            if is_depleted:
                status = "Fully Redeemed"
                color = FG_MUTED
            elif not c["active"]:
                status = "Disabled"
                color = DESTRUCTIVE
            else:
                status = "Active"
                color = SUCCESS_FG
                
            st = QTableWidgetItem(status)
            st.setForeground(QColor(color))
            if is_depleted:
                st.setFont(font(F_SM, italic=True))
            self._tbl.setItem(i, 5, st)
            
            # Action buttons
            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(2, 2, 2, 2)
            al.setSpacing(4)
            
            toggle_btn = QPushButton()
            toggle_btn.setFixedSize(24, 24)
            toggle_btn.setCursor(Qt.PointingHandCursor)
            
            # Determine color based on status
            if is_depleted:
                bg = "#CBD5E1"  # Muted slate gray
                tip = "Coupon limit reached"
            else:
                bg = SUCCESS_FG if c["active"] else DESTRUCTIVE
                tip = "Click to " + ("Disable" if c["active"] else "Enable")
                
            toggle_btn.setToolTip(tip)
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    border: 2px solid {WHITE};
                    border-radius: 12px;
                }}
                QPushButton:hover {{ 
                    background: {bg};
                    border-color: {ACCENT};
                }}
            """)
            toggle_btn.clicked.connect(lambda _, cid=c["id"], active=c["active"]: self._toggle(cid, active))
            al.addWidget(toggle_btn)
            
            del_btn = QPushButton("Del")
            del_btn.setFixedHeight(28)
            del_btn.setFont(font(8))
            del_btn.setStyleSheet(f"background:{DESTRUCTIVE_TINT}; color:{DESTRUCTIVE}; border:none; border-radius:4px; padding:0 8px;")
            del_btn.clicked.connect(lambda _, cid=c["id"], code=c["code"]: self._delete(cid, code))
            al.addWidget(del_btn)
            
            self._tbl.setCellWidget(i, 6, aw)

    def _add_coupon(self):
        dlg = _CouponDialog(self)
        if dlg.exec_():
            code, percent, max_uses = dlg.values()
            try:
                db.create_discount_code(code, percent, max_uses)
                self.refresh()
                QMessageBox.information(self, "Created", f"Coupon '{code}' created successfully!")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _toggle(self, coupon_id, current_active):
        db.toggle_discount_status(coupon_id, not current_active)
        self.refresh()

    def _delete(self, coupon_id, code):
        if QMessageBox.question(self, "Delete Coupon", f"Delete coupon '{code}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            db.delete_discount(coupon_id)
            self.refresh()

    def _bulk_toggle(self, activate):
        ids = self._get_checked_ids()
        if not ids:
            row = self._tbl.currentRow()
            if row >= 0:
                ids = [self._tbl.item(row, 1).data(Qt.UserRole)]
        
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please check coupons or select a row.")
            return
            
        for cid in ids:
            db.toggle_discount_status(cid, activate)
        self.refresh()
        status = "activated" if activate else "deactivated"
        QMessageBox.information(self, "Success", f"Successfully {status} {len(ids)} coupons.")

    def _bulk_delete(self):
        ids = self._get_checked_ids()
        if not ids:
            row = self._tbl.currentRow()
            if row >= 0:
                ids = [self._tbl.item(row, 1).data(Qt.UserRole)]

        if not ids:
            QMessageBox.warning(self, "No Selection", "Please check coupons or select a row.")
            return
            
        if QMessageBox.question(self, "Delete Coupons", f"Delete {len(ids)} selected coupon(s)?", 
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            for rid in ids:
                db.delete_discount(rid)
            self.refresh()
            QMessageBox.information(self, "Deleted", f"Successfully deleted {len(ids)} coupons.")

    def _select_all_checks(self):
        for i in range(self._tbl.rowCount()):
            self._tbl.item(i, 0).setCheckState(Qt.Checked)

    def _clear_all_checks(self):
        for i in range(self._tbl.rowCount()):
            self._tbl.item(i, 0).setCheckState(Qt.Unchecked)

    def _get_checked_ids(self):
        ids = []
        for i in range(self._tbl.rowCount()):
            if self._tbl.item(i, 0).checkState() == Qt.Checked:
                ids.append(self._tbl.item(i, 1).data(Qt.UserRole))
        return ids


# ── COUPON DIALOG ─────────────────────────────────────────────────────────────

class _CouponDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Coupon Code")
        self.setFixedWidth(380)
        self.setStyleSheet(f"background: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_8, SP_8, SP_8, SP_6)
        lay.setSpacing(SP_4)
        
        lay.addWidget(QLabel("Create a new discount coupon"))
        
        self._code = LabeledField.edit("Coupon code (e.g., SAVE10)")
        self._percent = LabeledField.spin(1, 100)
        self._percent.setValue(10)
        self._max_uses = LabeledField.spin(0, 9999)
        self._max_uses.setValue(0)
        self._max_uses.setToolTip("0 = unlimited")
        
        lay.addWidget(LabeledField("Code *", self._code))
        lay.addWidget(LabeledField("Discount %", self._percent))
        lay.addWidget(LabeledField("Max Uses (0=∞)", self._max_uses))
        
        row = QHBoxLayout()
        row.addStretch()
        c = BtnSecondary("Cancel")
        c.clicked.connect(self.reject)
        ok = BtnPrimary("Create Coupon")
        ok.clicked.connect(self.accept)
        row.addWidget(c)
        row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        return self._code.text().strip(), self._percent.value(), self._max_uses.value()


# ── DIALOGS ───────────────────────────────────────────────────────────────────

class _InputDialog(QDialog):
    def __init__(self, title, label, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(320)
        self.setStyleSheet(f"background: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_8, SP_8, SP_8, SP_6)
        lay.setSpacing(SP_4)
        self._edit = LabeledField.edit()
        lay.addWidget(LabeledField(label, self._edit))
        row = QHBoxLayout()
        row.addStretch()
        c = BtnSecondary("Cancel")
        c.clicked.connect(self.reject)
        ok = BtnPrimary("Save")
        ok.clicked.connect(self.accept)
        row.addWidget(c)
        row.addWidget(ok)
        lay.addLayout(row)

    def value(self):
        return self._edit.text()


class _SupplierDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Supplier")
        self.setFixedWidth(360)
        self.setStyleSheet(f"background: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_8, SP_8, SP_8, SP_6)
        lay.setSpacing(SP_4)
        self._name = LabeledField.edit("Supplier name")
        self._contact = LabeledField.edit("+XX-XXX-XXXXXXX")
        lay.addWidget(LabeledField("Name *", self._name))
        lay.addWidget(LabeledField("Contact", self._contact))
        row = QHBoxLayout()
        row.addStretch()
        c = BtnSecondary("Cancel")
        c.clicked.connect(self.reject)
        ok = BtnPrimary("Save Supplier")
        ok.clicked.connect(self.accept)
        row.addWidget(c)
        row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        return self._name.text(), self._contact.text()