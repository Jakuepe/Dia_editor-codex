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
    QLineEdit, QFormLayout, QWidget, QStyleFactory, QDateEdit,  QGraphicsItem
)
os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
from qfluentwidgets.window.fluent_window import ( FluentWindow )
from qfluentwidgets import ( Theme )
from PyQt5.QtGui import (
    QBrush, QColor, QPen, QFont, QPainter, QImage, QTransform, QTextOption, 
    QPolygonF, QPixmap, QIcon, QPainterPath, QKeySequence, QPalette, QPainterPathStroker
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QRect, QPoint, QLineF, QPointF, QDate
def is_color_dark(color: QColor, threshold: float = 128.0) -> bool:
    """Berechnet die Helligkeit und gibt True zurück, wenn sie unter threshold liegt."""
    # Wahrnehmungs-Helligkeit (Luminanz) nach ITU-R BT.601
    r, g, b = color.red(), color.green(), color.blue()
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < threshold

TEMPLATES_FILE = "templates.json"

class NodeItem(QGraphicsRectItem):
    def __init__(self,
                shape="rect",
                rect=QRectF(0, 0, 100, 80),
                text1="Titel",
                text2="",
                text3="",
                color1=QColor("lightgray"),
                color2=QColor("white")):
        super().__init__(rect)
        self.padding_x       = 10
        self.padding_y_top   = 8
        self.padding_y_bot   = 8
        self.spacing12       = 4
        self.spacing23       = 4
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.node_shape = shape
        self.padding_x          = 20  # links + rechts
        self.top_bottom_padding = 5   # oben + unten
        self.spacing12          = 5   # Abstand Zeile1–2
        self.spacing23          = 0   # Abstand Zeile2–3

        self.text1 = text1
        self.text2 = text2
        self.text3 = text3
        # Fixe Höhe und dynamische Breite
        self.min_width  = rect.width()
        self.min_height = rect.height()
        self.color1     = color1
        self.color2     = color2
        self._pen        = QPen(Qt.black)
        self.setPen(self._pen)
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable
        )

        # Texte
        self.text_item1 = QGraphicsTextItem(self.text1, self)
        self.text_item2 = QGraphicsTextItem(self.text2, self)
        self.text_item3 = QGraphicsTextItem(self.text3, self)
        for txt in (self.text_item1, self.text_item2, getattr(self, 'text_item3', None)):
            if not txt:
                continue
            opt = txt.document().defaultTextOption()
            opt.setWrapMode(QTextOption.NoWrap)     # kein Umbruch
            opt.setAlignment(Qt.AlignCenter)        # Text zentriert innerhalb seiner Breite
            txt.document().setDefaultTextOption(opt)

        # Initiales Layout
        self.adjustSize()
        self.center_texts()
        

        opt = self.text_item1.document().defaultTextOption()
        opt.setWrapMode(QTextOption.NoWrap)
        self.text_item1.document().setDefaultTextOption(opt)

        # Dasselbe für text_item2 und text_item3:
        opt = self.text_item2.document().defaultTextOption()
        opt.setWrapMode(QTextOption.NoWrap)
        self.text_item2.document().setDefaultTextOption(opt)
        
        opt = self.text_item3.document().defaultTextOption()
        opt.setWrapMode(QTextOption.NoWrap)
        self.text_item3.document().setDefaultTextOption(opt)
        
        self.text_item1.setTextWidth(self.rect().width() - self.padding_x)
        self.text_item2.setTextWidth(self.rect().width() - self.padding_x)
        self.text_item3.setTextWidth(self.rect().width() - self.padding_x)

        # Fonts
        f1 = QFont(); f1.setPointSize(10)
        f2 = QFont(); f2.setPointSize(8)
        self.text_item1.setFont(f1)
        self.text_item2.setFont(f2)
        self.text_item3.setFont(f2)

        
    def _update_layout(self):
        """Zentraler Aufruf nach jeder Text-/Größenänderung."""
        self.adjustSize()
        self._position_texts()
        self._update_text_colors()
        
    def adjustSize(self):
        """
        Höhe bleibt fix für genau 2 Zeilen (Text1 + Text2),
        Breite passt sich an alle vorhandenen Zeilen (inkl. Text3) an.
        """
        # ── 1) Höhe nur auf Basis von Text1 & Text2 ────────────────
        # Höhe der Zeilen (0, falls leer)
        h1 = self.text_item1.boundingRect().height() if self.text_item1.toPlainText().strip() else 0
        h2 = self.text_item2.boundingRect().height() if self.text_item2.toPlainText().strip() else 0

        # Gesamt-Höhe für exakt 2 Zeilen plus Padding
        two_line_h = (
            self.padding_y_top    # oberes Padding
            + h1
            + self.spacing12      # Abstand zwischen Zeile1 & Zeile2
            + h2
            + self.padding_y_bot  # unteres Padding
        )
        new_h = max(self.min_height, two_line_h)

        # ── 2) Breite auf Basis ALLER Zeilen ────────────────────────
        widths = []
        for ti in (self.text_item1, self.text_item2, getattr(self, 'text_item3', None)):
            if ti and ti.toPlainText().strip():
                widths.append(ti.boundingRect().width())
        max_text_w = max(widths) if widths else 0
        new_w = max(self.min_width, max_text_w + 2 * self.padding_x)

        # ── 3) Szene informieren & Rect setzen ─────────────────────
        self.prepareGeometryChange()
        self.setRect(QRectF(0, 0, new_w, new_h))

        # ── 4) Texte neu positionieren ─────────────────────────────
        self.center_texts()
  
    def _position_texts(self):
        content = self._get_content_rect()
        half_h   = content.height() / 2

        # Texte messen (immer)
        r1 = self.text_item1.boundingRect()
        r2 = self.text_item2.boundingRect()
        r3_text = self.text_item3.toPlainText().strip()
        r3 = self.text_item3.boundingRect() if r3_text else None

        # Konstanten
        pad_y_top  = self.padding_y_top
        spacing12  = self.spacing12
        spacing23  = self.spacing23

        # ── Zweizeilen-Fall ───────────────────────────────────────────
        if not r3_text:
            # Text1 obere Hälfte zentrieren
            x1 = content.x() + (content.width() - r1.width()) / 2
            y1 = content.y() + (half_h - r1.height()) / 2
            self.text_item1.setPos(x1, y1)

            # Text2 untere Hälfte zentrieren
            x2 = content.x() + (content.width() - r2.width()) / 2
            y2 = content.y() + half_h + (half_h - r2.height()) / 2
            self.text_item2.setPos(x2, y2)
            return

        # ── Dreizeilen-Fall ────────────────────────────────────────────
        # Zeile 1: oberhalb
        x1 = content.x() + (content.width() - r1.width()) / 2
        y1 = content.y() + pad_y_top
        self.text_item1.setPos(x1, y1)

        # Gesamthöhe von Zeile2+23+3
        group_h = r2.height() + spacing23 + r3.height()
        # Start so, dass Gruppe zentriert in unterer Hälfte sitzt
        start_y = content.y() + half_h + (half_h - group_h) / 2

        # Zeile 2
        x2 = content.x() + (content.width() - r2.width()) / 2
        y2 = start_y
        self.text_item2.setPos(x2, y2)

        # Zeile 3 direkt darunter
        x3 = content.x() + (content.width() - r3.width()) / 2
        y3 = y2 + r2.height() + spacing23
        self.text_item3.setPos(x3, y3)
   
    def paint(self, painter, option, widget):
        # ── ganz oben: hole das Rechteck des Nodes ────────────────
        r = self.rect()

        # 1) Pfad für die Form erzeugen
        path = QPainterPath()
        if self.node_shape == "rect":
            path.addRect(r)
        elif self.node_shape == "ellipse":
            path.addEllipse(r)
        elif self.node_shape == "diamond":
            pts = [
                QPointF(r.x() + r.width()/2, r.y()),
                QPointF(r.x() + r.width(),    r.y() + r.height()/2),
                QPointF(r.x() + r.width()/2, r.y() + r.height()),
                QPointF(r.x(),                r.y() + r.height()/2),
            ]
            path.addPolygon(QPolygonF(pts))
        elif self.node_shape == "triangle":
            pts = [
                QPointF(r.x() + r.width()/2, r.y()),
                QPointF(r.x() + r.width(),    r.y() + r.height()),
                QPointF(r.x(),                r.y() + r.height()),
            ]
            path.addPolygon(QPolygonF(pts))
        elif self.node_shape == "hexagon":
            w, h, x, y = r.width(), r.height(), r.x(), r.y()
            pts = [
                QPointF(x + w*0.25, y),
                QPointF(x + w*0.75, y),
                QPointF(x + w,      y + h/2),
                QPointF(x + w*0.75, y + h),
                QPointF(x + w*0.25, y + h),
                QPointF(x,          y + h/2),
            ]
            path.addPolygon(QPolygonF(pts))

        # 2) obere Hälfte füllen
        painter.save()
        painter.setBrush(QBrush(self.color1))
        painter.setPen(self.pen())
        painter.setClipRect(QRectF(r.x(), r.y(), r.width(), r.height()/2))
        painter.drawPath(path)
        painter.restore()

        # 3) untere Hälfte füllen
        painter.save()
        painter.setBrush(QBrush(self.color2))
        painter.setPen(self.pen())
        painter.setClipRect(QRectF(r.x(),
                                  r.y() + r.height()/2,
                                  r.width(),
                                  r.height()/2))
        painter.drawPath(path)
        painter.restore()

        # 4) Outline zeichnen
        painter.setPen(self.pen())
        painter.drawPath(path)

        # 5) Texte layouten
        self._update_text_colors()

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
            # Ober­e Hälfte färben
            col1 = QColorDialog.getColor(
                self.color1,
                None,
                "Farbe obere Hälfte wählen"
            )
            if col1.isValid():
                # Untere Hälfte färben
                col2 = QColorDialog.getColor(
                    self.color2,
                    None,
                    "Farbe untere Hälfte wählen"
                )
                if not col2.isValid():
                    col2 = col1
                self.color1, self.color2 = col1, col2

                # Hier den korrekten Aufruf:
                self._update_text_colors()
                self.update()
                if hasattr(scene, 'parent'):
                    scene.parent.update_table()
            
        elif action == change_shape and scene:
            # 1) Liste der Anzeigenamen
            names = ["Rechteck", "Ellipse", "Raute", "Dreieck", "Hexagon"]
            # 2) Aktuellen Index ermitteln
            current = {
                "rect":     "Rechteck",
                "ellipse":  "Ellipse",
                "diamond":  "Raute",
                "triangle": "Dreieck",
                "hexagon":  "Hexagon"
            }[self.node_shape]
            idx = names.index(current)

            # 3) Dialog öffnen
            choice, ok = QInputDialog.getItem(
                None,
                "Form ändern",
                "Form:",
                names,
                idx,
                False
            )
            if not ok:
                return

            # 4) Mapping auf internen Wert
            mapping = {
                "Rechteck": "rect",
                "Ellipse":  "ellipse",
                "Raute":    "diamond",
                "Dreieck":  "triangle",
                "Hexagon":  "hexagon"
            }
            self.node_shape = mapping[choice]
            
            self.prepareGeometryChange()
            self.adjustSize()
            self._position_texts()

            # 5) Größe/Muster neu anpassen und neu zeichnen
            self._adjust_size()
            # (falls du _position_texts nutzt)
            self._position_texts()
            self.update()  # QGraphicsItem neu malen

            # 6) Tabelle aktualisieren
            if hasattr(scene, 'parent'):
                scene.parent.update_table()
        elif action == connect_node and scene:
            scene.connecting = True
            scene.connect_source = self
        elif action == edit_text and scene:
            # 1) Protokoll bearbeiten
            text1, ok1 = QInputDialog.getText(
                None,
                "Protokoll bearbeiten",
                "Protokoll:",
                text=self.text1
            )
            if not ok1:
                return

            # 2) Adresse bearbeiten
            text2, ok2 = QInputDialog.getText(
                None,
                "Adresse bearbeiten",
                "Adresse:",
                text=self.text2
            )
            if not ok2:
                return

            # 3) Bauteilart bearbeiten
            text3, ok3 = QInputDialog.getText(
                None,
                "Bauteilart bearbeiten",
                "Bauteilart:",
                text=getattr(self, 'text3', "")
            )
            if not ok3:
                return

            # Nur wenn alle drei OK:
            self.text1 = text1
            self.text2 = text2
            self.text3 = text3

            self.text_item1.setPlainText(text1)
            self.text_item2.setPlainText(text2)
            self.text_item3.setPlainText(text3)
            
            self.prepareGeometryChange()
            self.adjustSize()
            self._position_texts()

            self._update_layout()
            if scene.parent:
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
        else:
            super().contextMenuEvent(event)
        
        
    def _update_text_colors(self):
        """Zeile 1 kontrastiert mit color1, Zeile 2+3 mit color2."""
        fg1 = Qt.white if is_color_dark(self.color1) else Qt.black
        fg2 = Qt.white if is_color_dark(self.color2) else Qt.black
        self.text_item1.setDefaultTextColor(fg1)
        self.text_item2.setDefaultTextColor(fg2)
        self.text_item3.setDefaultTextColor(fg2)

    def itemChange(self, change, value):
        # Vor jeder Positionsänderung snappen wir auf das Raster
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            gridSize = 40  # muss exakt mit Deinem Gitter-Abstand übereinstimmen
            # value ist schon ein QPointF
            newPos = value
            x = round(newPos.x() / gridSize) * gridSize
            y = round(newPos.y() / gridSize) * gridSize
            return QPointF(x, y)
        return super().itemChange(change, value)
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Dynamic grid from the first view showing this scene
        views = self.scene().views()
        if not views:
            return
        g = views[0].grid_size
        p = self.pos()
        x = round(p.x() / g) * g
        y = round(p.y() / g) * g
        self.setPos(QPointF(x, y))
        
    def _get_content_rect(self) -> QRectF:
        """
        Liefert das Rechteck, in dem der Text stehen darf,
        je nachdem, welche Form self.node_shape hat.
        """
        r = self.rect()
        w, h = r.width(), r.height()
        x, y = r.x(), r.y()

        inset = 0.0
        if self.node_shape == "diamond":
            # Raute: Breite in der Mitte ist w/2
            inset = w * 0.25
        elif self.node_shape == "triangle":
            # Gleichschenkliges Dreieck: Basisbreite w,
            # obere Spitze nicht relevant, wir nutzen z.B. w*0.1 inset
            inset = w * 0.1
        elif self.node_shape == "hexagon":
            # Hexagon: die schmaleren Seitenbereiche je w*0.25
            inset = w * 0.25
        else:
            # Rechteck & Ellipse: kein Inset
            inset = 0

        # Text darf dann in x+inset .. x+w-inset stehen,
        # und in y .. y+h (oder unten je nach Zeile)
        return QRectF(x + inset, y, w - 2*inset, h)
        
    def center_texts(self):
        """
        Zeile 1 mittig in der oberen Hälfte, 
        Zeile 2 (und optional Zeile 3) in der unteren Hälfte.
        """
        r = self.rect()
        half_h = r.height() / 2

        # Zeilen sammeln
        lines = [self.text_item1]
        if self.text_item2.toPlainText().strip():
            lines.append(self.text_item2)
        if hasattr(self, 'text_item3') and self.text_item3.toPlainText().strip():
            lines.append(self.text_item3)

        # 1. Zeile oben mittig
        br1 = self.text_item1.boundingRect()
        x1  = r.x() + (r.width() - br1.width()) / 2
        y1  = r.y() + (half_h - br1.height()) / 2
        self.text_item1.setPos(x1, y1)

        # Wenn nur zwei Zeilen, setze Zeile2 mittig in unterer Hälfte
        if len(lines) == 2:
            br2 = lines[1].boundingRect()
            x2  = r.x() + (r.width() - br2.width()) / 2
            y2  = r.y() + half_h + (half_h - br2.height()) / 2
            lines[1].setPos(x2, y2)
            return

        # Bei drei Zeilen: Zeile2/3 gleichmäßig in untere Hälfte verteilen
        if len(lines) == 3:
            # Zeile2
            br2 = lines[1].boundingRect()
            x2  = r.x() + (r.width() - br2.width()) / 2
            # Setze Zeile2 auf 1/3 der unteren Hälfte
            y2  = r.y() + half_h + (half_h * 1/3) - (br2.height() / 2)
            lines[1].setPos(x2, y2)

            # Zeile3
            br3 = lines[2].boundingRect()
            x3  = r.x() + (r.width() - br3.width()) / 2
            # Setze Zeile3 auf 2/3 der unteren Hälfte
            y3  = r.y() + half_h + (half_h * 2/3) - (br3.height() / 2)
            lines[2].setPos(x3, y3)
            return
        
