"""requests.py  ·  Andalus Booksellers — Customer Wishlist & Pre-orders"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QLineEdit, QDateEdit, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from assets.theme import *
from ui.widgets import (
    SectionHeader, BtnPrimary, BtnSecondary, BtnDanger,
    LabeledField, TABLE_STYLE, font, serif, apply_shadow
)
import utils.database as db

class CustomerRequestsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_10, SP_6, SP_10, SP_6)
        lay.setSpacing(SP_5)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(SectionHeader("Wishlist & Customer Requests"))
        hdr.addStretch()
        
        btn_add = BtnPrimary("Add Request", "✨")
        btn_add.clicked.connect(self._add)
        hdr.addWidget(btn_add)
        lay.addLayout(hdr)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "", "Book Title", "Author", "Customer", "Contact", 
            "Request on", "Expected On", "Status"
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Author
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) 
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Author
        self._table.setColumnWidth(0, 40)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

        # Actions row
        act = QHBoxLayout()
        act.setSpacing(SP_3)
        
        btn_done = BtnPrimary("Mark as Fulfilled", "✓")
        btn_done.clicked.connect(self._mark_done)
        act.addWidget(btn_done)
        
        btn_del = BtnDanger("Remove Request", "✕")
        btn_del.clicked.connect(self._delete)
        act.addWidget(btn_del)
        
        act.addStretch()
        
        btn_all = BtnSecondary("Select All", "⚀")
        btn_all.clicked.connect(self._select_all_checks)
        act.addWidget(btn_all)
        
        btn_none = BtnSecondary("Clear", "✕")
        btn_none.clicked.connect(self._clear_all_checks)
        act.addWidget(btn_none)
        
        lay.addLayout(act)

    def refresh(self):
        reqs = db.get_customer_requests()
        self._table.setRowCount(len(reqs))
        for i, r in enumerate(reqs):
            # Checkbox
            ck = QTableWidgetItem()
            ck.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            ck.setCheckState(Qt.Unchecked)
            self._table.setItem(i, 0, ck)

            self._table.setItem(i, 1, QTableWidgetItem(r["book_title"]))
            self._table.setItem(i, 2, QTableWidgetItem(r["author"]))
            self._table.setItem(i, 3, QTableWidgetItem(r["customer_name"]))
            self._table.setItem(i, 4, QTableWidgetItem(r["customer_contact"]))
            self._table.setItem(i, 5, QTableWidgetItem(r["request_date"]))
            self._table.setItem(i, 6, QTableWidgetItem(r["expected_date"] or "TBD"))
            
            # Status pill styling
            status = r["status"]
            st_item = QTableWidgetItem(status)
            st_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 7, st_item)
            
            # Store ID in user data of the title item
            self._table.item(i, 1).setData(Qt.UserRole, r["id"])

    def _select_all_checks(self):
        for i in range(self._table.rowCount()):
            self._table.item(i, 0).setCheckState(Qt.Checked)

    def _clear_all_checks(self):
        for i in range(self._table.rowCount()):
            self._table.item(i, 0).setCheckState(Qt.Unchecked)

    def _get_checked_ids(self):
        ids = []
        for i in range(self._table.rowCount()):
            if self._table.item(i, 0).checkState() == Qt.Checked:
                ids.append(self._table.item(i, 1).data(Qt.UserRole))
        return ids

    def _add(self):
        dlg = RequestDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.data()
            db.add_customer_request(**d)
            self.refresh()
            QMessageBox.information(self, "Success", f"Request for \"{d['title']}\" saved.")

    def _mark_done(self):
        ids = self._get_checked_ids()
        if not ids:
            # Fallback to current row if nothing checked
            row = self._table.currentRow()
            if row >= 0:
                ids = [self._table.item(row, 1).data(Qt.UserRole)]
        
        if not ids:
            QMessageBox.warning(self, "No Selection", "Please check items or select a row.")
            return
            
        for rid in ids:
            db.update_request_status(rid, "Fulfilled")
        self.refresh()
        QMessageBox.information(self, "Success", f"Marked {len(ids)} requests as fulfilled.")

    def _delete(self):
        ids = self._get_checked_ids()
        if not ids:
            row = self._table.currentRow()
            if row >= 0:
                ids = [self._table.item(row, 1).data(Qt.UserRole)]

        if not ids:
            QMessageBox.warning(self, "No Selection", "Please check items or select a row.")
            return
            
        if QMessageBox.question(self, "Delete?", f"Remove {len(ids)} selected request(s)?", 
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for rid in ids:
                db.delete_customer_request(rid)
            self.refresh()
            QMessageBox.information(self, "Deleted", f"Successfully removed {len(ids)} requests.")

class RequestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Customer Request")
        self.setFixedWidth(450)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(SP_5, SP_5, SP_5, SP_5)
        lay.setSpacing(SP_4)

        self._title = LabeledField.edit("e.g. The Great Gatsby")
        lay.addWidget(LabeledField("Book Title", self._title))
        
        self._author = LabeledField.edit("Writer Name")
        lay.addWidget(LabeledField("Writer/Author", self._author))
        
        self._customer = LabeledField.edit("Customer Name")
        lay.addWidget(LabeledField("Customer Name", self._customer))
        
        self._contact = LabeledField.edit("Contact (Phone/Email)")
        lay.addWidget(LabeledField("Customer Contact", self._contact))
        
        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDate(QDate.currentDate().addDays(7))
        self._date.setMinimumHeight(38)
        self._date.setStyleSheet(f"QDateEdit {{ background:{SECONDARY}; border:1px solid {BORDER}; border-radius:{R_SM}px; padding:0 8px; }}")
        lay.addWidget(LabeledField("Expected Availability Date", self._date))

        lay.addSpacing(SP_4)
        btns = QHBoxLayout()
        bc = BtnSecondary("Cancel")
        bc.clicked.connect(self.reject)
        bs = BtnPrimary("Save Request", "✨")
        bs.clicked.connect(self.accept)
        btns.addWidget(bc)
        btns.addWidget(bs)
        lay.addLayout(btns)

    def data(self):
        return {
            "title": self._title.text().strip(),
            "author": self._author.text().strip(),
            "customer": self._customer.text().strip(),
            "contact": self._contact.text().strip(),
            "expected_date": self._date.date().toString("yyyy-MM-dd")
        }
