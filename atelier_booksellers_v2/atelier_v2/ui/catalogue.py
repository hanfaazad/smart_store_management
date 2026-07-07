"""catalogue.py  ·  Andalus Booksellers — Catalogue / Book Management"""

import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFileDialog, QMessageBox, QCheckBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor

from assets.theme import *
from ui.widgets import (
    SectionHeader, SearchBar, BtnPrimary, BtnSecondary, BtnDanger,
    LabeledField, TABLE_STYLE, font, serif, apply_shadow, HDivider
)
import utils.database as db

IMGS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "books")
os.makedirs(IMGS, exist_ok=True)


class CatalogueScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        root.setSpacing(SP_5)

        # Header row
        top = QHBoxLayout()
        top.addWidget(SectionHeader("Book Catalogue"))
        top.addStretch()
        self._search = SearchBar("Search by title or author…")
        self._search.setMaximumWidth(280)
        self._search.textChanged.connect(lambda t: self.refresh(t or None))
        top.addWidget(self._search)
        btn = BtnPrimary("Add Book", "＋")
        btn.clicked.connect(self._add)
        top.addWidget(btn)
        root.addLayout(top)

        # ── Bulk Edit Bar ──────────────────────────────────────────────────────
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
        
        # Separator
        sep = QLabel("│")
        sep.setStyleSheet(f"color: {ACCENT}; font-size: 14pt;")
        bulk_lay.addWidget(sep)
        
        # Bulk action buttons
        btn_price = BtnSecondary("💰 Set Price")
        btn_price.clicked.connect(self._bulk_set_price)
        bulk_lay.addWidget(btn_price)
        
        btn_qty = BtnSecondary("📦 Set Quantity")
        btn_qty.clicked.connect(self._bulk_set_quantity)
        bulk_lay.addWidget(btn_qty)
        
        btn_genre = BtnSecondary("🏷 Set Genre")
        btn_genre.clicked.connect(self._bulk_set_genre)
        bulk_lay.addWidget(btn_genre)
        
        btn_supplier = BtnSecondary("🏭 Set Supplier")
        btn_supplier.clicked.connect(self._bulk_set_supplier)
        bulk_lay.addWidget(btn_supplier)

        btn_disc = BtnSecondary("🏷 Set Discount")
        btn_disc.clicked.connect(self._bulk_set_discount)
        bulk_lay.addWidget(btn_disc)
        
        bulk_lay.addStretch()
        
        btn_clear = BtnSecondary("✕ Clear")
        btn_clear.clicked.connect(self._clear_selection)
        bulk_lay.addWidget(btn_clear)
        
        root.addWidget(self._bulk_bar)

        # ── Table ──────────────────────────────────────────────────────────────
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(10)
        self._tbl.setHorizontalHeaderLabels(["", "#", "📷", "Title", "Author", "Genre", "Price", "dis%", "Stock", "Actions"])
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(False)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tbl.setFocusPolicy(Qt.NoFocus)
        self._tbl.verticalHeader().setDefaultSectionSize(64)
        self._tbl.setStyleSheet(TABLE_STYLE)

        h = self._tbl.horizontalHeader()
        for col, mode in [
            (0, QHeaderView.Fixed),   # Checkbox
            (1, QHeaderView.Fixed),   # #
            (2, QHeaderView.Fixed),   # Cover
            (3, QHeaderView.Stretch), # Title
            (4, QHeaderView.Stretch), # Author
            (5, QHeaderView.Stretch), # Genre
            (6, QHeaderView.Fixed),   # Price
            (7, QHeaderView.Fixed),   # Disc %
            (8, QHeaderView.Fixed),   # Stock
            (9, QHeaderView.Fixed),   # Actions
        ]:
            h.setSectionResizeMode(col, mode)
        
        self._tbl.setColumnWidth(0, 30)    # Checkbox
        self._tbl.setColumnWidth(1, 40)    # #
        self._tbl.setColumnWidth(2, 50)    # Cover
        self._tbl.setColumnWidth(5, 120)   # Genre
        self._tbl.setColumnWidth(6, 100)   # Price
        self._tbl.setColumnWidth(7, 60)    # Disc %
        self._tbl.setColumnWidth(8, 70)    # Stock
        self._tbl.setColumnWidth(9, 140)   # Actions

        root.addWidget(self._tbl, stretch=1)

    # ── Bulk Edit Methods ─────────────────────────────────────────────────────
    
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
        selected = self._get_selected_ids()
        count = len(selected)
        self._bulk_bar.setVisible(count > 0)
        self._selected_count.setText(f"{count} book{'s' if count != 1 else ''} selected")

    def _get_selected_ids(self):
        """Get list of selected book IDs"""
        selected = []
        for i in range(self._tbl.rowCount()):
            widget = self._tbl.cellWidget(i, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    item = self._tbl.item(i, 1)
                    if item:
                        selected.append(item.data(Qt.UserRole))
        return selected

    def _bulk_set_price(self):
        """Set price for all selected books"""
        selected = self._get_selected_ids()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one book.")
            return
            
        price, ok = QInputDialog.getDouble(
            self, "Bulk Set Price", 
            f"Enter new price for {len(selected)} books (Rs.):",
            min=0, max=999999
        )
        if ok:
            for book_id in selected:
                book = db.get_book(book_id)
                if book:
                    db.update_book(
                        book_id, book['title'], book['author'], price,
                        book['quantity'], book['genre_id'], book['supplier_id'],
                        book['image_path'], book.get('discount_percent', 0)
                    )
            self.refresh()
            self._notify_main_win(f"Updated price for {len(selected)} books.")

    def _bulk_set_quantity(self):
        """Set quantity for all selected books"""
        selected = self._get_selected_ids()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one book.")
            return
            
        qty, ok = QInputDialog.getInt(
            self, "Bulk Set Quantity", 
            f"Enter new quantity for {len(selected)} books:",
            min=0, max=9999, value=1
        )
        if ok:
            alerts = []
            for book_id in selected:
                book = db.get_book(book_id)
                if book:
                    # Check if stock dropped to or below threshold
                    if qty <= STOCK_THRESHOLD and book.get('quantity', 0) > STOCK_THRESHOLD:
                        alerts.append(book['title'])
                    db.update_book(
                        book_id, book['title'], book['author'], book['price'],
                        qty, book['genre_id'], book['supplier_id'],
                        book['image_path'], book.get('discount_percent', 0)
                    )
            self.refresh()
            if alerts:
                titles = "\n".join([f"  • {t}" for t in alerts])
                QMessageBox.warning(self, "⚠ Low Stock Alert", 
                    f"The following books were set to low stock (Qty: {qty}):\n\n{titles}")
            else:
                self._notify_main_win(f"Updated quantity for {len(selected)} books.")

    def _bulk_set_genre(self):
        """Set genre for all selected books"""
        selected = self._get_selected_ids()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one book.")
            return
            
        genres = db.get_genres()
        if not genres:
            QMessageBox.warning(self, "No Genres", "Please add genres first.")
            return
            
        items = [g['name'] for g in genres]
        item, ok = QInputDialog.getItem(
            self, "Bulk Set Genre",
            f"Select genre for {len(selected)} books:",
            items, 0, False
        )
        if ok and item:
            genre_id = next((g['id'] for g in genres if g['name'] == item), None)
            for book_id in selected:
                book = db.get_book(book_id)
                if book:
                    db.update_book(
                        book_id, book['title'], book['author'], book['price'],
                        book['quantity'], genre_id, book['supplier_id'],
                        book['image_path'], book.get('discount_percent', 0)
                    )
            self.refresh()
            self._notify_main_win(f"Updated genre for {len(selected)} books.")

    def _bulk_set_supplier(self):
        """Set supplier for all selected books"""
        selected = self._get_selected_ids()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one book.")
            return
            
        suppliers = db.get_suppliers()
        if not suppliers:
            QMessageBox.warning(self, "No Suppliers", "Please add suppliers first.")
            return
            
        items = [s['name'] for s in suppliers]
        item, ok = QInputDialog.getItem(
            self, "Bulk Set Supplier",
            f"Select supplier for {len(selected)} books:",
            items, 0, False
        )
        if ok and item:
            supplier_id = next((s['id'] for s in suppliers if s['name'] == item), None)
            for book_id in selected:
                book = db.get_book(book_id)
                if book:
                    db.update_book(
                        book_id, book['title'], book['author'], book['price'],
                        book['quantity'], book['genre_id'], supplier_id,
                        book['image_path'], book.get('discount_percent', 0)
                    )
            self.refresh()
            self._notify_main_win(f"Updated supplier for {len(selected)} books.")

    def _bulk_set_discount(self):
        """Set discount percent for all selected books"""
        selected = self._get_selected_ids()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one book.")
            return
            
        disc, ok = QInputDialog.getInt(
            self, "Bulk Set Discount", 
            f"Enter discount percentage for {len(selected)} books (%):",
            min=0, max=100, value=10
        )
        if ok:
            for book_id in selected:
                book = db.get_book(book_id)
                if book:
                    db.update_book(
                        book_id, book['title'], book['author'], book['price'],
                        book['quantity'], book['genre_id'], book['supplier_id'],
                        book['image_path'], disc
                    )
            self.refresh()
            self._notify_main_win(f"Updated discount for {len(selected)} books.")

    def _notify_main_win(self, msg):
        p = self.parent()
        while p:
            if hasattr(p, 'show_toast'):
                p.show_toast(msg)
                break
            p = p.parent() if hasattr(p, 'parent') else None

    # ── Refresh ────────────────────────────────────────────────────────────────

    def refresh(self, search=None):
        books = db.get_books(search=search)
        self._tbl.setRowCount(0)

        for i, b in enumerate(books):
            self._tbl.insertRow(i)
            self._tbl.setRowHeight(i, 64)

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

            # Column 2: Cover thumbnail
            thumb = QLabel()
            thumb.setAlignment(Qt.AlignCenter)
            thumb.setFixedSize(44, 54)
            thumb.setStyleSheet(f"border-radius: {R_XS}px; background: {SECONDARY};")
            ip = b.get("image_path", "")
            if ip and os.path.exists(ip):
                pix = QPixmap(ip).scaled(44, 54, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                thumb.setPixmap(pix)
            else:
                thumb.setText("📖")
                thumb.setFont(font(18))
            self._tbl.setCellWidget(i, 2, self._wrap(thumb))

            # Column 3: Title
            ti = QTableWidgetItem(b["title"])
            ti.setFont(serif(F_MD))
            ti.setForeground(QColor(FG))
            self._tbl.setItem(i, 3, ti)

            # Column 4: Author
            ai = QTableWidgetItem(b["author"])
            ai.setFont(font(F_MD, italic=True))
            ai.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 4, ai)

            # Column 5: Genre pill
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
            self._tbl.setCellWidget(i, 5, self._wrap(gw))

            # Column 6: Price (Professional strikethrough)
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
            self._tbl.setCellWidget(i, 6, self._wrap(pl))

            # Column 7: Discount %
            disc_pct = b.get('discount_percent', 0)
            di = QTableWidgetItem(f"{disc_pct:.0f}%" if disc_pct > 0 else "—")
            di.setTextAlignment(Qt.AlignCenter)
            if disc_pct > 0:
                di.setForeground(QColor(DESTRUCTIVE))
                di.setFont(font(F_SM, bold=True))
            else:
                di.setForeground(QColor(FG_MUTED))
            self._tbl.setItem(i, 7, di)

            # Column 8: Stock pill
            qty = b["quantity"]
            if qty == 0:
                sw = QLabel("Out")
                sw.setAlignment(Qt.AlignCenter)
                sw.setFont(font(8, bold=True))
                sw.setStyleSheet(f"background:{DESTRUCTIVE_TINT}; color:{DESTRUCTIVE}; border-radius:8px; padding:2px 6px;")
            elif qty <= STOCK_THRESHOLD:
                sw = QLabel("▼  " + str(qty))
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
            self._tbl.setCellWidget(i, 8, self._wrap(sw))

            # Column 9: Actions
            aw = QWidget()
            aw.setStyleSheet("background: transparent;")
            al = QHBoxLayout(aw)
            al.setContentsMargins(2, 8, 2, 8)
            al.setSpacing(4)
            
            bi = BtnSecondary("")
            bi.setText("P")
            bi.setFixedSize(30, 30)
            bi.setStyleSheet(bi.styleSheet() + "padding: 0px; font-size: 12pt;")
            bi.clicked.connect(lambda _, bid=b["id"]: self._upload_img(bid))
            
            be = BtnPrimary("")
            be.setText("✍️")
            be.setFixedSize(30, 30)
            be.setStyleSheet(be.styleSheet() + "padding: 0px; font-size: 12pt;")
            be.clicked.connect(lambda _, book=b: self._edit(book))
            
            bd = BtnDanger("")
            bd.setText("✕")
            bd.setFixedSize(30, 30)
            bd.setStyleSheet(bd.styleSheet() + "padding: 0px; font-size: 12pt;")
            bd.clicked.connect(lambda _, bid=b["id"], ttl=b["title"]: self._delete(bid, ttl))
            
            for w in (bi, be, bd):
                al.addWidget(w)
            self._tbl.setCellWidget(i, 9, aw)

        self._update_bulk_bar()

    def _wrap(self, w):
        c = QWidget()
        c.setStyleSheet("background: transparent;")
        l = QHBoxLayout(c)
        l.setContentsMargins(0, 0, 0, 0)
        l.addStretch()
        l.addWidget(w)
        l.addStretch()
        return c

    def _upload_img(self, book_id):
        path, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "",
                                               "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not path:
            return
        ext = os.path.splitext(path)[1]
        dest = os.path.join(IMGS, f"book_{book_id}{ext}")
        shutil.copy2(path, dest)
        db.set_book_image(book_id, dest)
        self.refresh()

    def _add(self):
        dlg = BookDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            db.add_book(**d)
            self.refresh()

    def _edit(self, book):
        dlg = BookDialog(book=book, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            db.update_book(book["id"], **d)
            self.refresh()

            
            # Notify if stock dropped to or below threshold
            if d['quantity'] <= STOCK_THRESHOLD and book.get('quantity', 0) > STOCK_THRESHOLD:
                QMessageBox.warning(self, "⚠ Low Stock Alert", 
                    f"\"{d['title']}\" is now low on stock (Qty: {d['quantity']}).")

    def _delete(self, book_id, title):
        mb = QMessageBox(self)
        mb.setWindowTitle("Delete Book")
        mb.setText(f"Delete \"{title}\"?")
        mb.setInformativeText("This action cannot be undone.")
        mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        mb.setDefaultButton(QMessageBox.No)
        if mb.exec_() == QMessageBox.Yes:
            warning = db.delete_book(book_id)
            if warning:
                QMessageBox.information(self, "Deleted", warning)
            self.refresh()


class BookDialog(QDialog):
    def __init__(self, book=None, parent=None):
        super().__init__(parent)
        self._book = book
        self.setWindowTitle("Edit Book" if book else "Add New Book")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"background: {BG};")
        self._build()
        if book:
            self._populate()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_8, SP_8, SP_8, SP_6)
        lay.setSpacing(SP_5)

        title_lbl = QLabel("Edit Book" if self._book else "Add New Book")
        title_lbl.setFont(serif(F_2XL))
        title_lbl.setStyleSheet(f"color: {FG};")
        lay.addWidget(title_lbl)
        lay.addWidget(HDivider())

        self._title = LabeledField.edit("Book title")
        self._author = LabeledField.edit("Author name")
        lay.addWidget(LabeledField("Title *", self._title))
        lay.addWidget(LabeledField("Author *", self._author))

        row1 = QHBoxLayout()
        row1.setSpacing(SP_4)
        self._price = LabeledField.edit("e.g. 1200")
        self._qty = LabeledField.spin(0, 9999)
        self._discount = LabeledField.spin(0, 100)
        row1.addWidget(LabeledField("Price (Rs.) *", self._price))
        row1.addWidget(LabeledField("Quantity *", self._qty))
        row1.addWidget(LabeledField("Discount %", self._discount))
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(SP_4)
        self._genre = LabeledField.combo()
        self._supplier = LabeledField.combo()
        self._genres = db.get_genres()
        self._suppliers = db.get_suppliers()
        for g in self._genres:
            self._genre.addItem(g["name"], g["id"])
        for s in self._suppliers:
            self._supplier.addItem(s["name"], s["id"])
        row2.addWidget(LabeledField("Genre", self._genre))
        row2.addWidget(LabeledField("Supplier", self._supplier))
        lay.addLayout(row2)

        lay.addSpacing(SP_2)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = BtnSecondary("Cancel")
        cancel.clicked.connect(self.reject)
        save = BtnPrimary("Save Book")
        save.clicked.connect(self._validate)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _populate(self):
        b = self._book
        self._title.setText(b.get("title", ""))
        self._author.setText(b.get("author", ""))
        self._price.setText(str(b.get("price", "")))
        self._qty.setValue(b.get("quantity", 0))
        self._discount.setValue(int(b.get("discount_percent", 0)))
        for i, g in enumerate(self._genres):
            if g["id"] == b.get("genre_id"):
                self._genre.setCurrentIndex(i)
        for i, s in enumerate(self._suppliers):
            if s["id"] == b.get("supplier_id"):
                self._supplier.setCurrentIndex(i)

    def _validate(self):
        if not self._title.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            return
        if not self._author.text().strip():
            QMessageBox.warning(self, "Validation Error", "Author is required.")
            return
        try:
            v = float(self._price.text().strip())
            if v <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Enter a valid positive price.")
            return
        self.accept()

    def data(self):
        return dict(
            title=self._title.text().strip(),
            author=self._author.text().strip(),
            price=float(self._price.text().strip()),
            quantity=self._qty.value(),
            discount_percent=self._discount.value(),
            genre_id=self._genre.currentData(),
            supplier_id=self._supplier.currentData(),
            image_path=self._book.get("image_path", "") if self._book else "",
        )