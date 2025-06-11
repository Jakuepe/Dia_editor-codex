import json
import os
from PyQt5.QtWidgets import (
    QMainWindow, QToolBar, QAction, QListWidget, QListWidgetItem,
    QDockWidget, QMessageBox, QMenu, QTableWidget, QTableWidgetItem,
    QComboBox, QShortcut, QLineEdit, QFormLayout, QWidget,
    QFileDialog, QColorDialog, QInputDialog
)
from PyQt5.QtGui import QBrush, QColor, QPainter, QPixmap, QIcon, QPainterPath, QPen, QKeySequence
from PyQt5.QtCore import Qt, QRectF, QRect

from models import (
    NodeItem, EdgeItem, Template, EdgeTemplate, DEFAULT_TEMPLATES,
    TEMPLATES_FILE, is_color_dark
)
from scene import DiagramScene, DiagramView


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
        self.cb_page.addItems(["A4 Hoch", "A4 Quer", "A3 Hoch", "A3 Quer"])
        toolbar.addSeparator()
        toolbar.addWidget(self.cb_page)

        zoom_in_sc = QShortcut(QKeySequence.ZoomIn, self)
        zoom_out_sc = QShortcut(QKeySequence.ZoomOut, self)
        zoom_in_sc.activated.connect(self.view.zoom_in)
        zoom_out_sc.activated.connect(self.view.zoom_out)

        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_page)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.load_diagram)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_diagram)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, activated=self.add_node)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=lambda: setattr(self.scene, 'connecting', True))
        QShortcut(QKeySequence("Ctrl+I"), self, activated=self.export_image)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.export_pdf)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.export_table)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self.create_template)

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

        self.table = QTableWidget(0, 4)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        self.table.setHorizontalHeaderLabels(["Protokoll", "Adresse", "Form/Verbindung", "Standort/Position"])
        self.table_dock = QDockWidget("Tabelle", self)
        self.table_dock.setWidget(self.table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.table_dock)

        cust_widget = QWidget()
        form = QFormLayout(cust_widget)
        self.le_customer = QLineEdit()
        self.le_address = QLineEdit()
        self.le_project_no = QLineEdit()
        self.le_order_no = QLineEdit()
        form.addRow("Kundennummer:", self.le_customer)
        form.addRow("Anschrift:", self.le_address)
        form.addRow("Projekt-Nr.:", self.le_project_no)
        form.addRow("Auftrags-Nr.:", self.le_order_no)
        cust_widget.setLayout(form)

        self.cust_dock = QDockWidget("Kundendaten", self)
        self.cust_dock.setWidget(cust_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.cust_dock)

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

    # ---- actions ---------------------------------------------------------
    def delete_selected(self):
        for item in list(self.scene.selectedItems()):
            if isinstance(item, NodeItem):
                for edge in list(self.scene.edges):
                    if edge.source is item or edge.dest is item:
                        self.scene.removeItem(edge)
                        self.scene.edges.remove(edge)
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
            pts = [QPointF(8, 0), QPointF(24, 0), QPointF(32, 16), QPointF(24, 32), QPointF(8, 32), QPointF(0, 16)]
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
        standort, ok = QInputDialog.getText(self, "Standort eingeben", "Standort:")
        if not ok:
            standort = ""
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
        save_btn = msg.addButton("Speichern", QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Verwerfen", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("Abbrechen", QMessageBox.RejectRole)
        msg.setDefaultButton(save_btn)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked == save_btn:
            if not self.save_diagram():
                return
        elif clicked == cancel_btn:
            return
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
                "customer": self.le_customer.text(),
                "address": self.le_address.text(),
                "project_no": self.le_project_no.text(),
                "order_no": self.le_order_no.text()
            },
            "nodes": [],
            "edges": []
        }
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
            style = edge.pen().style()
            label = edge.text_item.toPlainText()
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
        self.le_customer.setText(meta.get("customer", ""))
        self.le_address.setText(meta.get("address", ""))
        self.le_project_no.setText(meta.get("project_no", ""))
        self.le_order_no.setText(meta.get("order_no", ""))
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
        path, _ = QFileDialog.getSaveFileName(self, "Als Bild exportieren", "", "PNG (*.png);;JPEG (*.jpg)")
        if not path:
            return
        rect = self.scene.itemsBoundingRect()
        if rect.isEmpty():
            QMessageBox.warning(self, "Exportieren", "Keine Elemente in der Szene zum Exportieren.")
            return
        dpi = 300
        mm2px = lambda mm: int(mm * 300 / 25.4)
        choice = self.cb_page.currentText()
        if "A4" in choice:
            w_mm, h_mm = 210, 297
        else:
            w_mm, h_mm = 297, 420
        if "Quer" in choice:
            w_mm, h_mm = h_mm, w_mm
        img_w = mm2px(w_mm)
        img_h = mm2px(h_mm)
        margin = mm2px(10)
        image = QPixmap(img_w, img_h)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        data = [
            ("Kundennummer", self.le_customer.text()),
            ("Anschrift", self.le_address.text()),
            ("Projekt-Nr.", self.le_project_no.text()),
            ("Auftrags-Nr.", self.le_order_no.text())
        ]
        row_h_px = fm.height() + 8
        max_label = max(label for label, _ in data)
        label_w = fm.horizontalAdvance(max_label)
        mm2px = lambda mm: int(mm * 300 / 25.4)
        padding_px = mm2px(5)
        col1_px = label_w + padding_px
        max_value = max(val for _, val in data)
        val_w = fm.horizontalAdvance(max_value)
        col2_px = val_w + padding_px
        table_w_px = col1_px + col2_px
        table_h_px = row_h_px * len(data)
        table_x = margin
        table_y = margin
        painter.drawRect(table_x, table_y, table_w_px, table_h_px)
        for i in range(1, len(data)):
            y = table_y + row_h_px * i
            painter.drawLine(table_x, y, table_x + table_w_px, y)
        painter.drawLine(table_x + col1_px, table_y, table_x + col1_px, table_y + table_h_px)
        for i, (lbl, val) in enumerate(data):
            cell_y = table_y + row_h_px * i
            rect_lbl = QRect(table_x + 2, cell_y + 2, col1_px - 4, row_h_px - 4)
            painter.drawText(rect_lbl, Qt.AlignLeft | Qt.AlignVCenter, lbl)
            rect_val = QRect(table_x + col1_px + 2, cell_y + 2, col2_px - 4, row_h_px - 4)
            painter.drawText(rect_val, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, val)
        painter.save()
        painter.translate(margin, margin + table_h_px + mm2px(5))
        avail_w = img_w - 2 * margin
        avail_h = img_h - margin - table_h_px - mm2px(5)
        scale = min(avail_w / rect.width(), avail_h / rect.height())
        painter.scale(scale, scale)
        self.scene.render(painter, QRectF(0, 0, rect.width(), rect.height()), rect)
        painter.restore()
        painter.end()
        image.save(path)
        QMessageBox.information(self, "Exportiert", "Bild wurde exportiert.")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Als PDF exportieren", "", "PDF-Datei (*.pdf)")
        if not path:
            return
        from PyQt5.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        choice = self.cb_page.currentText()
        if "A4" in choice:
            printer.setPaperSize(QPrinter.A4)
        else:
            printer.setPaperSize(QPrinter.A3)
        printer.setOrientation(QPrinter.Landscape if "Quer" in choice else QPrinter.Portrait)
        scene_rect = self.scene.itemsBoundingRect()
        if scene_rect.isEmpty():
            QMessageBox.warning(self, "Exportieren", "Keine Elemente in der Szene vorhanden.")
            return
        page_rect = printer.pageRect()
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Exportieren", "Kann PDF-Renderer nicht starten.")
            return
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        data = [
            ("Kundennummer", self.le_customer.text()),
            ("Anschrift", self.le_address.text()),
            ("Projekt-Nr.", self.le_project_no.text()),
            ("Auftrags-Nr.", self.le_order_no.text())
        ]
        fm = painter.fontMetrics()
        row_h = fm.height() + 8
        labels = [label for label, _ in data]
        max_label = max(labels, key=lambda lbl: fm.horizontalAdvance(lbl))
        label_w = fm.horizontalAdvance(max_label)
        avg_char = fm.horizontalAdvance("M")
        padding = avg_char * 6
        col1_w = max(label_w + padding, 120)
        max_value = max(value for _, value in data)
        value_w = fm.horizontalAdvance(max_value)
        col2_w = value_w + 20
        table_w = col1_w + col2_w
        table_x = page_rect.x() + 10
        table_y = page_rect.y() + 10
        table_h = row_h * len(data)
        painter.drawRect(table_x, table_y, table_w, table_h)
        for i in range(len(data)):
            y = table_y + row_h * (i + 1)
            painter.drawLine(table_x, y, table_x + table_w, y)
        painter.drawLine(table_x + col1_w, table_y, table_x + col1_w, table_y + table_h)
        for i, (label, value) in enumerate(data):
            cell_y = table_y + row_h * i
            r_lbl = QRectF(table_x + 2, cell_y + 2, col1_w - 4, row_h - 4)
            painter.drawText(r_lbl, Qt.AlignLeft | Qt.AlignVCenter, label)
            r_val = QRectF(table_x + col1_w + 2, cell_y + 2, col2_w - 4, row_h - 4)
            painter.drawText(r_val, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, value)
        header_h = table_h + 20
        footer_h = 36
        avail_w = page_rect.width()
        avail_h = page_rect.height() - header_h - footer_h
        scale = min(avail_w / scene_rect.width(), avail_h / scene_rect.height())
        painter.save()
        painter.translate(page_rect.x(), page_rect.y() + header_h)
        painter.scale(scale, scale)
        self.scene.render(painter, QRectF(0, 0, scene_rect.width(), scene_rect.height()), scene_rect)
        painter.restore()
        painter.drawText(page_rect.x() + 10, page_rect.y() + page_rect.height() - 5, f"{self.le_customer.text()} | {self.le_address.text()} | {self.le_project_no.text()} | {self.le_order_no.text()}")
        painter.end()
        QMessageBox.information(self, "Exportiert", "PDF wurde exportiert.")

    def export_table(self):
        path, _ = QFileDialog.getSaveFileName(self, "Tabelle exportieren", "", "CSV-Datei (*.csv)")
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            f.write("Kundennummer,Anschrift,Projekt-Nr.,Auftrags-Nr.\n")
            f.write(f"{self.le_customer.text()},{self.le_address.text()},{self.le_project_no.text()},{self.le_order_no.text()}\n\n")
            rows = self.table.rowCount()
            cols = self.table.columnCount()
            for r in range(rows):
                vals = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(cols)]
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
        mapping = {"Rechteck": "rect", "Ellipse": "ellipse", "Raute": "diamond", "Dreieck": "triangle", "Hexagon": "hexagon"}
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
        tpl = Template(name=name, shape=shape, color1=color1, color2=color2, width=width, height=height, text1=text1, text2=text2)
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
        self.save_templates()
        self.refresh_template_list()

    def load_templates(self):
        self.templates = DEFAULT_TEMPLATES.copy()
        if not os.path.exists(TEMPLATES_FILE):
            return
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = {tpl.name for tpl in self.templates}
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
        for node in self.scene.nodes:
            self.table.setItem(row, 0, QTableWidgetItem(node.text1))
            self.table.setItem(row, 1, QTableWidgetItem(node.text2))
            self.table.setItem(row, 2, QTableWidgetItem(node.shape))
            standort = getattr(node, 'standort', "")
            self.table.setItem(row, 3, QTableWidgetItem(standort))
            for col in (0, 1):
                item = self.table.item(row, col)
                if not item:
                    continue
                bg = node.color1 if col == 0 else node.color2
                item.setBackground(QBrush(bg))
                fg = Qt.white if is_color_dark(bg) else Qt.black
                item.setForeground(QBrush(fg))
            row += 1
        for edge in self.scene.edges:
            src = edge.source.text1
            dst = edge.dest.text1
            arrow = getattr(edge, 'arrow', '-')
            self.table.setItem(row, 0, QTableWidgetItem("Verbindung"))
            item = QTableWidgetItem(f"{src}{arrow}{dst}")
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
            self.table.setItem(row, 3, QTableWidgetItem(""))
            row += 1

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle("Beenden")
        msg.setText("Möchten Sie das aktuelle Diagramm speichern, bevor Sie beenden?")
        save_btn = msg.addButton("Speichern", QMessageBox.AcceptRole)
        discard_btn = msg.addButton("Verwerfen", QMessageBox.DestructiveRole)
        cancel_btn = msg.addButton("Abbrechen", QMessageBox.RejectRole)
        msg.setDefaultButton(save_btn)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked == save_btn:
            if self.save_diagram():
                event.accept()
            else:
                event.ignore()
        elif clicked == discard_btn:
            event.accept()
        else:
            event.ignore()

    def on_table_double_click(self, row: int, col: int):
        num_nodes = len(self.scene.nodes)
        if col != 1 or row < num_nodes:
            return
        edge = self.scene.edges[row - num_nodes]
        current = getattr(edge, 'arrow', '-')
        options = ["-", "→", "←", "↔"]
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0
        arrow, ok = QInputDialog.getItem(self, "Pfeilrichtung wählen", "Richtung:", options, idx, False)
        if not ok:
            return
        edge.arrow = arrow
        src = edge.source.text1
        dst = edge.dest.text1
        self.table.item(row, col).setText(f"{src} {arrow} {dst}")

    def refresh_template_list(self):
        seen = set()
        unique = []
        for tpl in self.templates:
            if tpl.name not in seen:
                seen.add(tpl.name)
                unique.append(tpl)
        self.templates = unique
        self.template_list.clear()
        for tpl in self.templates:
            item = self.create_template_item(tpl)
            self.template_list.addItem(item)
