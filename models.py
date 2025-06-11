import json
import os
from PyQt5.QtWidgets import (
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem, QMenu,
    QColorDialog, QInputDialog
)
from PyQt5.QtGui import (
    QBrush, QColor, QPen, QFont, QPainterPath, QPolygonF
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF


TEMPLATES_FILE = "templates.json"


def is_color_dark(color: QColor, threshold: float = 128.0) -> bool:
    """Return True if the color's luminance is below the given threshold."""
    r, g, b = color.red(), color.green(), color.blue()
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < threshold


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
        padding_x = 20
        padding_y = 20
        r1 = self.text_item1.boundingRect()
        r2 = self.text_item2.boundingRect()
        new_width = max(self.min_width, r1.width(), r2.width()) + padding_x
        new_height = max(self.min_height, r1.height() + r2.height()) + padding_y
        self.setRect(QRectF(0, 0, new_width, new_height))
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
        painter.save()
        painter.setBrush(QBrush(self.color1))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(r.x(), r.y(), r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
        painter.save()
        painter.setBrush(QBrush(self.color2))
        painter.setPen(self.pen)
        painter.setClipRect(QRectF(r.x(), r.y() + r.height()/2, r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()
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
        c1 = self.color1
        self.text_item1.setDefaultTextColor(Qt.white if is_color_dark(c1) else Qt.black)
        c2 = self.color2
        self.text_item2.setDefaultTextColor(Qt.white if is_color_dark(c2) else Qt.black)


class EdgeItem(QGraphicsLineItem):
    def __init__(self, source, dest, color1=Qt.red, color2=Qt.green, dash_pattern=(8.0, 4.0), label_text=""):
        super().__init__()
        self.source = source
        self.dest = dest
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.dash_pattern = dash_pattern
        self.pen_width = 2.0
        self.text_item = QGraphicsTextItem(label_text, self)
        self.text_item.setDefaultTextColor(Qt.black)
        self.setPen(QPen(Qt.NoPen))
        self.setZValue(-1)
        self.text_item.setZValue(1)

    def update_position(self):
        p1 = self.source.sceneBoundingRect().center()
        p2 = self.dest.sceneBoundingRect().center()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        mid = QLineF(p1, p2).pointAt(0.5)
        rect = self.text_item.boundingRect()
        self.text_item.setPos(mid.x() - rect.width()/2, mid.y() - rect.height()/2)

    def paint(self, painter, option, widget):
        self.update_position()
        line = self.line()
        length = line.length()
        if length <= 0:
            return
        dash, gap = self.dash_pattern
        pos = 0.0
        toggle = False
        while pos < length:
            start_pt = line.pointAt(pos/length)
            end_pos = min(pos + dash, length)
            end_pt = line.pointAt(end_pos/length)
            pen = QPen(self.color1 if not toggle else self.color2, self.pen_width)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(QLineF(start_pt, end_pt))
            pos += dash + gap
            toggle = not toggle

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        edit_label = menu.addAction("Text bearbeiten")
        delete_edge = menu.addAction("Verbindung löschen")
        action = menu.exec_(event.screenPos())
        scene = self.scene()
        if action == change_color and scene:
            col = QColorDialog.getColor(self.pen.color())
            if col.isValid():
                self.pen.setColor(col)
                self.setPen(self.pen)
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


class EdgeTemplate:
    def __init__(self, name: str, line_style, color1, color2, dash_pattern=(8.0, 4.0), default_label: str = ""):
        self.name = name
        self.line_style = line_style
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.dash_pattern = dash_pattern
        self.default_label = default_label


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

EDGE_TEMPLATES = [
    EdgeTemplate("KNX Hauptlinie", Qt.SolidLine, "#ff0000", "#00ff00", (8.0, 0.0), "Haupt"),
    EdgeTemplate("KNX Linie", Qt.SolidLine, "#00aa00", "#00aa00", (10.0, 0.0), "Linie"),
    EdgeTemplate("KNX RF Linie", Qt.DashLine, "#00aa00", "#00aa00", (5.0, 5.0), "RF"),
    EdgeTemplate("Loxone Tree", Qt.SolidLine, "#00ff00", "#ffffff", (8.0, 0.0), "Tree"),
    EdgeTemplate("Loxone Link", Qt.SolidLine, "#0000ff", "#ffffff", (8.0, 0.0), "Link"),
    EdgeTemplate("Loxone Air", Qt.DashLine, "#00ff00", "#000000", (5.0, 5.0), "Air"),
    EdgeTemplate("Ethernet", Qt.DotLine, "#000000", "#000000", (5.0, 0.0), "Eth"),
    EdgeTemplate("EE-Bus", Qt.DotLine, "#0000ff", "#0000ff", (5.0, 5.0), "EE-Bus"),
    EdgeTemplate("Modbus 485", Qt.DotLine, "#ffaa00", "#ffaa00", (5.0, 5.0), "Mod 485"),
    EdgeTemplate("Modbus 232", Qt.DotLine, "#ffaa00", "#ffff00", (5.0, 5.0), "Mod 232"),
    EdgeTemplate("M-Bus", Qt.DotLine, "#ffff00", "#aa007f", (5.0, 5.0), "M-Bus"),
]
