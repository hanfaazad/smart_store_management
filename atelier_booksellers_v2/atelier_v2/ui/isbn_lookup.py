"""isbn_lookup.py  ·  Andalus Booksellers — Visual ISBN & API Lookup"""

import os, sys
import requests
import re
import shutil
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QMessageBox, QLineEdit, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap

from assets.theme import *
from ui.widgets import (
    SectionHeader, BtnPrimary, BtnSecondary, LabeledField, 
    HDivider, font, serif, apply_shadow, StatusLabel
)
import utils.database as db

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "books")
os.makedirs(IMAGES_DIR, exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "atelier.db")


class FetchWorker(QThread):
    """Background thread for API calls"""
    finished = pyqtSignal(object)
    
    def __init__(self, isbn):
        super().__init__()
        self.isbn = isbn
        
    def run(self):
        data = self._fetch_by_isbn(self.isbn)
        self.finished.emit(data)
    
    def _fetch_by_isbn(self, isbn):
        """Fetch book details from OpenLibrary including genre"""
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            key = f"ISBN:{isbn}"
            if key in data:
                book = data[key]
                cover_url = book.get('cover', {}).get('large', '') if book.get('cover') else ''
                
                # Download cover if available
                image_path = ""
                if cover_url:
                    image_path = self._download_cover(cover_url, isbn)
                
                # Extract subjects/genres
                subjects = []
                if book.get('subjects'):
                    for subject in book['subjects'][:5]:
                        subjects.append(subject.get('name', ''))
                
                # Try to match with existing genres
                genre_id = self._match_genre(subjects)
                genre_name = self._get_genre_name(genre_id)
                
                return {
                    'title': book.get('title', ''),
                    'author': book['authors'][0]['name'] if book.get('authors') else '',
                    'isbn': isbn,
                    'image_path': image_path,
                    'subjects': subjects,
                    'genre_id': genre_id,
                    'genre_name': genre_name
                }
        except Exception as e:
            print(f"API Error: {e}")
        return None
    
    def _match_genre(self, subjects):
        """Match OpenLibrary subjects to database genres"""
        if not subjects:
            return None
        
        # Get existing genres from database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        genres = conn.execute("SELECT id, name FROM genres").fetchall()
        conn.close()
        
        # Genre keyword mapping
        genre_keywords = {
            'Literary Fiction': ['fiction', 'novel', 'literary', 'classic'],
            'Mystery': ['mystery', 'crime', 'thriller', 'detective', 'suspense'],
            'Science Fiction': ['science fiction', 'sci-fi', 'fantasy', 'dystopian'],
            'Romance': ['romance', 'love', 'romantic'],
            'Biography': ['biography', 'memoir', 'autobiography', 'life'],
            'History': ['history', 'historical', 'war', 'ancient'],
            'Poetry': ['poetry', 'poems', 'verse'],
            'Philosophy': ['philosophy', 'philosophical', 'ethics', 'logic'],
            'Self-Help': ['self-help', 'self help', 'personal development', 'psychology'],
        }
        
        # Check each subject against keywords
        for subject in subjects:
            subject_lower = subject.lower()
            for genre_name, keywords in genre_keywords.items():
                if any(kw in subject_lower for kw in keywords):
                    # Find matching genre ID
                    for g in genres:
                        if g['name'].lower() == genre_name.lower():
                            return g['id']
        
        # Default to Literary Fiction if no match
        for g in genres:
            if g['name'].lower() in ['literary fiction', 'fiction']:
                return g['id']
        
        return None
    
    def _get_genre_name(self, genre_id):
        """Get genre name from ID"""
        if not genre_id:
            return None
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        genre = conn.execute("SELECT name FROM genres WHERE id = ?", (genre_id,)).fetchone()
        conn.close()
        return genre['name'] if genre else None
    
    def _download_cover(self, url, isbn):
        """Download cover image"""
        try:
            resp = requests.get(url, stream=True, timeout=10)
            if resp.status_code == 200:
                filename = f"isbn_{isbn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = os.path.join(IMAGES_DIR, filename)
                with open(filepath, 'wb') as f:
                    resp.raw.decode_content = True
                    shutil.copyfileobj(resp.raw, f)
                return filepath
        except:
            pass
        return ""


class ISBNLookupScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fetched_data = None
        self.worker = None
        self._build()
        
    def _build(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(SP_10, SP_6, SP_10, SP_10)
        root.setSpacing(SP_5)

        root.addWidget(SectionHeader("ISBN Book Lookup"))

        # ── Step Cards ──────────────────────────────────────────────────────
        steps_row = QHBoxLayout()
        steps_row.setSpacing(SP_3)
        step_data = [
            ("1", "Find ISBN on the back cover near the barcode"),
            ("2", "Type it below and click Fetch Details"),
            ("3", "Review info, set price & quantity"),
            ("4", "Click Add to Catalogue"),
        ]
        for num, text in step_data:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {ACCENT_TINT};
                    border-radius: {R_MD}px;
                    border: none;
                }}
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(SP_4, SP_4, SP_4, SP_4)
            cl.setSpacing(SP_3)

            circle = QLabel(num)
            circle.setFixedSize(38, 38)
            circle.setAlignment(Qt.AlignCenter)
            circle.setFont(font(F_MD, bold=True))
            circle.setStyleSheet(f"""
                background: {PRIMARY};
                color: white;
                border-radius: 19px;
            """)

            lbl = QLabel(text)
            lbl.setFont(font(F_MD))
            lbl.setStyleSheet(f"color: {FG};")
            lbl.setWordWrap(True)

            cl.addWidget(circle)
            cl.addWidget(lbl, stretch=1)
            steps_row.addWidget(card, stretch=1)

        root.addLayout(steps_row)

        # ── ISBN Input Card ─────────────────────────────────────────────────
        input_card = QFrame()
        input_card.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border-radius: {R_MD}px;
                border: 1px solid {BORDER};
            }}
        """)

        input_lay = QVBoxLayout(input_card)
        input_lay.setContentsMargins(SP_5, SP_4, SP_5, SP_4)
        input_lay.setSpacing(SP_3)

        input_title = QLabel("ISBN NUMBER")
        input_title.setFont(font(F_SM, bold=True))
        input_title.setStyleSheet(f"color: {ACCENT}; letter-spacing: 0.18em;")
        input_lay.addWidget(input_title)

        isbn_row = QHBoxLayout()
        isbn_row.setSpacing(SP_3)

        self._isbn_input = QLineEdit()
        self._isbn_input.setPlaceholderText("e.g. 9780141036144")
        self._isbn_input.setMinimumHeight(50)
        self._isbn_input.setFont(font(F_LG))
        self._isbn_input.setStyleSheet(f"""
            QLineEdit {{
                background: {SECONDARY};
                border: 1px solid {BORDER};
                border-radius: {R_SM}px;
                padding: 0 15px;
                color: {FG};
                font-family: "Courier New", monospace;
                font-size: {F_LG}pt;
                letter-spacing: 0.06em;
            }}
            QLineEdit:focus {{
                border: 2px solid {PRIMARY};
                background: {CARD};
            }}
        """)
        self._isbn_input.returnPressed.connect(self._fetch)
        isbn_row.addWidget(self._isbn_input)

        self._fetch_btn = BtnPrimary("Search", "🔍")
        self._fetch_btn.setMinimumHeight(50)
        self._fetch_btn.setMinimumWidth(130)
        self._fetch_btn.clicked.connect(self._fetch)
        isbn_row.addWidget(self._fetch_btn)

        input_lay.addLayout(isbn_row)

        hint = QLabel("Try: 9780141036144 (1984)  ·  9780061120084 (To Kill a Mockingbird)")
        hint.setFont(font(F_SM, italic=True))
        hint.setStyleSheet(f"color: {FG_MUTED};")
        input_lay.addWidget(hint)

        self._status = StatusLabel()
        input_lay.addWidget(self._status)

        root.addWidget(input_card)

        # ── Preview Card ────────────────────────────────────────────────────
        self._preview_card = QFrame()
        self._preview_card.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border-radius: {R_MD}px;
                border: 1px solid {BORDER};
            }}
        """)
        self._preview_card.setVisible(False)

        preview_lay = QHBoxLayout(self._preview_card)
        preview_lay.setContentsMargins(SP_4, SP_4, SP_4, SP_4)
        preview_lay.setSpacing(SP_4)

        self._cover_lbl = QLabel()
        self._cover_lbl.setFixedSize(120, 160)
        self._cover_lbl.setAlignment(Qt.AlignCenter)
        self._cover_lbl.setStyleSheet(f"background: {SECONDARY}; border-radius: {R_MD}px;")
        self._cover_lbl.setText("📖")
        self._cover_lbl.setFont(font(36))
        preview_lay.addWidget(self._cover_lbl)

        details_lay = QVBoxLayout()
        details_lay.setSpacing(SP_2)

        self._title_lbl = QLabel("")
        self._title_lbl.setFont(serif(F_2XL))
        self._title_lbl.setStyleSheet(f"color: {FG};")
        self._title_lbl.setWordWrap(True)

        self._author_lbl = QLabel("")
        self._author_lbl.setFont(font(F_LG, italic=True))
        self._author_lbl.setStyleSheet(f"color: {FG_MUTED};")

        self._genre_lbl = QLabel("")
        self._genre_lbl.setFont(font(F_SM, bold=True))
        self._genre_lbl.setStyleSheet(f"""
            background: {ACCENT_TINT};
            color: {PRIMARY};
            border-radius: 10px;
            padding: 4px 12px;
        """)
        self._genre_lbl.setFixedHeight(28)

        details_lay.addWidget(self._title_lbl)
        details_lay.addWidget(self._author_lbl)
        details_lay.addWidget(self._genre_lbl)
        details_lay.addStretch()
        preview_lay.addLayout(details_lay, stretch=1)

        root.addWidget(self._preview_card)

        # ── Form ────────────────────────────────────────────────────────────
        self._preview_title = QLabel()  # kept for compat, hidden
        self._preview_title.setVisible(False)

        self._form_widget = QWidget()
        self._form_widget.setVisible(False)
        form_lay = QVBoxLayout(self._form_widget)
        form_lay.setContentsMargins(0, SP_4, 0, 0)
        form_lay.setSpacing(SP_5)

        self._title_edit = LabeledField.edit("Book title")
        self._author_edit = LabeledField.edit("Author name")
        self._price_edit = LabeledField.edit("Price (Rs.)")
        self._qty_spin = LabeledField.spin(0, 9999)
        self._qty_spin.setValue(1)
        self._disc_spin = LabeledField.spin(0, 100)
        self._disc_spin.setValue(0)
        
        self._genre_combo = LabeledField.combo()
        self._supplier_combo = LabeledField.combo()
        
        self._genres = db.get_genres()
        self._suppliers = db.get_suppliers()
        
        self._genre_combo.addItem("— Select Genre —", None)
        for g in self._genres:
            self._genre_combo.addItem(g["name"], g["id"])
            
        self._supplier_combo.addItem("— Select Supplier —", None)
        for s in self._suppliers:
            self._supplier_combo.addItem(s["name"], s["id"])

        form_lay.addWidget(LabeledField("TITLE *", self._title_edit))
        form_lay.addWidget(LabeledField("AUTHOR *", self._author_edit))

        row = QHBoxLayout()
        row.setSpacing(SP_4)
        row.addWidget(LabeledField("PRICE (Rs.) *", self._price_edit))
        row.addWidget(LabeledField("QUANTITY", self._qty_spin))
        row.addWidget(LabeledField("DISCOUNT %", self._disc_spin))
        form_lay.addLayout(row)
        
        row2 = QHBoxLayout()
        row2.setSpacing(SP_4)
        row2.addWidget(LabeledField("GENRE", self._genre_combo))
        row2.addWidget(LabeledField("SUPPLIER", self._supplier_combo))
        form_lay.addLayout(row2)

        root.addWidget(self._form_widget)

        # ── Action buttons ──────────────────────────────────────────────────
        self._action_widget = QWidget()
        self._action_widget.setVisible(False)
        action_lay = QHBoxLayout(self._action_widget)
        action_lay.setContentsMargins(0, SP_3, 0, 0)
        action_lay.addStretch()

        cancel_btn = BtnSecondary("Cancel")
        cancel_btn.clicked.connect(self._clear)
        action_lay.addWidget(cancel_btn)

        self._save_btn = BtnPrimary("Add to Catalogue ✓")
        self._save_btn.clicked.connect(self._save)
        action_lay.addWidget(self._save_btn)

        root.addWidget(self._action_widget)
        root.addStretch()

        main_layout.addWidget(scroll)
        
    def _fetch(self):
        """Fetch book by ISBN"""
        isbn = self._isbn_input.text().strip()
        if not isbn:
            self._status.show_msg("Please enter an ISBN.")
            return
        
        self._status.hide()
        
        # Clean ISBN
        isbn = re.sub(r'[- ]', '', isbn)
        
        self._fetch_btn.setEnabled(False)
        self._fetch_btn.setText("Fetching...")
        
        self.worker = FetchWorker(isbn)
        self.worker.finished.connect(self._on_fetched)
        self.worker.start()
        
    def _on_fetched(self, data):
        """Handle fetched data"""
        self._fetch_btn.setEnabled(True)
        self._fetch_btn.setText("🔍 Fetch Details")
        
        if not data or not data.get('title'):
            self._status.show_msg("No book found for this ISBN.", is_error=True)
            return
        
        self.fetched_data = data
        self._show_preview(data)
        self._isbn_input.clear()
        
    def _show_preview(self, data):
        """Show book preview"""
        self._preview_title.setVisible(True)
        self._preview_card.setVisible(True)
        self._form_widget.setVisible(True)
        self._action_widget.setVisible(True)
        
        self._title_lbl.setText(data.get('title', ''))
        self._author_lbl.setText(data.get('author', ''))
        
        # Show genre if detected
        if data.get('genre_name'):
            self._genre_lbl.setText(f"📚 {data['genre_name']}")
        elif data.get('subjects'):
            genre_text = ", ".join(data['subjects'][:2])
            self._genre_lbl.setText(f"📚 {genre_text}")
        else:
            self._genre_lbl.setText("")
        
        if data.get('image_path') and os.path.exists(data['image_path']):
            pix = QPixmap(data['image_path']).scaled(120, 160, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self._cover_lbl.setPixmap(pix)
            self._cover_lbl.setText("")
        
        self._title_edit.setText(data.get('title', ''))
        self._author_edit.setText(data.get('author', ''))
        self._price_edit.setText("")
        self._qty_spin.setValue(1)
        self._disc_spin.setValue(0)
        
        # Auto-select genre if matched
        matched_id = data.get('genre_id')
        if matched_id:
            for i in range(self._genre_combo.count()):
                if self._genre_combo.itemData(i) == matched_id:
                    self._genre_combo.setCurrentIndex(i)
                    break
        else:
            self._genre_combo.setCurrentIndex(0)
        self._supplier_combo.setCurrentIndex(0)
        
    def _clear(self):
        """Clear preview"""
        self._preview_title.setVisible(False)
        self._preview_card.setVisible(False)
        self._form_widget.setVisible(False)
        self._action_widget.setVisible(False)
        self.fetched_data = None
        self._cover_lbl.setPixmap(QPixmap())
        self._cover_lbl.setText("📖")
        
    def _save(self):
        """Save book to database"""
        if not self.fetched_data:
            return
            
        title = self._title_edit.text().strip()
        author = self._author_edit.text().strip()
        
        if not title or not author:
            QMessageBox.warning(self, "Missing", "Title and author are required.")
            return
            
        try:
            price = float(self._price_edit.text().strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Enter a valid price.")
            return
            
        qty = self._qty_spin.value()
        disc = self._disc_spin.value()
        genre_id = self._genre_combo.currentData()
        supplier_id = self._supplier_combo.currentData()
        
        db.add_book(
            title=title,
            author=author,
            price=price,
            quantity=qty,       
            genre_id=genre_id,           
            supplier_id=supplier_id,            
            image_path=self.fetched_data.get('image_path', ''),
            discount_percent=disc
        )
        
        genre_msg = f" ({self.fetched_data.get('genre_name', 'None')})" if genre_id else ""
        self._notify_main_window_toast(f"'{title}' added to catalogue!{genre_msg}")
        self._clear()
        self._notify_main_window_refresh()

    def _notify_main_window_toast(self, msg):
        p = self.parent()
        while p:
            if hasattr(p, 'show_toast'):
                p.show_toast(msg)
                break
            p = p.parent() if hasattr(p, 'parent') else None

    def _notify_main_window_refresh(self):
        """Tell main window to refresh all screens"""
        p = self.parent()
        while p:
            if hasattr(p, '_on_sale_done'):
                # We'll call a version that doesn't show its own toast to avoid double toast
                # Or just let it show the toast since it's a 'sale done' generic refresh.
                # Actually, _on_sale_done now shows "Sale recorded". 
                # Let's call refresh directly on screens or modify _on_sale_done.
                self._trigger_refresh(p)
                break
            p = p.parent() if hasattr(p, 'parent') else None

    def _trigger_refresh(self, main_win):
        # Trigger the refresh logic but without the "Sale recorded" toast
        for s in main_win._screens:
            if hasattr(s, 'refresh'):
                s.refresh()
        if hasattr(main_win, '_update_notifications'):
            main_win._update_notifications()