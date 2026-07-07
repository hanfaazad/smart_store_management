"""sales.py  ·  Andalus Booksellers — Point of Sale screen"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QMessageBox, QSizePolicy, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument, QFont

from assets.theme import *
from ui.widgets import (
    SectionHeader, BtnPrimary, BtnSecondary, BtnDanger, BtnGold, CartRow,
    LabeledField, HDivider, font, serif, apply_shadow
)
import utils.database as db
from datetime import datetime

TAX = 0.05


class SalesScreen(QWidget):
    completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cart   = {}
        self._books  = []
        self._order_n = 1
        self._empty_lbl = None
        self._cart_stretch = None
        self._applied_coupon = None  # Stores validated coupon
        self._build()
        self._reload_books()
        self._refresh_cart()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT: selector ────────────────────────────────────────────────
        left = QWidget()
        left.setStyleSheet(f"background: {BG};")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(SP_10, SP_6, SP_6, SP_6)
        ll.setSpacing(SP_5)

        ll.addWidget(SectionHeader("New Sale"))

        self._combo = LabeledField.combo()
        self._combo.setMinimumHeight(44)
        self._combo.currentIndexChanged.connect(self._on_select)
        ll.addWidget(LabeledField("Select Book", self._combo))

        self._detail = _BookDetail()
        ll.addWidget(self._detail)

        # Qty + Add row
        qrow = QHBoxLayout()
        qrow.setSpacing(SP_4)
        self._qty = LabeledField.spin(1, 999)
        self._qty.setMinimumHeight(44)

        btn_add = BtnPrimary("Add to Cart", "＋")
        btn_add.setMinimumHeight(44)
        btn_add.clicked.connect(self._add)

        qcol = QVBoxLayout()
        qcol.setSpacing(5)
        ql = QLabel("Quantity")
        ql.setFont(font(F_SM, bold=True))
        ql.setStyleSheet(f"color: {FG_MUTED}; letter-spacing: 0.06em;")
        qcol.addWidget(ql)
        qcol.addWidget(self._qty)
        qrow.addLayout(qcol)
        qrow.addWidget(btn_add, stretch=1)
        ll.addLayout(qrow)
        ll.addStretch()
        root.addWidget(left, stretch=1)

        vdiv = QFrame()
        vdiv.setFrameShape(QFrame.VLine)
        vdiv.setFixedWidth(1)
        vdiv.setStyleSheet(f"background: {BORDER};")
        root.addWidget(vdiv)

        # ── RIGHT: cart ───────────────────────────────────────────────────
        right = QWidget()
        right.setFixedWidth(CART_W)
        right.setStyleSheet(f"background: {CARD};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(SP_5, SP_6, SP_5, SP_6)
        rl.setSpacing(SP_3)

        ch = QHBoxLayout()
        ct = QLabel("Current Sale")
        ct.setFont(serif(F_XL))
        ct.setStyleSheet(f"color: {FG};")
        self._live = QLabel("● LIVE")
        self._live.setFont(font(F_XS, bold=True))
        self._live.setStyleSheet("color: #16A34A; letter-spacing: 0.12em;")
        ch.addWidget(ct)
        ch.addStretch()
        ch.addWidget(self._live)
        rl.addLayout(ch)

        self._order_lbl = QLabel(f"Order #SO-{self._order_n:04d}")
        self._order_lbl.setFont(font(F_SM))
        self._order_lbl.setStyleSheet(f"color: {FG_MUTED};")
        rl.addWidget(self._order_lbl)
        rl.addWidget(HDivider())

        self._cart_scroll = QScrollArea()
        self._cart_scroll.setWidgetResizable(True)
        self._cart_scroll.setFrameShape(QFrame.NoFrame)
        self._cart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cart_scroll.setStyleSheet("background: transparent;")

        self._cart_body = QWidget()
        self._cart_body.setStyleSheet("background: transparent;")
        self._cart_layout = QVBoxLayout(self._cart_body)
        self._cart_layout.setContentsMargins(0, 0, 0, 0)
        self._cart_layout.setSpacing(SP_2)

        self._cart_scroll.setWidget(self._cart_body)
        rl.addWidget(self._cart_scroll, stretch=1)

        rl.addWidget(HDivider())

        # Coupon input
        coupon_row = QHBoxLayout()
        coupon_row.setSpacing(SP_2)
        self._coupon_input = QLineEdit()
        self._coupon_input.setPlaceholderText("Coupon code")
        self._coupon_input.setFont(font(F_SM))
        self._coupon_input.setFixedHeight(32)
        self._coupon_input.setStyleSheet(f"""
            QLineEdit {{
                background: {SECONDARY};
                border: 1px solid {BORDER};
                border-radius: {R_SM}px;
                padding: 0 8px;
                color: {FG};
            }}
            QLineEdit:focus {{ border: 1px solid {PRIMARY}; }}
        """)
        coupon_row.addWidget(self._coupon_input)
        
        btn_apply = BtnSecondary("Apply")
        btn_apply.setFixedHeight(32)
        btn_apply.clicked.connect(self._apply_coupon)
        coupon_row.addWidget(btn_apply)
        
        btn_remove = BtnDanger("✕")
        btn_remove.setFixedSize(32, 32)
        btn_remove.clicked.connect(self._remove_coupon)
        coupon_row.addWidget(btn_remove)
        
        rl.addLayout(coupon_row)
        
        self._coupon_status = QLabel("")
        self._coupon_status.setFont(font(F_XS))
        self._coupon_status.setStyleSheet(f"color: {SUCCESS_FG};")
        rl.addWidget(self._coupon_status)

        rl.addWidget(HDivider())

        # Totals
        self._lbl_sub   = self._total_row("Subtotal",          rl)
        self._lbl_tax   = self._total_row(f"Tax ({int(TAX*100)}%)", rl)
        self._lbl_disc  = self._total_row("Discount",          rl)
        self._lbl_disc.setVisible(False)
        rl.addSpacing(SP_1)
        self._lbl_total = self._total_row("TOTAL", rl, big=True)
        rl.addSpacing(SP_3)

        btn_clear = BtnSecondary("Clear Cart")
        btn_clear.clicked.connect(self._clear)
        rl.addWidget(btn_clear)

        self._btn_confirm = BtnGold("Confirm Sale  ✓")
        self._btn_confirm.clicked.connect(self._confirm)
        rl.addWidget(self._btn_confirm)

        root.addWidget(right)

    def _total_row(self, label, parent_lay, big=False):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFont(font(F_LG if big else F_MD, bold=big))
        lbl.setStyleSheet(f"color: {FG if big else FG_MUTED};")
        val = QLabel("Rs. 0")
        val.setFont(font(F_XL if big else F_MD, bold=big))
        val.setStyleSheet(f"color: {ACCENT if big else FG};")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(val)
        parent_lay.addLayout(row)
        if label.startswith("Discount"):
            val.setStyleSheet(f"color: {DESTRUCTIVE};")
        return val

    # ── Logic ──────────────────────────────────────────────────────────────
    
    def refresh(self):
        """Ensure book list is fresh when navigating to this screen"""
        self._reload_books()

    def _reload_books(self):
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("— Select a book —", None)
        self._books = db.get_books()
        for b in self._books:
            price = b['price']
            disc_pct = b.get('discount_percent', 0)
            price_text = f"Rs. {price:,.0f}"
            if disc_pct > 0:
                disc_price = price * (1 - disc_pct / 100)
                price_text = f"Rs. {disc_price:,.0f} (Was Rs. {price:,.0f})"
                
            label = f"{b['title']}  ·  {price_text}  ·  {b['quantity']} in stock"
            self._combo.addItem(label, b["id"])
        self._combo.blockSignals(False)

    def _on_select(self, _):
        bid = self._combo.currentData()
        if not bid:
            self._detail.clear()
            return
        book = next((b for b in self._books if b["id"] == bid), None)
        if book:
            self._detail.set_book(book)
            self._qty.setMaximum(book["quantity"])
            self._qty.setValue(1)

    def _add(self):
        bid = self._combo.currentData()
        if not bid:
            QMessageBox.warning(self, "No Book Selected", "Please select a book first.")
            return
        book = next((b for b in self._books if b["id"] == bid), None)
        if not book:
            return
        qty = self._qty.value()
        already = self._cart.get(bid, {}).get("qty", 0)
        if already + qty > book["quantity"]:
            QMessageBox.warning(self, "Insufficient Stock",
                f"Only {book['quantity']} copies of \"{book['title']}\" available.\nAlready in cart: {already}")
            return
        if bid in self._cart:
            self._cart[bid]["qty"] += qty
        else:
            price = book["price"]
            disc_pct = book.get("discount_percent", 0)
            if disc_pct > 0:
                price = price * (1 - disc_pct / 100)
                
            self._cart[bid] = {
                "title": book["title"], 
                "price": price, 
                "qty": qty, 
                "discount_pct": disc_pct
            }
        self._refresh_cart()
        self._combo.setCurrentIndex(0)
        self._detail.clear()
        
    def _refresh_cart(self):
        while self._cart_layout.count():
            item = self._cart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        if not self._cart:
            self._empty_lbl = QLabel("Cart is empty.\nSelect a book and add it.")
            self._empty_lbl.setAlignment(Qt.AlignCenter)
            self._empty_lbl.setFont(font(F_MD, italic=True))
            self._empty_lbl.setStyleSheet(f"color: {FG_MUTED}; padding: 40px 0;")
            self._cart_layout.addWidget(self._empty_lbl)
            self._cart_layout.addStretch()
            self._set_totals(0)
            return

        for bid, info in self._cart.items():
            row = CartRow(bid, info["title"], info["price"], info["qty"], info.get("discount_pct", 0))
            row.removed.connect(self._remove)
            row.qty_changed.connect(self._change_qty)
            self._cart_layout.addWidget(row)
        self._cart_layout.addStretch()

        sub = sum(v["price"] * v["qty"] for v in self._cart.values())
        self._set_totals(sub)

    def _remove(self, bid):
        self._cart.pop(bid, None)
        self._refresh_cart()

    def _change_qty(self, bid, new_qty):
        if bid not in self._cart:
            return
        book = next((b for b in self._books if b["id"] == bid), None)
        if book and new_qty > book["quantity"]:
            QMessageBox.warning(self, "Insufficient Stock", f"Only {book['quantity']} copies available.")
            return
        self._cart[bid]["qty"] = new_qty
        sub = sum(v["price"] * v["qty"] for v in self._cart.values())
        self._set_totals(sub)

    def _set_totals(self, sub):
        tax = sub * TAX
        discount = 0
        
        if self._applied_coupon:
            discount = (sub + tax) * self._applied_coupon["percent"] / 100
        
        total = sub + tax - discount
        
        self._lbl_sub.setText(f"Rs. {sub:,.0f}")
        self._lbl_tax.setText(f"Rs. {tax:,.0f}")
        
        if discount > 0:
            self._lbl_disc.setText(f"Rs. -{discount:,.0f}")
            self._lbl_disc.setVisible(True)
        else:
            self._lbl_disc.setVisible(False)
            
        self._lbl_total.setText(f"Rs. {total:,.0f}")

    def _apply_coupon(self):
        code = self._coupon_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Empty", "Please enter a coupon code.")
            return
        
        coupon = db.validate_coupon(code)
        if coupon:
            self._applied_coupon = coupon
            self._coupon_status.setText(f"✓ {coupon['percent']:.0f}% off applied!")
            self._coupon_status.setStyleSheet(f"color: {SUCCESS_FG};")
            sub = sum(v["price"] * v["qty"] for v in self._cart.values())
            self._set_totals(sub)
        else:
            self._coupon_status.setText("✕ Invalid or expired code")
            self._coupon_status.setStyleSheet(f"color: {DESTRUCTIVE};")

    def _remove_coupon(self):
        self._applied_coupon = None
        self._coupon_input.clear()
        self._coupon_status.setText("")
        sub = sum(v["price"] * v["qty"] for v in self._cart.values())
        self._set_totals(sub)

    def _clear(self):
        self._cart.clear()
        self._applied_coupon = None
        self._coupon_input.clear()
        self._coupon_status.setText("")
        self._refresh_cart()

    def _print_receipt(self, items, subtotal, tax, discount, total, order_no):
        """Open print dialog for receipt"""
        try:
            emp = db.get_employee()
            now = datetime.now()
            
            text = f"""