class EdgeItem(QGraphicsLineItem):   
    def __init__(self, source, dest,
                 color1=Qt.red, 
                 color2=Qt.green,
                 dash_pattern=(8.0, 4.0),
                 label_text=""):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setFlag(QGraphicsLineItem.ItemIsSelectable, True)
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
        self.setZValue(0)
        self.text_item.setZValue(1)
    def paint(self, painter, option, widget=None):
        # 1) Position der Endpunkte updaten
        self.update_position()

        # 2) Basis-Linie und Länge
        line = self.line()
        length = line.length()
        if length <= 0:
            return

        # 3) Dash-Pattern entpacken
        dash, gap = self.dash_pattern

        # 4) Abwechselnd farbige Segmente zeichnen
        pos = 0.0
        toggle = False
        while pos < length:
            start_pt = line.pointAt(pos / length)
            end_pos = min(pos + dash, length)
            end_pt = line.pointAt(end_pos / length)

            pen = QPen(
                self.color1 if not toggle else self.color2,
                self.pen_width
            )
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(QLineF(start_pt, end_pt))

            pos += dash + gap
            toggle = not toggle

        # 5) Label-Text (bereits als QGraphicsTextItem child angelegt)
        #    Position wurde in update_position() festgelegt,
        #    hier reicht es, ihn zu zeichnen:
        self.text_item.paint(painter, option, widget)

    def update_position(self):
        rect1 = self.source.sceneBoundingRect()
        rect2 = self.dest.sceneBoundingRect()
        center1 = rect1.center()
        center2 = rect2.center()
        base_line = QLineF(center1, center2)

        def find_border_point(rect, line):
            edges = [
                QLineF(rect.topLeft(),     rect.topRight()),
                QLineF(rect.topRight(),    rect.bottomRight()),
                QLineF(rect.bottomRight(), rect.bottomLeft()),
                QLineF(rect.bottomLeft(),  rect.topLeft()),
            ]
            for edge in edges:
                pt = QPointF()
                inter_type = line.intersect(edge, pt)
                if inter_type == QLineF.BoundedIntersection:
                    return pt
            return rect.center()

        p1 = find_border_point(rect1, base_line)
        # Für das Ziel die Linie umdrehen
        rev_line = QLineF(center2, center1)
        p2 = find_border_point(rect2, rev_line)

        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

        # Label mittig positionieren
        mid = QLineF(p1, p2).pointAt(0.5)
        rect_text = self.text_item.boundingRect()
        self.text_item.setPos(
            mid.x() - rect_text.width()/2,
            mid.y() - 10 - rect_text.height()/2
        )

        def paint(self, painter, option, widget):
            print("Painting edge:", self.source.text1, "→", self.dest.text1)
            self.update_position()
            line = self.line()
            # 1) Pfad für die gewünschte Form erzeugen
            path = QPainterPath()
            if self.shape == "rect":
                path.addRect(r)
            elif self.shape == "ellipse":
                path.addEllipse(r)
            elif self.shape == "diamond":
                pts = [
                    QPointF(r.x() + r.width()/2, r.y()),
                    QPointF(r.x() + r.width(),    r.y() + r.height()/2),
                    QPointF(r.x() + r.width()/2, r.y() + r.height()),
                    QPointF(r.x(),                r.y() + r.height()/2),
                ]
                path.addPolygon(QPolygonF(pts))
            elif self.shape == "triangle":
                pts = [
                    QPointF(r.x() + r.width()/2, r.y()),
                    QPointF(r.x() + r.width(),    r.y() + r.height()),
                    QPointF(r.x(),                r.y() + r.height()),
                ]
                path.addPolygon(QPolygonF(pts))
            elif self.shape == "hexagon":
                w, h, x, y = r.width(), r.height(), r.x(), r.y()
                pts = [
                    QPointF(x + w*0.25, y),
                    QPointF(x + w*0.75, y),
                    QPointF(x + w,      y + h/2),
                    QPointF(x + w*0.75, y + h),
                    QPointF(x + w*0.25, y + h),
                    QPointF(x,          y + h/2),
                ]
                path.addPolygon(QPolygonF(pts))

            # 2) obere Hälfte füllen
            painter.save()
            painter.setBrush(QBrush(self.color1))
            painter.setPen(self.pen())
            painter.setClipRect(QRectF(r.x(), r.y(), r.width(), r.height()/2))
            painter.drawPath(path)
            painter.restore()

            # 3) untere Hälfte füllen
            painter.save()
            painter.setBrush(QBrush(self.color2))
            painter.setPen(self.pen())
            painter.setClipRect(QRectF(r.x(),
                                      r.y() + r.height()/2,
                                      r.width(),
                                      r.height()/2))
            painter.drawPath(path)
            painter.restore()

            # 4) Outline zeichnen
            painter.setPen(self.pen())
            painter.drawPath(path)

            # 5) Texte korrekt positionieren
            self._position_texts()

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
    
    def shape(self):
        """Erweitert die „treffbare“ Fläche auf ±5px um die Linie."""
        # 1) Erzeuge den Basis-Pfad der Linie
        path = QPainterPath()
        line = self.line()
        path.moveTo(line.p1())
        path.lineTo(line.p2())

        # 2) Erzeuge einen Stroker mit breiterem Bereich
        stroker = QPainterPathStroker()
        stroker.setWidth(self.pen_width + 10)  # +10px = ±5px um die Linie
        # 3) Gib die „Hit“-Form zurück
        return stroker.createStroke(path)
        
    def hoverEnterEvent(self, event):
        self.pen_width += 1
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.pen_width -= 1
        self.update()
        super().hoverLeaveEvent(event)

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

        mw = self.parent  # dein MainWindow
        if mw and mw.connect_mode and event.button() == Qt.LeftButton and isinstance(item, NodeItem):
            if mw.connect_source is None:
                mw.connect_source = item
                item.setPen(QPen(Qt.blue, 2))
            else:
                src  = mw.connect_source
                dest = item

                # Wahl: vordefiniertes Template oder custom_params
                if mw.custom_connect:
                    col1, col2, dash_pattern, label = mw.custom_params
                else:
                    tpl = mw.connect_template
                    col1, col2     = tpl.color1, tpl.color2
                    dash_pattern   = tpl.dash_pattern
                    label          = tpl.default_label

                # Quelle zurücksetzen
                src.setPen(QPen(Qt.black, 1))

                # Edge anlegen
                edge = EdgeItem(src, dest,
                                color1=col1,
                                color2=col2,
                                dash_pattern=dash_pattern,
                                label_text=label)
                self.addItem(edge)
                self.edges.append(edge)
                edge.update_position()
                mw.update_table()

                # Quelle zurücksetzen, Modus bleibt on
                mw.connect_source = None
            return

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
                result = self.ask_custom_style_and_color()
                if result is None:
                    self.connecting = False
                    self.connect_source = None
                    return
                line_style, color1, color2, dash_pattern, label = result
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
            print("Edge created:", edge, "– total edges in scene:", len(self.edges))
            self.edges.append(edge)

            # Verbindung fertig, Tabelle updaten
            self.connecting     = False
            self.connect_source = None
            if self.parent:
                self.parent.update_table()

        else:
            super().mousePressEvent(event)
    
    def ask_custom_style_and_color(self):
        # 1) Linien-Stil abfragen
        styles = {
            "Durchgezogen": Qt.SolidLine,
            "Gestrichelt":   Qt.DashLine,
            "Gepunktet":     Qt.DotLine,
            "Strich-Punkt":  Qt.DashDotLine,
            "Strich-Punkt-Punkt": Qt.DashDotDotLine
        }
        style_names = list(styles.keys())
        choice, ok = QInputDialog.getItem(
            None,
            "Linien-Stil",
            "Stil wählen:",
            style_names,
            0,
            False
        )
        if not ok:
            return None, None, None, ""
        line_style = styles[choice]

        # 2) Dash-Pattern abfragen
        dash, ok1 = QInputDialog.getDouble(None, "Strichlänge", "Länge Strich (px):", 8.0, 0.0, 100.0, 1)
        if not ok1:
            dash = 8.0
        gap, ok2  = QInputDialog.getDouble(None, "Lückenlänge", "Länge Lücke (px):", 4.0, 0.0, 100.0, 1)
        if not ok2:
            gap = 4.0
        dash_pattern = (dash, gap)

        # 3) Farben abfragen
        col1 = QColorDialog.getColor(Qt.black, None, "Farbe 1 wählen")
        color1 = col1 if col1.isValid() else QColor(Qt.black)
        col2 = QColorDialog.getColor(color1,  None, "Farbe 2 wählen")
        color2 = col2 if col2.isValid() else color1

        # 4) Label-Text abfragen
        label, ok3 = QInputDialog.getText(None, "Verbindungs-Label", "Text eingeben:", text="")
        if not ok3:
            label = ""

        return line_style, color1, color2, dash_pattern, label


