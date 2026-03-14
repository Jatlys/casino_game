import sys

from PyQt6.QtWidgets import QApplication

from view.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)    # Initialise the Qt application
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
