APP_STYLE = """
/* ------------------------------ Hauptfenster ------------------------------ */
QMainWindow {
  background: #F3F3F3;
}

/* -------------------------------- Toolbar -------------------------------- */
QToolBar {
  background: #F3F3F3;
  border: none;
  spacing: 4px;
  padding: 2px;
}
QToolButton {
  background: transparent;
  border: none;
  color: #000000;
  padding: 4px;
  border-radius: 4px;
}
QToolButton:hover {
  background: #E1E1E1;
}

/* ------------------------------- Dockwidgets ------------------------------ */
QDockWidget {
  background: #FFFFFF;
  border: 1px solid #C0C0C0;
}
QDockWidget::title {
  background: #FFFFFF;
  color: #000000;
  padding: 4px;
  border-bottom: 1px solid #C0C0C0;
}

/* ------------------------------ Tabellenview ----------------------------- */
QTableWidget {
  background: #FFFFFF;
  alternate-background-color: #F9F9F9;
  gridline-color: #E1E1E1;
}
QHeaderView::section {
  background: #F3F3F3;
  color: #000000;
  padding: 4px;
  border: none;
}
QTableWidget::item:selected {
  background: #0078D4;
  color: #FFFFFF;
}

/* ------------------------------ Buttons --------------------------------- */
QPushButton {
  background: #FFFFFF;
  border: 1px solid #C0C0C0;
  border-radius: 4px;
  padding: 4px 12px;
  color: #000000;
}
QPushButton:hover {
  background: #E1E1E1;
}
QPushButton:pressed {
  background: #D1D1D1;
}

/* ---------------------------- Eingabefelder ------------------------------ */
QLineEdit, QTextEdit, QComboBox {
  background: #FFFFFF;
  border: 1px solid #C0C0C0;
  border-radius: 4px;
  padding: 4px;
  color: #000000;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
  border: 1px solid #0078D4;
}

/* ---------------------------- GraphicsView ------------------------------- */
QGraphicsView {
  background: #F3F3F3;
  border: none;
}
"""
