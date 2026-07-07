"""
main.py  ·  Andalus Booksellers
Entry point — run:  python main.py

Setup:
    pip install PyQt5 matplotlib

Optional (for best typography):
    Download and place in ./fonts/:
    - PlayfairDisplay-Regular.ttf  (fonts.google.com/specimen/Playfair+Display)
    - Inter-Regular.ttf            (fonts.inter.ui)
    The app will use the best available font automatically.
"""

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main():
    from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient
    import os, tempfile

    # ── Single Instance Check ─────────────────────────────────────────────
    # Use a lock file in the temp directory to prevent multiple instances
    lock_path = os.path.join(tempfile.gettempdir(), "andalus_booksellers.lock")
    try:
        if os.path.exists(lock_path):
            # Try to remove it. If it's locked by another process, this fails.
            os.remove(lock_path)
        
        lock_file = open(lock_path, 'w')
        lock_file.write(str(os.getpid()))
        # We keep lock_file open until the app exits
    except (OSError, IOError):
        # Could not remove or write means another instance is likely running
        # We'll just exit quietly or with a small message if we had an app
        print("Application is already running.")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("Andalus Booksellers")
    app.setOrganizationName("Andalus")

    # ── Apply global stylesheet ──────────────────────────────────────────
    from assets.theme import get_global_stylesheet
    app.setStyleSheet(get_global_stylesheet())

    # ── Splash screen ────────────────────────────────────────────────────
    from assets.theme import SIDEBAR, ACCENT, SIDEBAR_FG, SIDEBAR_SUB, FONT_SERIF, FONT_SANS

    W, H = 520, 300
    pix = QPixmap(W, H)
    pix.fill(QColor(SIDEBAR))

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Subtle gradient overlay
    from PyQt5.QtGui import QLinearGradient
    grad = QLinearGradient(0, 0, W, H)
    grad.setColorAt(0.0, QColor(255,255,255,6))
    grad.setColorAt(1.0, QColor(0,0,0,20))
    p.fillRect(0, 0, W, H, grad)

    # Decorative line pattern
    p.setPen(QColor(ACCENT+"18"))
    for i in range(0, W+H, 30):
        p.drawLine(i, 0, 0, i)

    # Icon
    p.setFont(QFont(FONT_SERIF, 52))
    p.setPen(QColor(ACCENT))
    p.drawText(0, 30, W, 100, Qt.AlignCenter, "📖")

    # Name
    f = QFont(FONT_SERIF, 26); f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(SIDEBAR_FG))
    p.drawText(0, 140, W, 50, Qt.AlignCenter, "Andalus Booksellers")

    # Tagline
    p.setFont(QFont(FONT_SANS, 10))
    p.setPen(QColor(SIDEBAR_SUB))
    p.drawText(0, 192, W, 28, Qt.AlignCenter, "Initialising your store…")

    # Gold rule
    p.setPen(QColor(ACCENT+"80"))
    p.drawLine(W//2 - 60, 238, W//2 + 60, 238)

    p.end()

    splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.FramelessWindowHint)
    splash.show()
    app.processEvents()

    # ── Initialise database ──────────────────────────────────────────────
    import utils.database as db
    db.initialize()

    # ── Build and show main window ───────────────────────────────────────
    from ui.main_window import MainWindow
    window = MainWindow()

    def _launch():
        splash.finish(window)
        window.show()
        window.raise_()
        window.activateWindow()

    QTimer.singleShot(1400, _launch)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
