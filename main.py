import os
import sys
from PyQt5.QtWidgets import QApplication, QStyleFactory

from main_window import MainWindow
from styles import APP_STYLE


def main():
    os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("windowsvista"))
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
