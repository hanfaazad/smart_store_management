# 📖 Atelier Booksellers — Smart Bookstore Management System

A premium desktop bookstore management application.
**Python · PyQt5 · SQLite · Matplotlib**

---

## Quick Start

```bash
pip install PyQt5 matplotlib
python main.py
```

The database is created automatically on first run with **30 books** pre-seeded.

---

## Optional: Premium Typography

Download these font files and place them in the `./fonts/` folder before running.
The app will auto-detect and use them — no config needed.

| Font              | URL                                          |
|-------------------|----------------------------------------------|
| Playfair Display  | fonts.google.com/specimen/Playfair+Display   |
| Inter             | fonts.inter.ui                               |

Without them the app falls back to the best available system font (Georgia / Segoe UI).

---

## Project Structure

```
atelier_v2/
├── main.py                 ← Entry point. Splash, DB init, launch.
├── requirements.txt
├── atelier.db              ← SQLite database (auto-created)
│
├── assets/
│   └── theme.py            ← All design tokens: colours, fonts, spacing, shadows
│
├── utils/
│   └── database.py         ← Complete backend: all SQL, CRUD, analytics
│
├── ui/
│   ├── widgets.py          ← Every reusable component
│   ├── main_window.py      ← App shell: sidebar, header, page stack, navigation
│   ├── dashboard.py        ← KPI cards + genre filter + responsive book grid
│   ├── catalogue.py        ← Book table, Add/Edit/Delete, image upload
│   ├── sales.py            ← POS: book selector, live cart, tax, confirm sale
│   ├── inventory.py        ← Stock overview, mini cards, restock dialog
│   ├── insights.py         ← Analytics charts (pie, bar, line, top-3 list)
│   └── management.py       ← Genres, Suppliers, Sales History screens
│
├── fonts/                  ← Drop .ttf files here for premium typography
└── images/
    └── books/              ← Book cover images stored here after upload
```

---

## Features

| Screen          | Capability                                                        |
|-----------------|-------------------------------------------------------------------|
| Dashboard       | Live KPIs, % vs yesterday, genre chips, responsive book grid      |
| Catalogue       | Full CRUD table, cover image upload, search                       |
| Genres          | Add / delete genres (safe cascade)                                |
| Suppliers       | Add / delete suppliers with contact                               |
| New Sale        | Book selector, detail card, live cart, 5% tax, confirm            |
| Sales History   | Full transaction log, search by title                             |
| Inventory       | 4 stock mini-cards, low-stock filter, per-book restock            |
| Insights        | Genre pie, top-5 bar, 7-day revenue trend, top-3 favourites       |

---

## Adding Cover Images

1. Go to **Catalogue**
2. Click **📷 Image** on any row
3. Pick a `.jpg`, `.png`, or `.webp` file
4. Image is saved to `images/books/` and displayed everywhere

---

## Design System

| Token         | Value     | Usage                          |
|---------------|-----------|--------------------------------|
| Background    | `#F7F4ED` | Ivory canvas                   |
| Foreground    | `#19241F` | Forest ink body text           |
| Card          | `#FBF8F1` | Card surfaces                  |
| Primary       | `#1E3D2F` | Buttons, headings, sidebar row |
| Accent        | `#C99A3D` | Gold — badges, genre labels    |
| Destructive   | `#B83D2E` | Burgundy — low stock, delete   |
| Sidebar       | `#172F24` | Left nav background            |
