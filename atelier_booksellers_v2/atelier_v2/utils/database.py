"""
database.py  ·  Andalus Booksellers — complete SQLite backend
All tables, CRUD, sales processing, analytics queries.
"""

import sqlite3
import os
from datetime import datetime, date
from assets.theme import STOCK_THRESHOLD

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "atelier.db")


# ── CONNECTION ────────────────────────────────────────────────────────────────

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    return c


# ── INIT ──────────────────────────────────────────────────────────────────────

def initialize():
    db = _conn()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS genres (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL,
            contact TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            author      TEXT NOT NULL,
            price       REAL NOT NULL CHECK(price > 0),
            quantity    INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            discount_percent REAL DEFAULT 0,
            genre_id    INTEGER REFERENCES genres(id) ON DELETE SET NULL,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            image_path  TEXT DEFAULT '',
            added_on    TEXT DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS sales (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id    INTEGER REFERENCES books(id) ON DELETE SET NULL,
            qty_sold   INTEGER NOT NULL,
            unit_price REAL NOT NULL CHECK(unit_price > 0),
            sale_date  TEXT NOT NULL DEFAULT (date('now')),
            sale_time  TEXT NOT NULL DEFAULT (strftime('%H:%M:%S','now'))
        );
        CREATE TABLE IF NOT EXISTS employees (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Curator'
        );
        CREATE TABLE IF NOT EXISTS discounts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            code       TEXT NOT NULL UNIQUE,
            percent    REAL NOT NULL CHECK(percent > 0 AND percent <= 100),
            max_uses   INTEGER DEFAULT 0,
            used_count INTEGER DEFAULT 0,
            active     INTEGER DEFAULT 1,
            created_on TEXT DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS discount_usage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            discount_id INTEGER REFERENCES discounts(id),
            sale_date   TEXT DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS customer_requests (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            book_title       TEXT NOT NULL,
            author           TEXT NOT NULL,
            customer_name    TEXT NOT NULL,
            customer_contact TEXT DEFAULT '',
            request_date     TEXT DEFAULT (date('now')),
            expected_date    TEXT,
            status          TEXT DEFAULT 'Pending'
        );
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_books_genre    ON books(genre_id);
        CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales(sale_date);
        CREATE INDEX IF NOT EXISTS idx_sales_book     ON sales(book_id);
    """)
    db.commit()

    if db.execute("SELECT COUNT(*) FROM genres").fetchone()[0] == 0:
        _seed(db)
        db.commit()
    db.close()


def _seed(db):
    genres = [
        "Literary Fiction", "Mystery", "Poetry", "Philosophy",
        "Biography", "History", "Science Fiction", "Romance", "Self-Help"
    ]
    for g in genres:
        db.execute("INSERT OR IGNORE INTO genres(name) VALUES(?)", (g,))

    suppliers = [
        ("Oxford University Press", "+92-51-111-693-693"),
        ("Penguin Random House",    "+92-21-111-736-486"),
        ("HarperCollins",           "+92-42-111-472-737"),
    ]
    for s in suppliers:
        db.execute("INSERT INTO suppliers(name,contact) VALUES(?,?)", s)

    gmap = {r[0]: r[1] for r in db.execute("SELECT name,id FROM genres")}
    smap = {r[0]: r[1] for r in db.execute("SELECT name,id FROM suppliers")}

    books = [
        # Literary Fiction
        ("The Garden of Forking Paths",       "Jorge Luis Borges",         1450, 12, "Literary Fiction", "Oxford University Press"),
        ("One Hundred Years of Solitude",     "Gabriel García Márquez",    1680, 8,  "Literary Fiction", "Penguin Random House"),
        ("The Remains of the Day",            "Kazuo Ishiguro",            1240, 15, "Literary Fiction", "HarperCollins"),
        ("Beloved",                           "Toni Morrison",             1120, 10, "Literary Fiction", "Oxford University Press"),
        ("Never Let Me Go",                   "Kazuo Ishiguro",            1300, 9,  "Literary Fiction", "Penguin Random House"),
        # Mystery
        ("The Silent Inquiry",                "Helena Marsh",              1620, 9,  "Mystery",          "HarperCollins"),
        ("And Then There Were None",          "Agatha Christie",           920,  20, "Mystery",          "Oxford University Press"),
        ("The Name of the Rose",             "Umberto Eco",               1850, 6,  "Mystery",          "Penguin Random House"),
        ("Big Little Lies",                  "Liane Moriarty",            1120, 11, "Mystery",          "HarperCollins"),
        # Poetry
        ("Letters to a Young Poet",          "Rainer Maria Rilke",        980,  3,  "Poetry",           "Oxford University Press"),
        ("Leaves of Grass",                  "Walt Whitman",              860,  14, "Poetry",           "Penguin Random House"),
        ("Milk and Honey",                   "Rupi Kaur",                 760,  18, "Poetry",           "HarperCollins"),
        # Philosophy
        ("Meditations",                      "Marcus Aurelius",           950,  20, "Philosophy",       "Oxford University Press"),
        ("Sophie's World",                   "Jostein Gaarder",           1120, 7,  "Philosophy",       "Penguin Random House"),
        ("The Republic",                     "Plato",                     1060, 12, "Philosophy",       "HarperCollins"),
        ("On the Examined Life",             "T. Aurelius",               1280, 4,  "Philosophy",       "Oxford University Press"),
        # Biography
        ("The Diary of a Young Girl",        "Anne Frank",                810,  22, "Biography",        "Penguin Random House"),
        ("Long Walk to Freedom",             "Nelson Mandela",            1520, 9,  "Biography",        "HarperCollins"),
        ("Steve Jobs",                       "Walter Isaacson",           1940, 5,  "Biography",        "Oxford University Press"),
        ("Quiet Cities, Loud Minds",         "Ivan Solberg",              1740, 2,  "Biography",        "Penguin Random House"),
        # History
        ("Sapiens",                          "Yuval Noah Harari",         1680, 16, "History",          "HarperCollins"),
        ("The Silk Roads",                   "Peter Frankopan",           1720, 8,  "History",          "Oxford University Press"),
        ("Guns, Germs and Steel",            "Jared Diamond",             1520, 10, "History",          "Penguin Random House"),
        # Science Fiction
        ("Dune",                             "Frank Herbert",             1840, 14, "Science Fiction",  "HarperCollins"),
        ("1984",                             "George Orwell",             920,  25, "Science Fiction",  "Oxford University Press"),
        ("Brave New World",                  "Aldous Huxley",             860,  18, "Science Fiction",  "Penguin Random House"),
        ("After the Tide",                   "Mira Aldwin",               1200, 9,  "Science Fiction",  "HarperCollins"),
        # Romance
        ("Pride and Prejudice",              "Jane Austen",               820,  30, "Romance",          "Oxford University Press"),
        # Self-Help
        ("Atomic Habits",                    "James Clear",               1440, 20, "Self-Help",        "HarperCollins"),
        ("The Subtle Art of Not Giving a F*","Mark Manson",               1240, 15, "Self-Help",        "Penguin Random House"),
    ]

    for title, author, price, qty, genre, supplier in books:
        db.execute(
            "INSERT INTO books(title,author,price,quantity,genre_id,supplier_id) VALUES(?,?,?,?,?,?)",
            (title, author, price, qty, gmap.get(genre), smap.get(supplier))
        )

    from datetime import timedelta
    today = date.today()
    seed_sales = [
        (1,3,1450,0),(2,2,1680,0),(3,1,1240,0),(5,4,1300,0),
        (6,2,1620,1),(7,5,920,1),(10,1,980,2),(24,3,1840,2),
        (25,6,920,2),(29,4,1440,3),(28,2,820,3),(1,2,1450,4),
        (13,3,950,4),(21,2,1680,5),(8,1,1850,5),(12,4,760,6),
        (30,2,1240,6),(2,1,1680,0),(24,2,1840,1),
    ]
    for book_id, qty_sold, unit_price, days_ago in seed_sales:
        d = (today - timedelta(days=days_ago)).isoformat()
        db.execute(
            "INSERT INTO sales(book_id,qty_sold,unit_price,sale_date) VALUES(?,?,?,?)",
            (book_id, qty_sold, unit_price, d)
        )

    db.execute("INSERT INTO employees(name,role) VALUES(?,?)", ("Hanfa Azad", "Manager"))


# ── BOOKS ─────────────────────────────────────────────────────────────────────

def get_books(genre_id=None, search=None):
    db = _conn()
    q = """
        SELECT b.id, b.title, b.author, b.price, b.quantity,
               b.discount_percent,
               g.name AS genre, g.id AS genre_id,
               s.name AS supplier, s.id AS supplier_id,
               b.image_path, b.added_on
        FROM books b
        LEFT JOIN genres   g ON b.genre_id    = g.id
        LEFT JOIN suppliers s ON b.supplier_id = s.id
        WHERE 1=1
    """
    params = []
    if genre_id:
        q += " AND b.genre_id = ?"; params.append(genre_id)
    if search:
        q += " AND (b.title LIKE ? OR b.author LIKE ?)"; params += [f"%{search}%"]*2
    q += " ORDER BY b.title COLLATE NOCASE"
    rows = db.execute(q, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_book(book_id):
    db = _conn()
    r = db.execute("""
        SELECT b.*, g.name AS genre, s.name AS supplier
        FROM books b
        LEFT JOIN genres   g ON b.genre_id    = g.id
        LEFT JOIN suppliers s ON b.supplier_id = s.id
        WHERE b.id = ?
    """, (book_id,)).fetchone()
    db.close()
    return dict(r) if r else None


def add_book(title, author, price, quantity, genre_id, supplier_id, image_path="", discount_percent=0):
    db = _conn()
    cur = db.execute(
        "INSERT INTO books(title,author,price,quantity,genre_id,supplier_id,image_path,discount_percent) VALUES(?,?,?,?,?,?,?,?)",
        (title, author, price, quantity, genre_id, supplier_id, image_path, discount_percent)
    )
    db.commit(); db.close()
    return cur.lastrowid


def update_book(book_id, title, author, price, quantity, genre_id, supplier_id, image_path="", discount_percent=0):
    db = _conn()
    db.execute(
        "UPDATE books SET title=?,author=?,price=?,quantity=?,genre_id=?,supplier_id=?,image_path=?,discount_percent=? WHERE id=?",
        (title, author, price, quantity, genre_id, supplier_id, image_path, discount_percent, book_id)
    )
    db.commit(); db.close()


def delete_book(book_id):
    db = _conn()
    sales_count = db.execute("SELECT COUNT(*) FROM sales WHERE book_id=?", (book_id,)).fetchone()[0]
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit(); db.close()
    return f"Note: {sales_count} historical sale(s) for this book will be unlinked." if sales_count else None


def set_book_image(book_id, path):
    db = _conn()
    db.execute("UPDATE books SET image_path=? WHERE id=?", (path, book_id))
    db.commit(); db.close()


def restock(book_id, add_qty):
    db = _conn()
    db.execute("UPDATE books SET quantity = quantity + ? WHERE id=?", (add_qty, book_id))
    db.commit(); db.close()


# ── GENRES ────────────────────────────────────────────────────────────────────

def get_genres():
    db = _conn()
    rows = db.execute("SELECT id, name FROM genres ORDER BY name COLLATE NOCASE").fetchall()
    db.close()
    return [dict(r) for r in rows]


def add_genre(name):
    db = _conn()
    try:
        db.execute("INSERT INTO genres(name) VALUES(?)", (name,))
        db.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Genre '{name}' already exists.")
    finally:
        db.close()


def delete_genre(genre_id):
    db = _conn()
    db.execute("UPDATE books SET genre_id=NULL WHERE genre_id=?", (genre_id,))
    db.execute("DELETE FROM genres WHERE id=?", (genre_id,))
    db.commit(); db.close()


# ── SUPPLIERS ─────────────────────────────────────────────────────────────────

def get_suppliers():
    db = _conn()
    rows = db.execute("SELECT id, name, contact FROM suppliers ORDER BY name COLLATE NOCASE").fetchall()
    db.close()
    return [dict(r) for r in rows]


def add_supplier(name, contact=""):
    db = _conn()
    cur = db.execute("INSERT INTO suppliers(name,contact) VALUES(?,?)", (name, contact))
    db.commit(); db.close()
    return cur.lastrowid


def delete_supplier(supplier_id):
    db = _conn()
    db.execute("UPDATE books SET supplier_id=NULL WHERE supplier_id=?", (supplier_id,))
    db.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
    db.commit(); db.close()


# ── SALES ─────────────────────────────────────────────────────────────────────

def process_sale(cart):
    db = _conn()
    try:
        alerts = []
        for item in cart:
            row = db.execute("SELECT quantity, title FROM books WHERE id=?", (item["book_id"],)).fetchone()
            if not row:
                raise ValueError(f"Book ID {item['book_id']} not found.")
            if row["quantity"] < item["qty"]:
                raise ValueError(
                    f"Insufficient stock for \"{row['title']}\".\n"
                    f"Available: {row['quantity']}  ·  Requested: {item['qty']}"
                )
            
            # Track if stock drops to or below threshold
            old_qty = row["quantity"]
            new_qty = old_qty - item["qty"]
            if old_qty > STOCK_THRESHOLD and new_qty <= STOCK_THRESHOLD:
                alerts.append({"title": row["title"], "quantity": new_qty})

        ids = []
        today = date.today().isoformat()
        now   = datetime.now().strftime("%H:%M:%S")
        for item in cart:
            cur = db.execute(
                "INSERT INTO sales(book_id,qty_sold,unit_price,sale_date,sale_time) VALUES(?,?,?,?,?)",
                (item["book_id"], item["qty"], item["unit_price"], today, now)
            )
            db.execute("UPDATE books SET quantity=quantity-? WHERE id=?", (item["qty"], item["book_id"]))
            ids.append(cur.lastrowid)
        db.commit()
        return {"ids": ids, "alerts": alerts}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_sales(limit=500, search=None):
    db = _conn()
    q = """
        SELECT s.id, COALESCE(b.title,'[deleted]') AS title,
               COALESCE(b.author,'—') AS author,
               s.qty_sold, s.unit_price,
               (s.qty_sold * s.unit_price) AS total,
               s.sale_date, s.sale_time
        FROM sales s
        LEFT JOIN books b ON s.book_id = b.id
        WHERE 1=1
    """
    params = []
    if search:
        q += " AND b.title LIKE ?"; params.append(f"%{search}%")
    q += " ORDER BY s.id DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(q, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_sale_by_id(sale_id):
    db = _conn()
    r = db.execute("""
        SELECT s.*, COALESCE(b.title,'[deleted]') AS title,
               COALESCE(b.author,'—') AS author
        FROM sales s LEFT JOIN books b ON s.book_id = b.id
        WHERE s.id = ?
    """, (sale_id,)).fetchone()
    db.close()
    return dict(r) if r else None


# ── RETURNS ───────────────────────────────────────────────────────────────────

def process_return(sale_id, qty_to_return, reason="Customer return"):
    db = _conn()
    try:
        sale = db.execute("""
            SELECT s.id, s.book_id, s.qty_sold, s.unit_price,
                   COALESCE(b.title,'[deleted]') AS title,
                   COALESCE(b.author,'—') AS author
            FROM sales s LEFT JOIN books b ON s.book_id = b.id
            WHERE s.id = ?
        """, (sale_id,)).fetchone()
        
        if not sale:
            raise ValueError(f"Sale #{sale_id} not found")
        if sale["qty_sold"] <= 0:
            raise ValueError("This is already a return record")
        
        already = db.execute("""
            SELECT COALESCE(SUM(ABS(qty_sold)), 0)
            FROM sales WHERE book_id = ? AND qty_sold < 0
        """, (sale["book_id"],)).fetchone()[0]
        
        max_return = sale["qty_sold"] - already
        if max_return <= 0:
            raise ValueError("All copies already returned")
        if qty_to_return > max_return:
            raise ValueError(f"Can only return {max_return} more cop{'y' if max_return==1 else 'ies'}")
        
        refund = qty_to_return * sale["unit_price"]
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")
        
        db.execute("""
            INSERT INTO sales(book_id, qty_sold, unit_price, sale_date, sale_time)
            VALUES (?, ?, ?, ?, ?)
        """, (sale["book_id"], -qty_to_return, sale["unit_price"], today, now))
        
        if sale["book_id"]:
            db.execute("UPDATE books SET quantity = quantity + ? WHERE id = ?",
                      (qty_to_return, sale["book_id"]))
        
        db.commit()
        
        return {
            "sale_id": sale_id,
            "title": sale["title"],
            "author": sale["author"],
            "qty": qty_to_return,
            "unit_price": sale["unit_price"],
            "refund": refund,
            "date": today,
            "reason": reason
        }
    except Exception as e:
        db.rollback()
        raise ValueError(str(e))
    finally:
        db.close()


# ── ANALYTICS ─────────────────────────────────────────────────────────────────

def dashboard_stats():
    db = _conn()
    today = date.today().isoformat()

    today_rev = db.execute(
        "SELECT COALESCE(SUM(qty_sold*unit_price),0) FROM sales WHERE sale_date=?", (today,)
    ).fetchone()[0]
    
    today_tax = today_rev * 0.05

    total_books   = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    low_stock_cnt = db.execute("SELECT COUNT(*) FROM books WHERE quantity>0 AND quantity<=?", (STOCK_THRESHOLD,)).fetchone()[0]
    out_of_stock  = db.execute("SELECT COUNT(*) FROM books WHERE quantity=0").fetchone()[0]

    best = db.execute("""
        SELECT b.title, SUM(s.qty_sold) AS sold
        FROM sales s JOIN books b ON s.book_id=b.id
        WHERE s.qty_sold > 0
        GROUP BY s.book_id ORDER BY sold DESC LIMIT 1
    """).fetchone()

    yesterday = db.execute(
        "SELECT COALESCE(SUM(qty_sold*unit_price),0) FROM sales WHERE sale_date=date('now','-1 day')"
    ).fetchone()[0]

    db.close()
    return {
        "today_rev":     today_rev,
        "today_tax":     today_tax,
        "yesterday_rev": yesterday,
        "total_books":   total_books,
        "low_stock":     low_stock_cnt,
        "out_of_stock":  out_of_stock,
        "bestseller":    best["title"] if best else "—",
        "bestseller_sold": best["sold"] if best else 0,
    }


def top_books(n=5):
    db = _conn()
    rows = db.execute("""
        SELECT b.title, b.author,
               SUM(s.qty_sold) AS total_sold,
               SUM(s.qty_sold*s.unit_price) AS revenue
        FROM sales s JOIN books b ON s.book_id=b.id
        WHERE s.qty_sold > 0
        GROUP BY s.book_id ORDER BY total_sold DESC LIMIT ?
    """, (n,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def sales_by_genre():
    db = _conn()
    rows = db.execute("""
        SELECT g.name, SUM(s.qty_sold) AS total_sold,
               SUM(s.qty_sold*s.unit_price) AS revenue
        FROM sales s
        JOIN books  b ON s.book_id  = b.id
        JOIN genres g ON b.genre_id = g.id
        WHERE s.qty_sold > 0
        GROUP BY g.id ORDER BY revenue DESC
    """).fetchall()
    db.close()
    return [dict(r) for r in rows]


def daily_revenue(days=7):
    db = _conn()
    rows = db.execute("""
        SELECT sale_date, SUM(qty_sold*unit_price) AS revenue
        FROM sales
        WHERE sale_date >= date('now', ?)
        GROUP BY sale_date ORDER BY sale_date ASC
    """, (f"-{days-1} days",)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def low_stock_books(threshold=STOCK_THRESHOLD):
    db = _conn()
    rows = db.execute("""
        SELECT b.id, b.title, b.author, b.quantity,
               COALESCE(g.name,'—') AS genre
        FROM books b LEFT JOIN genres g ON b.genre_id=g.id
        WHERE b.quantity < ?
        ORDER BY b.quantity ASC, b.title
    """, (threshold,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def alltime_revenue():
    db = _conn()
    v = db.execute("SELECT COALESCE(SUM(qty_sold*unit_price),0) FROM sales").fetchone()[0]
    db.close()
    return v


def total_books_sold():
    db = _conn()
    v = db.execute("SELECT COALESCE(SUM(qty_sold),0) FROM sales WHERE qty_sold > 0").fetchone()[0]
    db.close()
    return v


# ── EMPLOYEE ──────────────────────────────────────────────────────────────────

def get_employee():
    db = _conn()
    r = db.execute("SELECT * FROM employees LIMIT 1").fetchone()
    db.close()
    return dict(r) if r else {"name": "Curator", "role": "Curator"}


# ── DISCOUNTS & COUPONS ────────────────────────────────────────────────────────

def create_discount_code(code, percent, max_uses=0):
    db = _conn()
    try:
        db.execute(
            "INSERT INTO discounts(code, percent, max_uses) VALUES(?,?,?)",
            (code.strip().upper(), percent, max_uses)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        raise ValueError(f"Code '{code}' already exists.")
    finally:
        db.close()


def get_all_discounts():
    db = _conn()
    rows = db.execute("SELECT * FROM discounts ORDER BY created_on DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]


def validate_coupon(code):
    db = _conn()
    row = db.execute(
        "SELECT * FROM discounts WHERE code=? AND active=1", (code.strip().upper(),)
    ).fetchone()
    db.close()
    if not row:
        return None
    if row["max_uses"] > 0 and row["used_count"] >= row["max_uses"]:
        return None
    return {"id": row["id"], "code": row["code"], "percent": row["percent"]}


def apply_coupon(discount_id):
    db = _conn()
    db.execute("UPDATE discounts SET used_count = used_count + 1 WHERE id=?", (discount_id,))
    db.execute("INSERT INTO discount_usage(discount_id) VALUES(?)", (discount_id,))
    db.commit()
    db.close()


def toggle_discount_status(discount_id, active):
    db = _conn()
    db.execute("UPDATE discounts SET active=? WHERE id=?", (int(active), discount_id))
    db.commit()
    db.close()


def delete_discount(discount_id):
    db = _conn()
    db.execute("DELETE FROM discounts WHERE id=?", (discount_id,))
    db.commit()
    db.close()


def set_book_discount(book_id, percent):
    db = _conn()
    db.execute("UPDATE books SET discount_percent=? WHERE id=?", (percent, book_id))
    db.commit()
    db.close()


def get_book_discount(book_id):
    db = _conn()
    r = db.execute("SELECT discount_percent FROM books WHERE id=?", (book_id,)).fetchone()
    db.close()
    return r["discount_percent"] if r else 0


# ── CUSTOMER REQUESTS (Wishlist) ──────────────────────────────────────────────

def get_customer_requests():
    db = _conn()
    rows = db.execute("SELECT * FROM customer_requests ORDER BY request_date DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]


def add_customer_request(title, author, customer, contact, expected_date):
    db = _conn()
    db.execute(
        "INSERT INTO customer_requests(book_title, author, customer_name, customer_contact, expected_date) VALUES(?,?,?,?,?)",
        (title, author, customer, contact, expected_date)
    )
    db.commit()
    db.close()


def delete_customer_request(request_id):
    db = _conn()
    db.execute("DELETE FROM customer_requests WHERE id=?", (request_id,))
    db.commit()
    db.close()


def update_request_status(request_id, status):
    db = _conn()
    db.execute("UPDATE customer_requests SET status=? WHERE id=?", (status, request_id))
    db.commit()
    db.close()


# ── SETTINGS ──────────────────────────────────────────────────────────────────

def get_setting(key, default=None):
    db = _conn()
    r = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    db.close()
    return r["value"] if r else default

def set_setting(key, value):
    db = _conn()
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, value))
    db.commit()
    db.close()