class Template:
    def __init__(self, name, shape, color1, color2, width, height, text1, text2, text3=""):
        self.name = name
        self.shape = shape
        self.color1 = color1
        self.color2 = color2
        self.width = width
        self.height = height
        self.text1 = text1
        self.text2 = text2
        self.text3 = text3
DEFAULT_TEMPLATES = [
    Template("KNX", "rect", "#00aa00", "#00aa00", 100, 80, "KNX", ""),
    Template("DALI", "rect", "#b0b0b0", "#000000", 100, 80, "DALI", ""),
    Template("Loxone", "rect", "#00ff00", "#00ff00", 100, 80, "Loxone", ""),
    Template("Loxone Tree", "rect", "#00ff00", "#ffffff", 100, 80, "Loxone Tree", ""),
    Template("Loxone Link", "rect", "#0000ff", "#ffffff", 100, 80, "Loxone Link", ""),
    Template("Loxone Air", "rect", "#00ff00", "#000000", 100, 80, "Loxone Air", ""),
    Template("IP Symcon", "rect", "#00ffff", "#00ffff", 100, 80, "IP-Symcon", ""),
    Template("Netzwerk Gerät", "rect", "#00aaff", "#00aaff", 100, 80, "Netzwerk Gerät", ""),
    Template("EE-Bus", "rect", "#0000ff", "#0000ff", 100, 80, "EE-Bus", ""),
    Template("Modbus 485", "rect", "#ffaa00", "#ffaa00", 100, 80, "Modbus 485", ""),
    Template("Modbus 232", "rect", "#ffaa00", "#ffff00", 100, 80, "Modbus 232", ""),
    Template("M-Bus", "rect", "#ffff00", "#aa007f", 100, 80, "M-Bus", "")
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
        self.show_grid = True
        self.setStyleSheet("background: transparent;")
        self.viewport().setAttribute(Qt.WA_TranslucentBackground, True)

        # Zoom-Logik etc. bleibt unverändert
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.grid_size = 40  # Start-Wert


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
    def drawBackground(self, painter, rect):
        g = self.grid_size
        pen = QPen(QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)

        left   = int(rect.left()   // g) * g
        top    = int(rect.top()    // g) * g
        right  = int(rect.right()  // g + 1) * g
        bottom = int(rect.bottom() // g + 1) * g

        # Vertikale Linien
        x = left
        while x <= right:
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += g

        # Horizontale Linien
        y = top
        while y <= bottom:
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += g
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
       
        self.templates = []
        self.load_templates()
        self.init_ui()
        self.connect_mode = False
        self.connect_source = None
        self.connect_template = None
        self.custom_connect   = False
        self.custom_params    = None
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
        
        self.action_toggle_grid = QAction("Gitter", self, checkable=True)
        self.action_toggle_grid.setChecked(True)
        self.action_toggle_grid.setToolTip("Gitter Ein/Aus")
        self.action_toggle_grid.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.action_toggle_grid)
        
        self.action_grid_up = QAction("Gitter +", self)
        self.action_grid_up.setToolTip("Rastergröße vergrößern")
        self.action_grid_up.triggered.connect(self.on_grid_up)
        toolbar.addAction(self.action_grid_up)
        
        self.action_grid_down = QAction("Gitter –", self)
        self.action_grid_down.setToolTip("Rastergröße verkleinern")
        self.action_grid_down.triggered.connect(self.on_grid_down)
        toolbar.addAction(self.action_grid_down)
        
        self.action_connect_mode = QAction("Verbindungsmodus", self, checkable=True)
        self.action_connect_mode.setToolTip("Klicke zum Starten: Wähle zuerst einen Verbindungstyp, dann zwei Nodes")
        self.action_connect_mode.triggered.connect(self.toggle_connect_mode)
        toolbar.addAction(self.action_connect_mode)

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
        self.le_company     = QLineEdit()
        self.le_operator    = QLineEdit()
        self.de_created_date = QDateEdit(QDate.currentDate())
        self.de_created_date.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Kundennummer:",    self.le_customer)
        form.addRow("Anschrift:",       self.le_address)
        form.addRow("Projekt-Nr.:",     self.le_project_no)
        form.addRow("Auftrags-Nr.:",    self.le_order_no)
        form.addRow("Firma:",           self.le_company)
        form.addRow("Bearbeiter:",      self.le_operator)
        form.addRow("Erstellungsdatum:", self.de_created_date)
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
        node.prepareGeometryChange()
        node.adjustSize()
        node.center_texts()
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
            node.prepareGeometryChange()
            node.adjustSize()
            node.center_texts()
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
                "order_no":   self.le_order_no.text(),
                "company":      self.le_company.text(),
                "operator":     self.le_operator.text(),
                "created_date": self.de_created_date.date().toString("yyyy-MM-dd")
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
        self.le_company.     setText(meta.get("company", ""))
        self.le_operator.    setText(meta.get("operator", ""))
        date_str = meta.get("created_date", QDate.currentDate().toString("yyyy-MM-dd"))
        self.de_created_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
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
            ("Auftrags-Nr.", self.le_order_no.text()),
            ("Firma",           self.le_company.text()),
            ("Bearbeiter",      self.le_operator.text()),
            ("Erstellungsdatum", self.de_created_date.date().toString("dd.MM.yyyy"))
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
            ("Auftrags-Nr.", self.le_order_no.text()),
            ("Firma",           self.le_company.text()),
            ("Bearbeiter",      self.le_operator.text()),
            ("Erstellungsdatum", self.de_created_date.date().toString("dd.MM.yyyy"))
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

        col1 = QColorDialog.getColor(
        QColor("lightgray"),
        None,
        "Farbe obere Hälfte wählen"      # Titel des Dialogs
        )
        color1 = col1.name() if col1.isValid() else "lightgray"

        # Farbe für untere Hälfte wählen
        col2 = QColorDialog.getColor(
            QColor("white"),
            None,
            "Farbe untere Hälfte wählen"     # und hier deutlich machen, wofür
        )
        color2 = col2.name() if col2.isValid() else "white"

        width, ok = QInputDialog.getInt(self, "Breite eingeben", "Breite:", 100, 10, 1000, 1)
        if not ok:
            return
        height, ok = QInputDialog.getInt(self, "Höhe eingeben", "Höhe:", 80, 10, 1000, 1)
        if not ok:
            return
        text1, ok1 = QInputDialog.getText(self, "Text eingeben", "Protokoll:")
        if not ok1:
            return
        text2, ok2 = QInputDialog.getText(self, "Text eingeben", "Adresse:")
        if not ok2:
            return
        text3, ok3 = QInputDialog.getText(self, "Bauteilart eingeben", "Bauteilart:", text="")
        if not ok3:
            text3 = ""

        tpl = Template(
            name=name,
            shape=shape,
            color1=color1,
            color2=color2,
            width=width,
            height=height,
            text1=text1,
            text2=text2,
            text3=text3
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
                text2=tpl_data.get("text2", ""),
                text3=tpl_data.get("text3", "")
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
                "text2": tpl.text2,
                "text3": tpl.text3
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
            self.table.setItem(row, 2, QTableWidgetItem(node.node_shape))
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
            
    def toggle_grid(self, checked: bool):
        # schalte das Gitter in der View ein/aus
        self.view.show_grid = checked
        # zwinge Neuzeichnen
        self.view.viewport().update()
        
    def on_grid_up(self):
        """Raster um 10px vergrößern, maximal 200px."""
        v = self.view
        v.grid_size = min(200, v.grid_size + 10)
        v.viewport().update()

    def on_grid_down(self):
        """Raster um 10px verkleinern, minimal 10px."""
        v = self.view
        v.grid_size = max(10, v.grid_size - 10)
        v.viewport().update()
     
    def toggle_connect_mode(self, checked: bool):
        if checked:
            names = [tpl.name for tpl in EDGE_TEMPLATES] + ["Benutzerdefiniert"]
            choice, ok = QInputDialog.getItem(
                self, "Verbindungstyp wählen", "Typ:", names, 0, False
            )
            if not ok:
                self.action_connect_mode.setChecked(False)
                return

            if choice == "Benutzerdefiniert":
                # Einmalig benutzerdefiniert abfragen:
                params = self.ask_custom_connection()
                if params is None:
                    # Abgebrochen: Modus wieder aus
                    self.action_connect_mode.setChecked(False)
                    return
                self.custom_connect  = True
                self.custom_params   = params
                self.connect_template = None
            else:
                self.custom_connect  = False
                self.custom_params   = None
                self.connect_template = next(t for t in EDGE_TEMPLATES if t.name == choice)

            self.connect_source = None
            self.view.setCursor(Qt.CrossCursor)
            self.connect_mode   = True

        else:
            # Modus ausschalten
            self.connect_mode     = False
            self.custom_connect   = False
            self.connect_template = None
            self.custom_params    = None
            self.connect_source   = None
            self.view.setCursor(Qt.ArrowCursor)
     
    def ask_custom_connection(self):
        # Farbe 1
        col1 = QColorDialog.getColor(
            QColor(Qt.red), self, "Farbe 1 (erstes Segment) wählen"
        )
        if not col1.isValid(): return None

        # Farbe 2
        col2 = QColorDialog.getColor(
            QColor(Qt.green), self, "Farbe 2 (zweites Segment) wählen"
        )
        if not col2.isValid():
            col2 = col1

        # Dash-Pattern
        dash, ok1 = QInputDialog.getInt(
            self, "Strichlänge", "Länge des Strichs (px):", 8, 1, 200, 1
        )
        if not ok1: return None
        gap, ok2 = QInputDialog.getInt(
            self, "Lückenlänge", "Länge der Lücke (px):", 4, 0, 200, 1
        )
        if not ok2: return None

        # Label-Text
        label, ok3 = QInputDialog.getText(
            self, "Verbindungs-Label", "Text für Verbindung:", text=""
        )
        if not ok3:
            label = ""

        return (col1, col2, (dash, gap), label)


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
