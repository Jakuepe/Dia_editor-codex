from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QInputDialog
from PyQt5.QtGui import QTransform, QPixmap, QPainter, QBrush, QColor, QPen
from PyQt5.QtCore import Qt

from models import NodeItem, EdgeItem, EDGE_TEMPLATES


class DiagramScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []
        self.connecting = False
        self.connect_source = None
        self.parent = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if self.connecting and event.button() == Qt.LeftButton and isinstance(item, NodeItem):
            dest = item
            names = [tpl.name for tpl in EDGE_TEMPLATES] + ["Benutzerdefiniert"]
            choice, ok = QInputDialog.getItem(None, "Verbindungsvorlage wählen", "Typ:", names, 0, False)
            if not ok:
                self.connecting = False
                self.connect_source = None
                return
            if choice == "Benutzerdefiniert":
                line_style, color1, color2, label = self.ask_custom_style_and_color()
            else:
                tpl = next(t for t in EDGE_TEMPLATES if t.name == choice)
                line_style = tpl.line_style
                color1 = tpl.color1
                color2 = tpl.color2
                dash_pattern = tpl.dash_pattern
                label = tpl.default_label
            edge = EdgeItem(self.connect_source, dest, color1=color1, color2=color2, dash_pattern=dash_pattern, label_text=label)
            self.addItem(edge)
            self.edges.append(edge)
            self.connecting = False
            self.connect_source = None
            if self.parent:
                self.parent.update_table()
        else:
            super().mousePressEvent(event)

    def ask_custom_style_and_color(self):
        # Placeholder for custom style dialog
        return Qt.SolidLine, Qt.black, Qt.black, ""


class DiagramView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            if hasattr(self.scene(), 'parent'):
                self.scene().parent.delete_selected()
        else:
            super().keyPressEvent(event)
