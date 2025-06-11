import sys
import os
import json
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
    QFileDialog, QToolBar, QAction, QColorDialog, QInputDialog,
    QListWidget, QListWidgetItem, QDockWidget, QMessageBox, QMenu,
    QTableWidget, QTableWidgetItem, QShortcut, QLabel, QComboBox, 
    QLineEdit, QFormLayout, QWidget, QStyleFactory
)
os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
from qfluentwidgets.window.fluent_window import ( FluentWindow )
from qfluentwidgets import ( Theme )
from PyQt5.QtGui import (
    QBrush, QColor, QPen, QFont, QPainter, QImage, QTransform,
    QPolygonF, QPixmap, QIcon, QPainterPath, QKeySequence, QPalette,
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QRect, QPoint, QLineF, QPointF
def is_color_dark(color: QColor, threshold: float = 128.0) -> bool:
    """Berechnet die Helligkeit und gibt True zurück, wenn sie unter threshold liegt."""
    # Wahrnehmungs-Helligkeit (Luminanz) nach ITU-R BT.601
    r, g, b = color.red(), color.green(), color.blue()
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < threshold

TEMPLATES_FILE = "templates.json"

class NodeItem(QGraphicsRectItem):
    def __init__(self, shape="rect", rect=QRectF(0, 0, 100, 60), text1="Node", text2="", color1=QColor("lightgray"), color2=QColor("white")):
        super().__init__(rect)
        self.min_width = rect.width()
        self.min_height = rect.height()
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.shape = shape
        self.color1 = color1
        self.color2 = color2
        self.pen = QPen(Qt.black)
        self.setPen(self.pen)

        self.text1 = text1
        self.text2 = text2

        self.text_item1 = QGraphicsTextItem(text1, self)
        self.text_item1.setDefaultTextColor(Qt.black)
        font1 = QFont()
        font1.setPointSize(10)
        self.text_item1.setFont(font1)

        self.text_item2 = QGraphicsTextItem(text2, self)
        self.text_item2.setDefaultTextColor(Qt.black)
        font2 = QFont()
        font2.setPointSize(8)
        self.text_item2.setFont(font2)

        self.center_texts()
        self.adjustSize()
        
    def adjustSize(self):
        """Vergrößert das Node-Rechteck, wenn der Text nicht mehr hineinpasst."""
        padding_x = 20
        padding_y = 20
        # Text-Größen ermitteln
        r1 = self.text_item1.boundingRect()
        r2 = self.text_item2.boundingRect()
        # Breite: max aus min_width und Breite der Texte plus Padding
        new_width  = max(self.min_width, r1.width(), r2.width()) + padding_x
        # Höhe: Text-Höhe + Padding, mindestens min_height
        new_height = max(self.min_height, r1.height() + r2.height()) + padding_y
        # Rectangle neu setzen (immer ab (0,0))
        self.setRect(QRectF(0, 0, new_width, new_height))
        # Texte neu zentrieren
        self.center_texts()
        self.update_text_colors()

    def center_texts(self):
        rect = self.rect()
        text1_rect = self.text_item1.boundingRect()
        x1 = rect.x() + (rect.width() - text1_rect.width()) / 2
        y1 = rect.y() + 5
        self.text_item1.setPos(x1, y1)
        text2_rect = self.text_item2.boundingRect()
        x2 = rect.x() + (rect.width() - text2_rect.width()) / 2
        y2 = y1 + text1_rect.height()
        self.text_item2.setPos(x2, y2)

    def paint(self, painter, option, widget):
        self.update_text_colors()
        r = self.rect()
        path = QPainterPath()
        if self.shape == "rect":
            path.addRect(r)
        elif self.shape == "ellipse":
            path.addEllipse(r)
        elif self.shape == "diamond":
            points = [
                QPointF(r.x() + r.width()/2, r.y()),
                QPointF(r.x() + r.width(), r.y() + r.height()/2),
                QPointF(r.x() + r.width()/2, r.y() + r.height()),
                QPointF(r.x(), r.y() + r.height()/2)
            ]
            path.addPolygon(QPolygonF(points))
        elif self.shape == "triangle":
            points = [
                QPointF(r.x() + r.width()/2, r.y()),
                QPointF(r.x() + r.width(), r.y() + r.height()),
                QPointF(r.x(), r.y() + r.height())
            ]
            path.addPolygon(QPolygonF(points))
        elif self.shape == "hexagon":
            w, h = r.width(), r.height()
            x, y = r.x(), r.y()
            points = [
                QPointF(x + w*0.25, y),
                QPointF(x + w*0.75, y),
                QPointF(x + w, y + h/2),
                QPointF(x + w*0.75, y + h),
                QPointF(x + w*0.25, y + h),
                QPointF(x, y + h/2)
            ]
            path.addPolygon(QPolygonF(points))
        # Top half
        painter.save()
        painter.setBrush(QBrush(self.color1))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(r.x(), r.y(), r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        # Bottom half
        painter.save()
        painter.setBrush(QBrush(self.color2))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(r.x(), r.y() + r.height()/2, r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        # Outline
        painter.setPen(self.pen)
        painter.drawPath(path)
        self.center_texts()

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        change_shape = menu.addAction("Form ändern")
        connect_node = menu.addAction("Verbinden")
        edit_text = menu.addAction("Text bearbeiten")
        delete_node = menu.addAction("Löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == change_color and scene:
            col1 = QColorDialog.getColor(self.color1)
            if col1.isValid():
                col2 = QColorDialog.getColor(self.color2)
                if not col2.isValid():
                    col2 = col1
                self.color1, self.color2 = col1, col2
                self.update_text_colors()
                self.update()
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == change_shape and scene:
            shapes = ["Rechteck", "Ellipse", "Raute", "Dreieck", "Hexagon"]
            idx, ok = QInputDialog.getItem(None, "Form wählen", "Form:", shapes, 0, False)
            if ok:
                mapping = {
                    "Rechteck": "rect",
                    "Ellipse": "ellipse",
                    "Raute": "diamond",
                    "Dreieck": "triangle",
                    "Hexagon": "hexagon"
                }
                self.shape = mapping[idx]
                self.update()
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == connect_node and scene:
            scene.connecting = True
            scene.connect_source = self
        elif action == edit_text and scene:
            text1, ok1 = QInputDialog.getText(None, "Protokoll bearbeiten", "Protokoll:", text=self.text1)
            if ok1:
                text2, ok2 = QInputDialog.getText(None, "Adresse bearbeiten", "Adresse", text=self.text2)
                if ok2:
                    self.text1 = text1
                    self.text2 = text2
                    self.text_item1.setPlainText(text1)
                    self.text_item2.setPlainText(text2)
                    self.center_texts()
                    self.adjustSize()
                    if hasattr(scene, 'parent'):
                        scene.parent.update_table()
        elif action == delete_node and scene:
            for edge in list(scene.items()):
                if isinstance(edge, EdgeItem) and (edge.source == self or edge.dest == self):
                    scene.removeItem(edge)
                    if edge in scene.edges:
                        scene.edges.remove(edge)
            scene.removeItem(self)
            if self in scene.nodes:
                scene.nodes.remove(self)
            if hasattr(scene, 'parent'):
                scene.parent.update_table()
        super().contextMenuEvent(event)
        
    def update_text_colors(self):
        # primärer Text über color1 entscheiden
        c1 = self.color1
        self.text_item1.setDefaultTextColor(Qt.white if is_color_dark(c1) else Qt.black)
        # sekundärer Text über color2 entscheiden
        c2 = self.color2
        self.text_item2.setDefaultTextColor(Qt.white if is_color_dark(c2) else Qt.black)

class EdgeItem(QGraphicsLineItem):
    def __init__(self, source, dest,
                 color1=Qt.red, 
                 color2=Qt.green,
                 dash_pattern=(8.0, 4.0),
                 label_text=""):
        super().__init__()
        self.source       = source
        self.dest         = dest
        # Zwei Farben und Muster speichern
        self.color1       = QColor(color1)
        self.color2       = QColor(color2)
        self.dash_pattern = dash_pattern
        self.pen_width    = 2.0

        # Label-TextItem (Zeichnung übernehmen wir selbst)
        self.text_item = QGraphicsTextItem(label_text, self)
        self.text_item.setDefaultTextColor(Qt.black)

        # **Keinen** initialen Pen setzen – wir malen komplett selbst
        self.setPen(QPen(Qt.NoPen))

        # Reihenfolge: Linie immer *unter* den Nodes, Text darüber
        self.setZValue(-1)
        self.text_item.setZValue(1)

    def update_position(self):
        p1 = self.source.sceneBoundingRect().center()
        p2 = self.dest.  sceneBoundingRect().center()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        # Label mittig positionieren
        mid = QLineF(p1, p2).pointAt(0.5)
        rect = self.text_item.boundingRect()
        self.text_item.setPos(mid.x() - rect.width()/2,
                              mid.y() - rect.height()/2)

    def paint(self, painter, option, widget):
        # 1) Geometrie updaten
        self.update_position()
        line   = self.line()
        length = line.length()
        if length <= 0:
            return

        # 2) Dash- und Gap-Längen
        dash, gap = self.dash_pattern

        pos    = 0.0
        toggle = False

        # 3) Segment-Loop: abwechselnd color1/color2 zeichnen
        while pos < length:
            start_pt = line.pointAt(pos/length)
            end_pos  = min(pos + dash, length)
            end_pt   = line.pointAt(end_pos/length)

            pen = QPen(
                self.color1 if not toggle else self.color2,
                self.pen_width
            )
            # Immer einfarbig in jedem Segment
            pen.setStyle(Qt.SolidLine)

            painter.setPen(pen)
            painter.drawLine(QLineF(start_pt, end_pt))

            pos    += dash + gap
            toggle = not toggle

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        edit_label = menu.addAction("Text bearbeiten")
        delete_edge = menu.addAction("Verbindung löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == change_color and scene:
            # Farbdialog öffnen, Startfarbe ist aktuelle Linienfarbe
            col = QColorDialog.getColor(self.pen.color())
            if col.isValid():
                self.pen.setColor(col)
                self.setPen(self.pen)
                # Tabelle updaten, falls vorhanden
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == edit_label and scene:
            text, ok = QInputDialog.getText(None, "Verbindungstext", "Text für Verbindung:", text=self.label_text)
            if ok:
                self.label_text = text
                self.text_item.setPlainText(text)
                self.update_position()
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
        elif action == delete_edge and scene:
            scene.removeItem(self)
            if self in scene.edges:
                scene.edges.remove(self)
            if hasattr(scene, 'parent'):
                scene.parent.update_table()
        super().contextMenuEvent(event)

class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []
        self.connecting = False
        self.connect_source = None
        self.parent = None

class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        # ─── ganz wichtig ──────────────────────────────
        self.nodes       = []      # hier die Node-Liste
        self.edges       = []      # hier die Edge-Liste
        self.connecting  = False
        self.connect_source = None
        self.parent      = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())

        # ← Hier beginnt der Connect-Block, den Du ersetzen willst
        if self.connecting and event.button() == Qt.LeftButton and isinstance(item, NodeItem):
            dest = item

            # ── ERSETZE ab hier deinen alten Stil/Farb-Dialog … ──
            names = [tpl.name for tpl in EDGE_TEMPLATES] + ["Benutzerdefiniert"]
            choice, ok = QInputDialog.getItem(
                None,
                "Verbindungsvorlage wählen",
                "Typ:",
                names,
                0,
                False
            )
            if not ok:
                self.connecting = False
                self.connect_source = None
                return

            if choice == "Benutzerdefiniert":
                # hier kannst Du optional Deinen Fallback-Code reinpacken
                line_style, color1, color2, label = self.ask_custom_style_and_color()
            else:
                tpl = next(t for t in EDGE_TEMPLATES if t.name == choice)
                line_style   = tpl.line_style
                color1       = tpl.color1
                color2       = tpl.color2
                dash_pattern = tpl.dash_pattern
                label        = tpl.default_label

            edge = EdgeItem(
                self.connect_source,
                dest,
                color1=color1,
                color2=color2,
                dash_pattern=dash_pattern,
                label_text=label
            )
            self.addItem(edge)
            self.edges.append(edge)

            # Verbindung fertig, Tabelle updaten
            self.connecting     = False
            self.connect_source = None
            if self.parent:
                self.parent.update_table()

        else:
            super().mousePressEvent(event)

class Template:
    def __init__(self, name, shape, color1, color2, width, height, text1, text2):
        self.name = name
        self.shape = shape
        self.color1 = color1
        self.color2 = color2
        self.width = width
        self.height = height
        self.text1 = text1
        self.text2 = text2
DEFAULT_TEMPLATES = [
    Template("KNX", "rect", "#00aa00", "#00aa00", 100, 60, "KNX", ""),
    Template("DALI", "rect", "#b0b0b0", "#000000", 100, 60, "DALI", ""),
    Template("Loxone", "rect", "#00ff00", "#00ff00", 100, 60, "Loxone", ""),
    Template("Loxone Tree", "rect", "#00ff00", "#ffffff", 100, 60, "Loxone Tree", ""),
    Template("Loxone Link", "rect", "#0000ff", "#ffffff", 100, 60, "Loxone Link", ""),
    Template("Loxone Air", "rect", "#00ff00", "#000000", 100, 60, "Loxone Air", ""),
    Template("IP Symcon", "rect", "#00ffff", "#00ffff", 100, 60, "IP-Symcon", ""),
    Template("Netzwerk Gerät", "rect", "#00aaff", "#00aaff", 100, 60, "Netzwerk Gerät", ""),
    Template("EE-Bus", "rect", "#0000ff", "#0000ff", 100, 60, "EE-Bus", ""),
    Template("Modbus 485", "rect", "#ffaa00", "#ffaa00", 100, 60, "Modbus 485", ""),
    Template("Modbus 232", "rect", "#ffaa00", "#ffff00", 100, 60, "Modbus 232", ""),
    Template("M-Bus", "rect", "#ffff00", "#aa007f", 100, 60, "M-Bus", "")
]
class EdgeTemplate:
    def __init__(self, name: str,
                 line_style,               # Qt.PenStyle oder Spezial-String
                 color1,                   # z.B. Qt.red oder QColor(...)
                 color2,                   # zweite Farbe
                 dash_pattern=(8.0,4.0),   # Länge Strich, Länge Lücke
                 default_label: str = ""):
        self.name         = name
        self.line_style   = line_style
        self.color1       = QColor(color1)
        self.color2       = QColor(color2)
        self.dash_pattern = dash_pattern
        self.default_label= default_label

# Feste Verbindungsvorlagen
EDGE_TEMPLATES = [
    EdgeTemplate("KNX Hauptlinie", Qt.SolidLine,    "#ff0000", "#00ff00", (8.0,0.0), "Haupt"),
    EdgeTemplate("KNX Linie",         Qt.SolidLine,      "#00aa00", "#00aa00", (10.0,0.0), "Linie"),
    EdgeTemplate("KNX RF Linie", Qt.DashLine,     "#00aa00", "#00aa00", (5.0,5.0), "RF"),
    EdgeTemplate("Loxone Tree", Qt.SolidLine,     "#00ff00", "#ffffff", (8.0,0.0), "Tree"),
    EdgeTemplate("Loxone Link", Qt.SolidLine,     "#0000ff", "#ffffff", (8.0,0.0), "Link"),
    EdgeTemplate("Loxone Air", Qt.DashLine,     "#00ff00", "#000000", (5.0,5.0), "Air"),
    EdgeTemplate("Ethernet", Qt.DotLine,     "#000000", "#000000", (5.0,0.0), "Eth"),
    EdgeTemplate("EE-Bus", Qt.DotLine,     "#0000ff", "#0000ff", (5.0,5.0), "EE-Bus"),
    EdgeTemplate("Modbus 485", Qt.DotLine,     "#ffaa00", "#ffaa00", (5.0,5.0), "Mod 485"),
    EdgeTemplate("Modbus 232", Qt.DotLine,     "#ffaa00", "#ffff00", (5.0,5.0), "Mod 232"),
    EdgeTemplate("M-Bus", Qt.DotLine,     "#ffff00", "#aa007f", (5.0,5.0), "M-Bus"),
    # … weitere Templates …
]

class DiagramView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zoom unter Mauszeiger
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.25 if delta > 0 else 0.8
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(0.8, 0.8)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            # delegiere an MainWindow.delete_selected()
            if hasattr(self.scene(), 'parent'):
                self.scene().parent.delete_selected()
        else:
            super().keyPressEvent(event)
import sys
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme
from qfluentwidgets.common.icon import FluentIcon
from qfluentwidgets.window.fluent_window import FluentWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagramm-Editor")
        self.setGeometry(100, 100, 1000, 600)

        self.scene = DiagramScene()
        self.scene.parent = self
        self.view = DiagramView(self.scene)
        self.setCentralWidget(self.view)
        self.view.setBackgroundBrush(QBrush(Qt.white))
        self.templates = []
        self.load_templates()
        self.init_ui()
        self.update_table()
        

    def init_ui(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        add_node_action = QAction("Knoten hinzufügen", self)
        add_node_action.triggered.connect(self.add_node)
        toolbar.addAction(add_node_action)

        new_page_action = QAction("Neue Seite", self)
        new_page_action.triggered.connect(self.new_page)
        toolbar.addAction(new_page_action)

        save_action = QAction("Speichern", self)
        save_action.triggered.connect(self.save_diagram)
        toolbar.addAction(save_action)

        load_action = QAction("Laden", self)
        load_action.triggered.connect(self.load_diagram)
        toolbar.addAction(load_action)

        export_img_action = QAction("Als Bild exportieren", self)
        export_img_action.triggered.connect(self.export_image)
        toolbar.addAction(export_img_action)

        export_pdf_action = QAction("Als PDF exportieren", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        toolbar.addAction(export_pdf_action)

        export_table_action = QAction("Tabelle exportieren", self)
        export_table_action.triggered.connect(self.export_table)
        toolbar.addAction(export_table_action)

        create_template_action = QAction("Template erstellen", self)
        create_template_action.triggered.connect(self.create_template)
        toolbar.addAction(create_template_action)

        delete_template_action = QAction("Template löschen", self)
        delete_template_action.triggered.connect(self.delete_template)
        toolbar.addAction(delete_template_action)
        
        self.cb_page = QComboBox()
        self.cb_page.addItems([
            "A4 Hoch",
            "A4 Quer",
            "A3 Hoch",
            "A3 Quer"
        ])
        toolbar.addSeparator()
        toolbar.addWidget(self.cb_page)
        
        zoom_in_sc = QShortcut(QKeySequence.ZoomIn, self)
        zoom_out_sc = QShortcut(QKeySequence.ZoomOut, self)
        
        zoom_in_sc.activated.connect(self.view.zoom_in)
        zoom_out_sc.activated.connect(self.view.zoom_out)
        
        QShortcut(QKeySequence("Ctrl+N"),      self, activated=self.new_page)
        QShortcut(QKeySequence("Ctrl+O"),      self, activated=self.load_diagram)
        QShortcut(QKeySequence("Ctrl+S"),      self, activated=self.save_diagram)
        QShortcut(QKeySequence("Ctrl+Q"),      self, activated=self.close)       # schließt das Fenster

        # Diagramm-Elemente
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, activated=self.add_node)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=lambda: setattr(self.scene, 'connecting', True))

        # Exporte
        QShortcut(QKeySequence("Ctrl+I"),      self, activated=self.export_image)
        QShortcut(QKeySequence("Ctrl+P"),      self, activated=self.export_pdf)
        QShortcut(QKeySequence("Ctrl+E"),      self, activated=self.export_table)

        # Templates
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self.create_template)

        # Template-Liste rechts
        self.template_list = QListWidget()
        self.template_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.template_list.customContextMenuRequested.connect(self.show_template_context_menu)
        self.template_list.clear()
        for tpl in self.templates:
            item = self.create_template_item(tpl)
            self.template_list.addItem(item)
        self.template_list.itemDoubleClicked.connect(self.add_node_from_template)
        self.template_dock = QDockWidget("Templates", self)
        self.template_dock.setWidget(self.template_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.template_dock)

        # Tabelle rechts unten
        self.table = QTableWidget(0, 4)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        self.table.setHorizontalHeaderLabels(["Protokoll", "Adresse", "Form/Verbindung", "Standort/Position"])
        self.table_dock = QDockWidget("Tabelle", self)
        self.table_dock.setWidget(self.table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.table_dock)
        
        # ── Kundendaten-Dock ────────────────────────────
        cust_widget = QWidget()
        form = QFormLayout(cust_widget)
        self.le_customer    = QLineEdit()
        self.le_address     = QLineEdit()
        self.le_project_no  = QLineEdit()
        self.le_order_no    = QLineEdit()
        form.addRow("Kundennummer:",    self.le_customer)
        form.addRow("Anschrift:",       self.le_address)
        form.addRow("Projekt-Nr.:",     self.le_project_no)
        form.addRow("Auftrags-Nr.:",    self.le_order_no)
        cust_widget.setLayout(form)

        self.cust_dock = QDockWidget("Kundendaten", self)
        self.cust_dock.setWidget(cust_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.cust_dock)
        
        # Toggle-Actions für die drei Docks
        self.action_toggle_customer = QAction("Kundendaten", self, checkable=True)
        self.action_toggle_customer.setChecked(self.cust_dock.isVisible())
        self.action_toggle_customer.toggled.connect(self.cust_dock.setVisible)
        self.cust_dock.visibilityChanged.connect(self.action_toggle_customer.setChecked)
        toolbar.addAction(self.action_toggle_customer)

        self.action_toggle_templates = QAction("Templates", self, checkable=True)
        self.action_toggle_templates.setChecked(self.template_dock.isVisible())
        self.action_toggle_templates.toggled.connect(self.template_dock.setVisible)
        self.template_dock.visibilityChanged.connect(self.action_toggle_templates.setChecked)
        toolbar.addAction(self.action_toggle_templates)

        self.action_toggle_table = QAction("Tabelle", self, checkable=True)
        self.action_toggle_table.setChecked(self.table_dock.isVisible())
        self.action_toggle_table.toggled.connect(self.table_dock.setVisible)
        self.table_dock.visibilityChanged.connect(self.action_toggle_table.setChecked)
        toolbar.addAction(self.action_toggle_table)
        self.refresh_template_list()
        
    def delete_selected(self):
        # lösche alle selektierten Knoten und Kanten
        for item in list(self.scene.selectedItems()):
            if isinstance(item, NodeItem):
                # entferne zuerst alle angrenzenden Kanten
                for edge in list(self.scene.edges):
                    if edge.source is item or edge.dest is item:
                        self.scene.removeItem(edge)
                        self.scene.edges.remove(edge)
                # dann den Node
                self.scene.removeItem(item)
                self.scene.nodes.remove(item)
            elif isinstance(item, EdgeItem):
                self.scene.removeItem(item)
                self.scene.edges.remove(item)
        self.update_table()    

    def create_template_item(self, tpl):
        item = QListWidgetItem(tpl.name)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        # Zweifarbiges Icon
        r = QRectF(0, 0, 32, 32)
        path = QPainterPath()
        if tpl.shape == "rect":
            path.addRect(r)
        elif tpl.shape == "ellipse":
            path.addEllipse(r)
        elif tpl.shape == "diamond":
            points = [QPointF(16, 0), QPointF(32, 16), QPointF(16, 32), QPointF(0, 16)]
            path.addPolygon(QPolygonF(points))
        elif tpl.shape == "triangle":
            points = [QPointF(16, 0), QPointF(32, 32), QPointF(0, 32)]
            path.addPolygon(QPolygonF(points))
        elif tpl.shape == "hexagon":
            pts = [
                QPointF(8, 0), QPointF(24, 0), QPointF(32, 16),
                QPointF(24, 32), QPointF(8, 32), QPointF(0, 16)
            ]
            path.addPolygon(QPolygonF(pts))
        painter.save()
        painter.setBrush(QBrush(QColor(tpl.color1)))
        painter.setPen(QPen(Qt.black))
        painter.setClipRect(QRectF(0, 0, 32, 16))
        painter.drawPath(path)
        painter.restore()
        painter.save()
        painter.setBrush(QBrush(QColor(tpl.color2)))
        painter.setPen(QPen(Qt.black))
        painter.setClipRect(QRectF(0, 16, 32, 16))
        painter.drawPath(path)
        painter.restore()
        painter.setPen(QPen(Qt.black))
        painter.drawPath(path)
        painter.end()
        item.setIcon(QIcon(pixmap))
        return item

    def show_template_context_menu(self, pos):
        item = self.template_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        delete_action = menu.addAction("Template löschen")
        action = menu.exec_(self.template_list.mapToGlobal(pos))
        if action == delete_action:
            row = self.template_list.row(item)
            del self.templates[row]
            self.template_list.takeItem(row)
            self.save_templates()

    def add_node(self):
        # Standort abfragen
        standort, ok = QInputDialog.getText(self, "Standort eingeben", "Standort:")
        if not ok:
           standort = ""
        # Node erstellen und Standort zuweisen
        node = NodeItem()
        node.standort = standort
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
        self.scene.nodes.append(node)
        self.update_table()

    def add_node_from_template(self, item: QListWidgetItem):
        name = item.text()
        tpl = next((t for t in self.templates if t.name == name), None)
        if tpl:
            # Standort abfragen
            standort, ok = QInputDialog.getText(self, "Standort eingeben", "Standort:")
            if not ok:
                standort = ""
            node = NodeItem(
                shape=tpl.shape,
                rect=QRectF(0, 0, tpl.width, tpl.height),
                text1=tpl.text1,
                text2=tpl.text2,
                color1=QColor(tpl.color1),
                color2=QColor(tpl.color2)
            )
            node.standort = standort
            
            node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
            self.update_table()

    def new_page(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Neue Seite")
        msg.setText("Möchten Sie das aktuelle Diagramm speichern?")
        save_btn    = msg.addButton("Speichern",   QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Verwerfen",   QMessageBox.DestructiveRole)
        cancel_btn  = msg.addButton("Abbrechen",   QMessageBox.RejectRole)
        msg.setDefaultButton(save_btn)
        msg.exec_()

        clicked = msg.clickedButton()
        if   clicked == save_btn:
            if not self.save_diagram():
                return  # Speichern abgebrochen → Abbruch
        elif clicked == cancel_btn:
            return     # Abbruch → nichts tun

        # Save bestätigt oder Verwerfen:
        for itm in list(self.scene.items()):
            self.scene.removeItem(itm)
        self.scene.nodes.clear()
        self.scene.edges.clear()
        self.table.setRowCount(0)

    def save_diagram(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(self, "Diagramm speichern", "", "JSON-Datei (*.json)")
        if not path:
            return False
        data = {
            "metadata": {
                "customer":   self.le_customer.text(),
                "address":    self.le_address.text(),
                "project_no": self.le_project_no.text(),
                "order_no":   self.le_order_no.text()
            },
            "nodes": [], 
            "edges": []}
        for idx, node in enumerate(self.scene.nodes):
            data["nodes"].append({
                "id": idx,
                "shape": node.shape,
                "color1": node.color1.name(),
                "color2": node.color2.name(),
                "x": node.pos().x(),
                "y": node.pos().y(),
                "width": node.rect().width(),
                "height": node.rect().height(),
                "text1": node.text1,
                "text2": node.text2
            })
        for edge in self.scene.edges:
            src_id = self.scene.nodes.index(edge.source)
            dest_id = self.scene.nodes.index(edge.dest)
            style = edge.pen.style()
            label = edge.label_text
            data["edges"].append({"source": src_id, "dest": dest_id, "style": style, "label": label})
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Gespeichert", "Diagramm wurde gespeichert.")
        return True

    def load_diagram(self):
        path, _ = QFileDialog.getOpenFileName(self, "Diagramm laden", "", "JSON-Datei (*.json)")
        if not path:
            return
        with open(path, "r") as f:
            data = json.load(f)
        meta = data.get("metadata", {})
        self.le_customer.  setText(meta.get("customer", ""))
        self.le_address.   setText(meta.get("address", ""))
        self.le_project_no.setText(meta.get("project_no", ""))
        self.le_order_no.  setText(meta.get("order_no", ""))
        for itm in list(self.scene.items()):
            self.scene.removeItem(itm)
        self.scene.nodes.clear()
        self.scene.edges.clear()
        for node_data in data.get("nodes", []):
            node = NodeItem(
                shape=node_data.get("shape", "rect"),
                rect=QRectF(0, 0, node_data.get("width", 100), node_data.get("height", 60)),
                text1=node_data.get("text1", ""),
                text2=node_data.get("text2", ""),
                color1=QColor(node_data.get("color1", "lightgray")),
                color2=QColor(node_data.get("color2", "white"))
            )
            node.setPos(node_data.get("x", 0), node_data.get("y", 0))
            self.scene.addItem(node)
            self.scene.nodes.append(node)
        for edge_data in data.get("edges", []):
            src = self.scene.nodes[edge_data.get("source")]
            dest = self.scene.nodes[edge_data.get("dest")]
            style = edge_data.get("style", Qt.SolidLine)
            label = edge_data.get("label", "")
            edge = EdgeItem(src, dest, style, label)
            self.scene.addItem(edge)
            self.scene.edges.append(edge)
        self.update_table()
        QMessageBox.information(self, "Geladen", "Diagramm wurde geladen.")

    def export_image(self):
        # 1) Dateiauswahl
        path, _ = QFileDialog.getSaveFileName(
            self, "Als Bild exportieren", "", "PNG (*.png);;JPEG (*.jpg)"
        )
        if not path:
            return

        # 2) Szene prüfen
        rect = self.scene.itemsBoundingRect()
        if rect.isEmpty():
            QMessageBox.warning(self, "Exportieren", "Keine Elemente in der Szene zum Exportieren.")
            return

        # 3) DPI und mm→px-Funktion
        dpi    = 300
        mm2px  = lambda mm: int(mm * 300 / 25.4)

        # 4) Papierformat aus ComboBox
        choice = self.cb_page.currentText()
        if "A4" in choice:
            w_mm, h_mm = 210, 297
        else:
            w_mm, h_mm = 297, 420
        if "Quer" in choice:
            w_mm, h_mm = h_mm, w_mm

        img_w   = mm2px(w_mm)
        img_h   = mm2px(h_mm)
        margin  = mm2px(10)

        # 5) QImage und QPainter anlegen
        image = QImage(img_w, img_h, QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.black)

        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        fm = painter.fontMetrics()

        # Die Daten-Paare
        data = [
            ("Kundennummer", self.le_customer.text()),
            ("Anschrift",    self.le_address.text()),
            ("Projekt-Nr.",  self.le_project_no.text()),
            ("Auftrags-Nr.", self.le_order_no.text())
        ]

        # Zeilenhöhe (Höhe + Padding)
        row_h_px = fm.height() + 8

        # Breite des breitesten Labels
        max_label = max(label for label, _ in data)
        label_w   = fm.horizontalAdvance(max_label)

        # Puffer in mm ins Pixel umrechnen (z.B. 5 mm extra)
        mm2px = lambda mm: int(mm * 300 / 25.4)
        padding_px = mm2px(5)

        # Erste Spalte: exakte Label-Breite + Puffer
        col1_px = label_w + padding_px

        # Werte-Spalte: breitestes Value + Puffer
        max_value = max(val for _, val in data)
        val_w     = fm.horizontalAdvance(max_value)
        col2_px   = val_w + padding_px

        # Gesamt-Tabelle
        table_w_px = col1_px + col2_px
        table_h_px = row_h_px * len(data)

        # Position der Tabelle
        table_x = margin
        table_y = margin


        # 8) Zeichne Rahmen & Gitterlinien
        painter.drawRect(table_x, table_y, table_w_px, table_h_px)
        for i in range(1, len(data)):
            y = table_y + row_h_px * i
            painter.drawLine(table_x, y, table_x + table_w_px, y)
        painter.drawLine(table_x + col1_px, table_y,
                         table_x + col1_px, table_y + table_h_px)

        # 9) Zellen-Texte mit Umbruch
        for i, (lbl, val) in enumerate(data):
            cell_y = table_y + row_h_px * i
            # Label-Zelle
            rect_lbl = QRect(
                table_x + 2,
                cell_y + 2,
                col1_px - 4,
                row_h_px - 4
            )
            painter.drawText(
                rect_lbl,
                Qt.AlignLeft | Qt.AlignVCenter,
                lbl
            )
            # Value-Zelle
            rect_val = QRect(
                table_x + col1_px + 2,
                cell_y + 2,
                col2_px - 4,
                row_h_px - 4
            )
            painter.drawText(
                rect_val,
                Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap,
                val
            )

        # 10) Diagramm direkt unter der Tabelle rendern
        painter.save()
        painter.translate(margin, margin + table_h_px + mm2px(5))  # 5mm Abstand
        avail_w = img_w  - 2*margin
        avail_h = img_h  - margin - table_h_px - mm2px(5)
        scale   = min(avail_w/rect.width(), avail_h/rect.height())
        painter.scale(scale, scale)
        self.scene.render(painter,
                          QRectF(0, 0, rect.width(), rect.height()),
                          rect)
        painter.restore()

        # 11) Ende und speichern
        painter.end()
        image.save(path)
        QMessageBox.information(self, "Exportiert", "Bild wurde exportiert.")

    def export_pdf(self):
        # 1) Dateiauswahl
        path, _ = QFileDialog.getSaveFileName(
            self, "Als PDF exportieren", "", "PDF-Datei (*.pdf)"
        )
        if not path:
            return

        # 2) Printer konfigurieren
        from PyQt5.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)

        choice = self.cb_page.currentText()
        # Papierformat
        if "A4" in choice:
            printer.setPaperSize(QPrinter.A4)
        else:
            printer.setPaperSize(QPrinter.A3)
        # Orientierung
        printer.setOrientation(
            QPrinter.Landscape if "Quer" in choice else QPrinter.Portrait
        )

        # 3) Szene prüfen
        scene_rect = self.scene.itemsBoundingRect()
        if scene_rect.isEmpty():
            QMessageBox.warning(self, "Exportieren", "Keine Elemente in der Szene vorhanden.")
            return

        page_rect = printer.pageRect()

        # 4) Painter EINMAL beginnen
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Exportieren", "Kann PDF-Renderer nicht starten.")
            return
        painter.setRenderHint(QPainter.Antialiasing)

        # 5) Schrift & Metadaten-Tabelle
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)

        # Dynamische Tabelle
        data = [
            ("Kundennummer", self.le_customer.text()),
            ("Anschrift",    self.le_address.text()),
            ("Projekt-Nr.",  self.le_project_no.text()),
            ("Auftrags-Nr.", self.le_order_no.text())
        ]
        fm = painter.fontMetrics()
        row_h   = fm.height() + 8
        labels = [label for label, _ in data]
        max_label = max(labels, key=lambda lbl: fm.horizontalAdvance(lbl))
        label_w   = fm.horizontalAdvance(max_label)
        avg_char = fm.horizontalAdvance("M")  # Breite eines Großbuchstabens M
        padding  = avg_char * 6
        col1_w  = max(label_w + padding, 120)
        max_value = max(value for _, value in data)
        value_w   = fm.horizontalAdvance(max_value)
        col2_w  = value_w + 20
        table_w = col1_w + col2_w
        table_x = page_rect.x() + 10
        table_y = page_rect.y() + 10
        table_h = row_h * len(data)

        # Rahmen und Linien
        painter.drawRect(table_x, table_y, table_w, table_h)
        for i in range(len(data)):
            y = table_y + row_h * (i+1)
            painter.drawLine(table_x, y, table_x + table_w, y)
        painter.drawLine(table_x + col1_w, table_y,
                         table_x + col1_w, table_y + table_h)

        # Zelltexte
        for i, (label, value) in enumerate(data):
            cell_y = table_y + row_h * i
            # Label‐Zelle
            r_lbl = QRectF(table_x + 2,
                            cell_y + 2,
                            col1_w - 4,
                            row_h - 4)
            painter.drawText(r_lbl,
                            Qt.AlignLeft | Qt.AlignVCenter,
                            label)

            # Value‐Zelle mit WordWrap
            r_val = QRectF(table_x + col1_w + 2,
                            cell_y + 2,
                            col2_w - 4,
                            row_h - 4)
            painter.drawText(r_val,
                            Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap,
                            value)

        # 6) Diagramm rendern
        header_h = table_h + 20
        footer_h = 36
        avail_w = page_rect.width()
        avail_h = page_rect.height() - header_h - footer_h
        scale   = min(avail_w / scene_rect.width(), avail_h / scene_rect.height())

        painter.save()
        painter.translate(page_rect.x(), page_rect.y() + header_h)
        painter.scale(scale, scale)
        self.scene.render(painter,
                          QRectF(0, 0, scene_rect.width(), scene_rect.height()),
                          scene_rect)
        painter.restore()

        # 7) Footer-Text
        painter.drawText(
            page_rect.x() + 10,
            page_rect.y() + page_rect.height() - 5,
            f"{self.le_customer.text()} | {self.le_address.text()} | "
            f"{self.le_project_no.text()} | {self.le_order_no.text()}"
        )

        # 8) Painter beenden
        painter.end()
        QMessageBox.information(self, "Exportiert", "PDF wurde exportiert.")

    def export_table(self):
        path, _ = QFileDialog.getSaveFileName(self, "Tabelle exportieren", "", "CSV-Datei (*.csv)")
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            # Kopfzeile
            f.write("Kundennummer,Anschrift,Projekt-Nr.,Auftrags-Nr.\n")
            f.write(f"{self.le_customer.text()},"
                    f"{self.le_address.text()},"
                    f"{self.le_project_no.text()},"
                    f"{self.le_order_no.text()}\n\n")
            # dann Tabelle
            rows = self.table.rowCount()
            cols = self.table.columnCount()
            for r in range(rows):
                vals = [self.table.item(r,c).text() if self.table.item(r,c) else ""
                        for c in range(cols)]
                f.write(','.join(vals) + '\n')
        QMessageBox.information(self, "Exportiert", "Tabelle wurde exportiert.")

    def create_template(self):
        name, ok = QInputDialog.getText(self, "Template-Name", "Name des Templates:")
        if not ok or not name:
            return
        shapes = ["Rechteck", "Ellipse", "Raute", "Dreieck", "Hexagon"]
        shape_str, ok = QInputDialog.getItem(self, "Form wählen", "Form:", shapes, 0, False)
        if not ok:
            return
        mapping = {
            "Rechteck": "rect",
            "Ellipse": "ellipse",
            "Raute": "diamond",
            "Dreieck": "triangle",
            "Hexagon": "hexagon"
        }
        shape = mapping[shape_str]

        col1 = QColorDialog.getColor(QColor("lightgray"))
        color1 = col1.name() if col1.isValid() else "lightgray"
        col2 = QColorDialog.getColor(QColor("white"))
        color2 = col2.name() if col2.isValid() else "white"

        width, ok = QInputDialog.getInt(self, "Breite eingeben", "Breite:", 100, 10, 1000, 1)
        if not ok:
            return
        height, ok = QInputDialog.getInt(self, "Höhe eingeben", "Höhe:", 60, 10, 1000, 1)
        if not ok:
            return
        text1, ok1 = QInputDialog.getText(self, "Text eingeben", "Protokoll:")
        if not ok1:
            return
        text2, ok2 = QInputDialog.getText(self, "Text eingeben", "Adresse:")
        if not ok2:
            return

        tpl = Template(
            name=name,
            shape=shape,
            color1=color1,
            color2=color2,
            width=width,
            height=height,
            text1=text1,
            text2=text2
        )
        self.templates.append(tpl)
        item = self.create_template_item(tpl)
        self.template_list.addItem(item)
        self.save_templates()
        self.refresh_template_list()
        QMessageBox.information(self, "Template erstellt", f"Template '{name}' wurde erstellt.")

    def delete_template(self):
        current = self.template_list.currentItem()
        if not current:
            return
        row = self.template_list.row(current)
        del self.templates[row]
        self.template_list.takeItem(row)
        self.templates.append(remove_tpl)
        self.save_templates()
        self.refresh_template_list()

    def load_templates(self):
        """Lädt zuerst DEFAULT_TEMPLATES und dann die Datei,
        überspringt aber doppelte Namen aus der Datei."""
        # 1) Starte mit einer Kopie der festen Default-Templates
        self.templates = DEFAULT_TEMPLATES.copy()

        # 2) Wenn es die Datei gibt, lade sie
        if not os.path.exists(TEMPLATES_FILE):
            return
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 3) Erstelle ein Set aller bereits bekannten Namen
        existing = {tpl.name for tpl in self.templates}

        # 4) Füge aus der Datei nur hinzu, was noch nicht vorhanden ist
        for tpl_data in data:
            name = tpl_data.get("name", "")
            if not name or name in existing:
                continue
            tpl = Template(
                name=name,
                shape=tpl_data.get("shape", "rect"),
                color1=tpl_data.get("color1", "lightgray"),
                color2=tpl_data.get("color2", "white"),
                width=tpl_data.get("width", 100),
                height=tpl_data.get("height", 60),
                text1=tpl_data.get("text1", ""),
                text2=tpl_data.get("text2", "")
            )
            self.templates.append(tpl)
            existing.add(name)

    def save_templates(self):
        data = []
        for tpl in self.templates:
            data.append({
                "name": tpl.name,
                "shape": tpl.shape,
                "color1": tpl.color1,
                "color2": tpl.color2,
                "width": tpl.width,
                "height": tpl.height,
                "text1": tpl.text1,
                "text2": tpl.text2
            })
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def update_table(self):
        total_rows = len(self.scene.nodes) + len(self.scene.edges)
        self.table.setRowCount(total_rows)
        row = 0
        # Knoten
        for node in self.scene.nodes:
            self.table.setItem(row, 0, QTableWidgetItem(node.text1))
            self.table.setItem(row, 1, QTableWidgetItem(node.text2))
            self.table.setItem(row, 2, QTableWidgetItem(node.shape))
            # Standort und Position
            standort = getattr(node, 'standort', "")
            self.table.setItem(row, 3, QTableWidgetItem(standort))
            
            for col in (0, 1):
                item = self.table.item(row, col)
                if not item:
                    continue
                bg = node.color1 if col == 0 else node.color2
                item.setBackground(QBrush(bg))
                # Schriftfarbe je nach Helligkeit
                fg = Qt.white if is_color_dark(bg) else Qt.black
                item.setForeground(QBrush(fg))

            
            row += 1
            
        # Verbindungen
        for edge in self.scene.edges:
            src = edge.source.text1
            dst = edge.dest.text1
            arrow = getattr(edge, 'arrow', '-') #aus EgdeItem.arrow
            # Spalte 0
            self.table.setItem(row, 0, QTableWidgetItem("Verbindung"))
            #Spalte 1: Protokoll/Adresse mit wählbarem Arrow
            item = QTableWidgetItem(f"{src}{arrow}{dst}")
            #optional: zentrieren
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item)
            style_name = {
                Qt.SolidLine: "Twisted Pair",
                Qt.DashLine: "Funk",
                Qt.DotLine: "Ethernet",
                Qt.DashDotLine: "Bus",
                Qt.DashDotDotLine: "Strich-Punkt-Punkt"
            }.get(edge.pen().style(), "Twisted Pair")
            self.table.setItem(row, 2, QTableWidgetItem(style_name))
            # Für Verbindungen bleibt die Standort-Spalte leer
            self.table.setItem(row, 3, QTableWidgetItem(""))
            row += 1
    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle("Beenden")
        msg.setText("Möchten Sie das aktuelle Diagramm speichern, bevor Sie beenden?")
        save_btn    = msg.addButton("Speichern",   QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Verwerfen",   QMessageBox.DestructiveRole)
        cancel_btn  = msg.addButton("Abbrechen",   QMessageBox.RejectRole)
        msg.setDefaultButton(save_btn)
        msg.exec_()

        clicked = msg.clickedButton()
        if   clicked == save_btn:
            if self.save_diagram():
                event.accept()
            else:
                event.ignore()
        elif clicked == discard_btn:
            event.accept()
        else:  # Abbrechen
            event.ignore()
            
    def on_table_double_click(self, row: int, col: int):
        # nur Spalte 1 und nur, wenn es eine Verbindungs-Zeile ist
        num_nodes = len(self.scene.nodes)
        if col != 1 or row < num_nodes:
            return

        # Finde das zugehörige EdgeItem
        edge = self.scene.edges[row - num_nodes]
        # aktuelle Arrow-Variante
        current = edge.arrow
        # Liste der möglichen Pfeile
        options = ["-", "→", "←", "↔"]
        # Startindex ermitteln
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0
        # Dialog
        arrow, ok = QInputDialog.getItem(
            self,
            "Pfeilrichtung wählen",
            "Richtung:",
            options,
            idx,
            False
        )
        if not ok:
            return

        # übernehmen
        edge.arrow = arrow
        # Tabelle updaten (nur diese Zelle)
        src = edge.source.text1
        dst = edge.dest.text1
        self.table.item(row, col).setText(f"{src} {arrow} {dst}")
        
    def delete_selected(self):
        # lösche alle selektierten Nodes und Edges
        for item in list(self.scene.selectedItems()):
            if isinstance(item, NodeItem):
                # verbundene Kanten entfernen
                for edge in list(self.scene.edges):
                    if edge.source is item or edge.dest is item:
                        self.scene.removeItem(edge)
                        self.scene.edges.remove(edge)
                # dann den Node
                self.scene.removeItem(item)
                self.scene.nodes.remove(item)
            elif isinstance(item, EdgeItem):
                self.scene.removeItem(item)
                self.scene.edges.remove(item)
        self.update_table()  
        
    def refresh_template_list(self):
        # 1) Templates nach Name deduplizieren
        seen = set()
        unique = []
        for tpl in self.templates:
            if tpl.name not in seen:
                seen.add(tpl.name)
                unique.append(tpl)
        self.templates = unique

        # 2) QListWidget neu befüllen
        self.template_list.clear()
        for tpl in self.templates:
            item = self.create_template_item(tpl)
            self.template_list.addItem(item)

import sys
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet

if __name__ == "__main__":
    import os, sys
    from PyQt5.QtWidgets import QApplication, QStyleFactory

    # 1) Unter Windows 11 das native Mica-Fensterdekor + Darkmode erzwingen
    os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"

    # 2) QApplication anlegen und nativen Style aktivieren
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("windowsvista"))

    # 3) QSS-Theme laden
    app.setStyleSheet("""
    /* ------------------------------ Hauptfenster ------------------------------ */
    QMainWindow {
      background: #F3F3F3;
    }

    /* -------------------------------- Toolbar --------------------------------- */
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

    /* ------------------------------ Tabellenview ------------------------------ */
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
      background: #0078D4;     /* Windows-11-Blau */
      color: #FFFFFF;
    }

    /* ------------------------------ Buttons ------------------------------ */
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

    /* ---------------------------- Eingabefelder ---------------------------- */
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

    /* ---------------------------- GraphicsView ---------------------------- */
    QGraphicsView {
      background: #F3F3F3;
      border: none;
    }
    """)

    # 4) Hauptfenster starten
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
