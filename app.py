import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)

    # Apply a dark theme stylesheet
    app.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: #f0f0f0;
        }
        QMenuBar {
            background-color: #3c3c3c;
            color: #f0f0f0;
        }
        QMenuBar::item:selected {
            background-color: #5c5c5c;
        }
        QMenu {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #5c5c5c;
        }
        QMenu::item:selected {
            background-color: #5c5c5c;
        }
        QPushButton {
            background-color: #5c5c5c;
            color: #f0f0f0;
            border: 1px solid #7c7c7c;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #6c6c6c;
        }
        QPushButton:pressed {
            background-color: #4c4c4c;
        }
        QLineEdit, QTextEdit {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #5c5c5c;
            padding: 2px;
        }
        QTabWidget::pane {
            border: 1px solid #5c5c5c;
        }
        QTabBar::tab {
            background: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #5c5c5c;
            border-bottom-color: #3c3c3c; /* same as pane color */
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 5px;
        }
        QTabBar::tab:selected {
            background: #2b2b2b;
            border-bottom-color: #2b2b2b;
        }
        QTableWidget {
            background-color: #2b2b2b;
            color: #f0f0f0;
            gridline-color: #5c5c5c;
            selection-background-color: #5c5c5c;
            selection-color: #f0f0f0;
        }
        QHeaderView::section {
            background-color: #3c3c3c;
            color: #f0f0f0;
            padding: 4px;
            border: 1px solid #5c5c5c;
        }
        QGroupBox {
            border: 1px solid #5c5c5c;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
            background-color: #2b2b2b;
            color: #f0f0f0;
        }
        QTreeWidget {
            background-color: #2b2b2b;
            color: #f0f0f0;
            border: 1px solid #5c5c5c;
            selection-background-color: #5c5c5c;
            selection-color: #f0f0f0;
        }
        QTreeWidget::item:selected {
            background-color: #5c5c5c;
            color: #f0f0f0;
        }
    """)

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