📖 ANDALUS BOOKSELLERS
   Purveyors of Fine Literature
========================================
Order: {order_no}
Date: {now.strftime('%d %b %Y, %I:%M %p')}
Cashier: {emp['name']}
========================================

ITEM                      QTY     AMOUNT
----------------------------------------
"""
            for item in items:
                book = self._cart[item['book_id']]
                title = book['title'][:22]
                qty = item['qty']
                price = item['unit_price']
                line_total = qty * price
                text += f"{title:<24} {qty:>3} x {price:>7,.0f} = {line_total:>8,.0f}\n"
            
            text += f"""
----------------------------------------
Subtotal:      Rs. {subtotal:>10,.0f}
Tax (5%):      Rs. {tax:>10,.0f}"""
            
            if discount > 0:
                text += f"""
Discount:     Rs. -{discount:>10,.0f}"""
            
            text += f"""
========================================
TOTAL:         Rs. {total:>10,.0f}
========================================

    Thank you for shopping with us!
      All sales final unless defective.
"""
            
            doc = QTextDocument()
            doc.setPlainText(text)
            doc.setDefaultFont(QFont("Courier New", 9))
            
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec_() == QPrintDialog.Accepted:
                doc.print_(printer)
                return True
            return False
            
        except ImportError:
            QMessageBox.warning(self, "Print Error", "Print support not available.")
            return False

    def _confirm(self):
        if not self._cart:
            QMessageBox.warning(self, "Empty Cart", "Add books before confirming.")
            return

        items = [{"book_id": bid, "qty": v["qty"], "unit_price": v["price"]}
                 for bid, v in self._cart.items()]
        sub   = sum(i["qty"] * i["unit_price"] for i in items)
        tax   = sub * TAX
        discount = 0
        
        if self._applied_coupon:
            discount = (sub + tax) * self._applied_coupon["percent"] / 100
        
        total = sub + tax - discount

        lines = "\n".join(
            f"  • {self._cart[i['book_id']]['title']}  ×{i['qty']}  =  Rs. {i['qty'] * i['unit_price']:,.0f}"
            for i in items
        )
        
        coupon_msg = ""
        if self._applied_coupon:
            coupon_msg = f"\nCoupon: {self._applied_coupon['code']} ({self._applied_coupon['percent']:.0f}% off)"
            coupon_msg += f"\nDiscount: -Rs. {discount:,.0f}"
        
        mb = QMessageBox(self)
        mb.setWindowTitle("Confirm Sale")
        mb.setText(f"Finalise this transaction?\n\n{lines}\n{coupon_msg}")
        mb.setInformativeText(
            f"Subtotal: Rs. {sub:,.0f}\nTax (5%): Rs. {tax:,.0f}\nTotal:    Rs. {total:,.0f}"
        )
        mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        mb.setDefaultButton(QMessageBox.Yes)
        if mb.exec_() != QMessageBox.Yes:
            return

        try:
            res = db.process_sale(items)
            alerts = res.get("alerts", [])
        except ValueError as e:
            QMessageBox.critical(self, "Sale Failed", str(e))
            return

        # Mark coupon as used
        if self._applied_coupon:
            db.apply_coupon(self._applied_coupon["id"])

        self._order_n += 1
        order_no = f"SO-{self._order_n:04d}"
        self._order_lbl.setText(f"Order #{order_no}")
        
        # Notify main window to refresh and show toast
        self.completed.emit()
        
        if alerts:
            self._show_low_stock_warning(alerts)

        self._print_receipt(items, sub, tax, discount, total, order_no)
        
        self._cart.clear()
        self._applied_coupon = None
        self._coupon_input.clear()
        self._coupon_status.setText("")
        self._reload_books()
        self._refresh_cart()
        self._detail.clear()
        self.completed.emit()

    def _show_low_stock_warning(self, alerts):
        """Show a premium popup for low stock items"""
        msg = QMessageBox(self)
        msg.setWindowTitle("⚠ Low Stock Alert")
        msg.setIcon(QMessageBox.Warning)
        
        titles = "\n".join([f"  • {a['title']} (Only {a['quantity']} left)" for a in alerts])
        msg.setText("The following items are running low on stock:")
        msg.setInformativeText(titles)
        
        # Style it a bit if possible, though QMessageBox is limited.
        # We can at least use a custom icon or just the standard warning.
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def pre_select_book(self, book_id):
        """Called from dashboard when user clicks a book card."""
        self._reload_books()
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == book_id:
                self._combo.setCurrentIndex(i)
                # Auto-focus the quantity so the user can just press Enter
                self._qty.setFocus()
                self._qty.selectAll()
                break


class _BookDetail(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(340)
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: none;
                border-radius: {R_MD}px;
            }}
        """)
        apply_shadow(self, *SHADOW_SM)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(SP_4, SP_4, SP_4, SP_4)
        lay.setSpacing(SP_8)

        self._thumb = QLabel()
        self._thumb.setFixedSize(240, 320)
        self._thumb.setAlignment(Qt.AlignCenter)
        self._thumb.setStyleSheet(f"background: {SECONDARY}; border-radius: {R_SM}px;")
        self._thumb.setText("📖")
        self._thumb.setFont(font(64))
        lay.addWidget(self._thumb)

        col = QVBoxLayout()
        col.setSpacing(SP_3)
        self._t = QLabel("Select a book…")
        self._t.setFont(serif(F_3XL))
        self._t.setStyleSheet(f"color: {FG};")
        self._t.setWordWrap(True)
        self._a = QLabel("")
        self._a.setFont(font(F_XL, italic=True))
        self._a.setStyleSheet(f"color: {FG_MUTED};")
        self._g = QLabel("")
        self._g.setFont(font(F_MD, bold=True))
        self._g.setStyleSheet(f"color: {ACCENT}; letter-spacing: 0.16em;")
        self._p = QLabel("")
        self._p.setFont(serif(48))
        self._p.setStyleSheet(f"color: {PRIMARY};")
        
        self._old_p = QLabel("")
        self._old_p.setFont(font(F_LG))
        self._old_p.setStyleSheet(f"color: {FG_MUTED}; text-decoration: line-through;")
        self._old_p.setVisible(False)
        
        self._s = QLabel("")
        self._s.setFont(font(F_LG, bold=True))
        for w in (self._t, self._a, self._g, self._p, self._old_p, self._s):
            col.addWidget(w)
        col.addStretch()
        lay.addLayout(col, stretch=1)

    def set_book(self, b):
        self._t.setText(b.get("title", ""))
        self._a.setText(b.get("author", ""))
        genre = b.get("genre")
        self._g.setText(genre.upper() if genre else "")
        # Price display with discount
        original_price = b.get("price", 0)
        disc_pct = b.get("discount_percent", 0)
        if disc_pct > 0:
            discounted_price = original_price * (1 - disc_pct / 100)
            self._p.setText(f"Rs. {discounted_price:,.0f}")
            self._p.setStyleSheet(f"color: {DESTRUCTIVE};")
            
            self._old_p.setText(f"Original: Rs. {original_price:,.0f}")
            self._old_p.setVisible(True)
            
            # Optionally update genre label to include discount tag or similar
            self._g.setText(f"{self._g.text()}  ·  {int(disc_pct)}% OFF")
        else:
            self._p.setText(f"Rs. {original_price:,.0f}")
            self._p.setStyleSheet(f"color: {PRIMARY};")
            self._old_p.setVisible(False)
        qty = b.get("quantity", 0)
        if qty == 0:
            self._s.setText("✕  Out of stock")
            self._s.setStyleSheet(f"color: {DESTRUCTIVE};")
        elif qty <= STOCK_THRESHOLD:
            self._s.setText(f"⚠  Only {qty} left")
            self._s.setStyleSheet(f"color: {DESTRUCTIVE};")
        else:
            self._s.setText(f"✓  {qty} in stock")
            self._s.setStyleSheet(f"color: {SUCCESS_FG};")
        ip = b.get("image_path", "")
        if ip and os.path.exists(ip):
            pix = QPixmap(ip).scaled(240, 320, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self._thumb.setPixmap(pix)
            self._thumb.setText("")
        else:
            self._thumb.setPixmap(QPixmap())
            self._thumb.setText("📖")

    def clear(self):
        self._t.setText("Select a book…")
        for w in (self._a, self._g, self._p, self._s):
            w.setText("")
        self._old_p.setText("")
        self._old_p.setVisible(False)
        self._thumb.setPixmap(QPixmap())
        self._thumb.setText("📖")