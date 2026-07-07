# 📖 Andalus Booksellers

Andalus Booksellers is a desktop bookstore management application built with Python and PyQt5. It helps a small bookstore manage inventory, process sales, review analytics, and track customer requests from a single polished interface.

**Tech stack:** Python · PyQt5 · SQLite · Matplotlib · ReportLab

---

## Quick start

From the project folder, install the requirements and launch the app:

```bash
pip install -r requirements.txt
python main.py
```

On first run, the app creates the SQLite database automatically and seeds it with sample genres, suppliers, books, and sales data.

---

## What the app includes

- Dashboard with quick KPIs and a searchable book grid
- Catalogue management for books, prices, stock levels, discounts, and cover images
- Sales screen for fast checkout and cart-based transactions
- Sales history with export support and return processing
- Inventory overview with low-stock visibility
- Insights and charts for revenue and book performance
- Genres, suppliers, coupons, and customer request management
- ISBN lookup screen for book lookups

---

## Project structure

```text
atelier_v2/
├── main.py
├── requirements.txt
├── atelier.db                # SQLite database (created automatically)
├── assets/
│   └── theme.py              # App styling and design tokens
├── ui/
│   ├── dashboard.py          # Dashboard screen
│   ├── catalogue.py          # Book catalogue and CRUD tools
│   ├── sales.py              # Point-of-sale flow
│   ├── inventory.py          # Inventory and restocking
│   ├── insights.py           # Analytics charts
│   ├── management.py         # Genres, suppliers, coupons, sales history
│   ├── requests.py           # Customer requests / wishlist flow
│   ├── isbn_lookup.py        # ISBN lookup screen
│   ├── main_window.py        # Main app shell and navigation
│   └── widgets.py            # Reusable UI components
└── utils/
    └── database.py           # Database schema, CRUD logic, and seed data
```

---

## Optional typography

The app can use custom fonts if you place TrueType font files in a local fonts folder. If they are not present, it will fall back to the best available system font automatically.

---

## Notes

- Cover images can be added from the Catalogue screen and stored under the app's image folder.
- The interface is designed for a desktop workflow and is best used in a normal desktop environment.
