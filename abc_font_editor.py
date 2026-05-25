import os
import struct
import json
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QLineEdit, QMessageBox, QComboBox, QSpinBox, QDialog, QDialogButtonBox,
    QSizePolicy, QTextEdit
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QRectF
from PIL import Image
import sys

class ABCFontEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ABC Font Editor")
        self.abc_path = None
        self.texture_path = None
        self.texture_size = (2048, 1024)
        self.offset_dec = 0
        self.zoom = 1.0
        self.glyphs = []
        self.original_data = b""
        self.dirty = False
        self.manual_offset = False  # Track if offset was set manually
        self.init_ui()

    def show_error(self, title, message):
        """Helper method to show error dialogs consistently"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setModal(True)
        msg_box.raise_()
        msg_box.activateWindow()
        msg_box.exec_()

    def show_warning(self, title, message):
        """Helper method to show warning dialogs consistently"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setModal(True)
        msg_box.raise_()
        msg_box.activateWindow()
        msg_box.exec_()

    def show_info(self, title, message):
        """Helper method to show info dialogs consistently"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setModal(True)
        msg_box.raise_()
        msg_box.activateWindow()
        msg_box.exec_()

    def init_ui(self):
        self.setStyleSheet("background-color: #202020; color: white;")
        layout = QVBoxLayout(self)

        # Combined offset display in one label
        self.offsets_label = QLabel("")
        self.offsets_label.setStyleSheet("color: #aaa;")
        self.offsets_label.setVisible(False)
        layout.addWidget(self.offsets_label)

        top_row = QHBoxLayout()

        # Offset input with classic spin buttons
        top_row.addWidget(QLabel("Offset (dec):"))
        self.offset_input = QLineEdit("0")
        self.offset_input.setFixedWidth(80)
        self.offset_input.setStyleSheet("background-color: #333; color: white;")
        top_row.addWidget(self.offset_input)

        self.offset_spin = QSpinBox()
        self.offset_spin.setButtonSymbols(QSpinBox.PlusMinus)
        self.offset_spin.setRange(0, 0xFFFFFF)
        self.offset_spin.setStyleSheet("QSpinBox { background-color: #333; color: white; }")
        self.offset_spin.setFixedWidth(20)
        self.offset_spin.setVisible(False)
        top_row.addWidget(self.offset_spin)

        self.offset_up = QPushButton("▲")
        self.offset_down = QPushButton("▼")
        self.offset_up.setFixedWidth(25)
        self.offset_down.setFixedWidth(25)
        self.offset_up.clicked.connect(self.increment_offset)
        self.offset_up.clicked.connect(self.apply_offset)
        self.offset_down.clicked.connect(self.decrement_offset)
        self.offset_down.clicked.connect(self.apply_offset)
        top_row.addWidget(self.offset_up)
        top_row.addWidget(self.offset_down)

        self.apply_offset_btn = QPushButton("Apply")
        self.glyph_count_label = QLabel("Glyphs: 0")
        self.glyph_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.glyph_count_label.setStyleSheet("color: white;")
        self.apply_offset_btn.setFixedWidth(60)
        self.apply_offset_btn.clicked.connect(self.apply_offset)
        top_row.addWidget(self.apply_offset_btn)
        
        # Add spacing after offset controls
        top_row.addSpacing(20)
        
        # Texture resolution input (moved before glyph count)
        top_row.addWidget(QLabel("Texture:"))
        self.texture_width_input = QLineEdit(str(self.texture_size[0]))
        self.texture_height_input = QLineEdit(str(self.texture_size[1]))
        self.texture_width_input.setFixedWidth(50)
        self.texture_height_input.setFixedWidth(50)
        self.texture_width_input.setStyleSheet("background-color: #333; color: white;")
        self.texture_height_input.setStyleSheet("background-color: #333; color: white;")
        self.texture_width_input.setPlaceholderText("width")
        self.texture_height_input.setPlaceholderText("height")
        top_row.addWidget(self.texture_width_input)
        top_row.addWidget(QLabel("x"))
        top_row.addWidget(self.texture_height_input)
        
        # Apply texture resolution button
        self.apply_texture_btn = QPushButton("Apply")
        self.apply_texture_btn.setFixedWidth(60)
        self.apply_texture_btn.clicked.connect(self.apply_texture_resolution)
        top_row.addWidget(self.apply_texture_btn)
        
        # Add spacing after texture controls
        top_row.addSpacing(20)
        
        top_row.addWidget(self.glyph_count_label)
        
        # Add spacing after glyph count
        top_row.addSpacing(20)

        for btn in [self.offset_up, self.offset_down, self.apply_offset_btn, self.apply_texture_btn]:
            btn.setStyleSheet("background-color: #333333; color: white;")

        top_row.addStretch()

        # Zoom controls
        top_row.addWidget(QLabel("Zoom:"))
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedWidth(25)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        top_row.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedWidth(25)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        top_row.addWidget(self.zoom_in_btn)
        
        for btn in [self.zoom_out_btn, self.zoom_in_btn]:
            btn.setStyleSheet("background-color: #333333; color: white;")

        layout.addLayout(top_row)

        # Canvas
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor(60, 60, 60))
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.mouseDoubleClickEvent = self.handle_view_double_click
        layout.addWidget(self.view, stretch=1)

        # Buttons
        bottom_row = QHBoxLayout()
        self.load_texture_btn = QPushButton("Load Texture")
        self.load_abc_btn = QPushButton("Load .abc")
        self.export_json_btn = QPushButton("Export to JSON")
        self.import_json_btn = QPushButton("Import from JSON")
        self.delete_symbols_btn = QPushButton("Delete Symbols")
        self.add_symbol_btn = QPushButton("Add Symbol")
        self.save_abc_btn = QPushButton("Save .abc")
        for btn in [self.load_texture_btn, self.load_abc_btn, self.export_json_btn, self.import_json_btn, self.delete_symbols_btn, self.add_symbol_btn, self.save_abc_btn]:
            btn.setStyleSheet("background-color: #333333; color: white;")
        self.export_json_btn.setEnabled(False)
        self.import_json_btn.setEnabled(False)
        self.delete_symbols_btn.setEnabled(False)
        self.add_symbol_btn.setEnabled(False)
        self.save_abc_btn.setEnabled(False)

        bottom_row.addWidget(self.load_texture_btn)
        bottom_row.addWidget(self.load_abc_btn)
        bottom_row.addWidget(self.export_json_btn)
        bottom_row.addWidget(self.import_json_btn)
        bottom_row.addWidget(self.delete_symbols_btn)
        bottom_row.addWidget(self.add_symbol_btn)
        bottom_row.addWidget(self.save_abc_btn)
        layout.addLayout(bottom_row)

        self.load_texture_btn.clicked.connect(self.load_texture)
        self.load_abc_btn.clicked.connect(self.load_abc)
        self.export_json_btn.clicked.connect(self.export_json)
        self.import_json_btn.clicked.connect(self.import_json)
        self.delete_symbols_btn.clicked.connect(self.delete_symbols)
        self.add_symbol_btn.clicked.connect(self.add_symbol)
        self.save_abc_btn.clicked.connect(self.save_abc)

    def load_texture(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Texture", "", "Images (*.dds *.png)")
        if not path:
            return
        self.texture_path = path
        image = Image.open(path)
        self.texture_size = image.size

        # Update texture resolution inputs with actual image size
        self.texture_width_input.setText(str(image.size[0]))
        self.texture_height_input.setText(str(image.size[1]))

        img = image.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
        self.pixmap = QPixmap.fromImage(qimg)
        self.glyph_count_label.setText(f"Glyphs: {len(self.glyphs)}")
        self.refresh_view()

    def load_abc(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open ABC", "", "ABC Files (*.abc)")
        if not path:
            return
        self.abc_path = path
        try:
            with open(path, "rb") as f:
                self.original_data = f.read()
        except Exception as e:
            self.show_error("Error", f"Failed to read ABC file:\n{str(e)}")
            return

        # Determine table layout from header
        if len(self.original_data) < 22:
            self.show_warning("Error", "ABC file too small.")
            return
        header = self.original_data[:22]
        self.charmap_max_codepoint = int.from_bytes(header[20:22], "little")
        self.charmap_count = self.charmap_max_codepoint + 1
        self.charmap_offset = 22
        self.charmap_end = self.charmap_offset + self.charmap_count * 2
        self.auto_offset = self.charmap_end
        if self.charmap_end + 2 > len(self.original_data):
            self.show_warning("Error", "ABC character map exceeds file size.")
            return
        self.charmap = list(struct.unpack_from(f"<{self.charmap_count}H", self.original_data, self.charmap_offset))
        self.glyph_record_count = struct.unpack_from("<H", self.original_data, self.charmap_end)[0]
        self.glyph_to_chars = {}
        for codepoint, glyph_index in enumerate(self.charmap):
            if glyph_index:
                self.glyph_to_chars.setdefault(glyph_index, []).append(codepoint)
        
        # Extract header data (bytes 4-19)
        self.glyph_height = struct.unpack("<f", self.original_data[4:8])[0]
        self.unknown_data_h1 = struct.unpack("<f", self.original_data[8:12])[0]
        self.unknown_data_h2 = struct.unpack("<f", self.original_data[12:16])[0]
        self.unknown_data_h3 = struct.unpack("<f", self.original_data[16:20])[0]
        self.offset_dec = self.charmap_end + 2  # First glyph offset
        self.offset_input.setText(str(self.offset_dec))
        self.manual_offset = False
        self.dirty = False
        self.extract_glyphs(self.offset_dec, manual=False)

        # Update combined offset label (hidden)
        self.offsets_label.setText("")

        self.export_json_btn.setEnabled(True)
        self.import_json_btn.setEnabled(True)
        self.delete_symbols_btn.setEnabled(True)
        self.add_symbol_btn.setEnabled(True)
        self.save_abc_btn.setEnabled(True)

    def extract_glyphs(self, offset, manual=False):
        data = self.original_data
        auto_offset = getattr(self, 'auto_offset', None)
        if auto_offset is None or auto_offset + 24 > len(data):
            self.show_warning("Invalid Offset", "Offset exceeds file size.")
            return

        self.special_block = data[auto_offset:auto_offset+2]
        record_count = getattr(self, "glyph_record_count", None)

        # Determine start position for glyphs
        # Now offset points to first glyph, so we don't need to skip service block
        i = offset
        index = 0
        temp_glyphs = []
        while i + 24 <= len(data):
            if record_count is not None and index >= record_count:
                break
            entry = data[i:i+24]
            if len(entry) < 24:
                break
            try:
                # Correct structure: unknown_data (2 bytes), UV coordinates (16 bytes), padding/width/cell_width (6 bytes)
                unknown_data = struct.unpack("<H", entry[:2])[0]
                x0, y0, x1, y1 = struct.unpack("<ffff", entry[2:18])
                padding_left, width, cell_width = struct.unpack("<hHH", entry[18:24])
            except struct.error:
                break

            TOLERANCE = 0.02
            if not (0.0 <= x0 <= 1.0 + TOLERANCE and 0.0 <= x1 <= 1.0 + TOLERANCE and
                    0.0 <= y0 <= 1.0 + TOLERANCE and 0.0 <= y1 <= 1.0 + TOLERANCE):
                i += 24
                index += 1
                continue

            hex_repr = " ".join(f"{b:02X}" for b in entry)
            glyph = {
                "index": index,
                "cell_width": cell_width,
                "unknown_data": unknown_data,  # not studied
                "chars": [chr(c) for c in self.glyph_to_chars.get(index, [])],
                "codepoints": self.glyph_to_chars.get(index, []),
                "uv_x_start": x0, "uv_y_start": y0, "uv_x_end": x1, "uv_y_end": y1,
                "px_x_start": int(x0 * self.texture_size[0]),
                "px_y_start": int(y0 * self.texture_size[1]),
                "px_x_end": int(x1 * self.texture_size[0]),
                "px_y_end": int(y1 * self.texture_size[1]),
                "padding_left": padding_left,
                "glyph_width": width,
                "hex": hex_repr
            }
            temp_glyphs.append(glyph)
            i += 24
            index += 1

        self.trailing_data = data[i:]

        if temp_glyphs:
            self.glyphs = temp_glyphs
            self.glyph_count_label.setText(f"Glyphs: {len(self.glyphs)}")
            self.refresh_view()
        else:
            self.show_warning("No Glyphs", "No valid glyphs found at this offset.")

    def export_json(self):
        if not self.glyphs:
            self.show_warning("No Data", "Load a .abc file first.")
            return
    
        class ExportDialog(QDialog):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Export Coordinate Format")
                self.setStyleSheet("background-color: #202020; color: white;")
                self.setFixedSize(200, 80)
                layout = QVBoxLayout()
    
                label = QLabel("Choose coordinate export format:")
                label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                label.setStyleSheet("color: white;")
                layout.addWidget(label)
    
                btn_row = QHBoxLayout()
                self.uv_btn = QPushButton("UV (0.0–1.0)")
                self.px_btn = QPushButton("Pixel")
                for btn in (self.uv_btn, self.px_btn):
                    btn.setStyleSheet("background-color: #333333; color: white;")
                    btn.setFixedWidth(85)
                    btn_row.addWidget(btn)
                layout.addLayout(btn_row)
    
                self.selection = None
                self.uv_btn.clicked.connect(lambda: self.choose("uv"))
                self.px_btn.clicked.connect(lambda: self.choose("pixel"))
    
                self.setLayout(layout)
    
            def choose(self, mode):
                self.selection = mode
                self.accept()
    
        dlg = ExportDialog()
        if dlg.exec_() != QDialog.Accepted or dlg.selection is None:
            return
    
        use_uv = dlg.selection == "uv"
    
        export_path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
        if not export_path:
            return
    
        output = []
        # Add parameter descriptions
        output.append({
            "_note": {
                "_hex": "is for reference only and is not used during import",
                "_uv_xy_start_end": "UV coordinates (0.0-1.0) for texture mapping",
                "_px_xy_start_end": "Pixel coordinates for texture mapping",
                "_padding_left": "Left padding width before glyph (can be negative for kerning)",
                "_glyph_width": "Width of the glyph/symbol in pixels",
                "_cell_width": "Total width allocated for the glyph cell",
                "_unknown_data": "Unknown 2-byte field preserved by import/export",
                "_chars": "Characters that map to this glyph through the ABC character map",
                "_codepoints": "Unicode codepoints that map to this glyph"
            }
        })
        # Add global parameters
        output.append({
            "global": {
                "glyph_height": self.glyph_height,
                "unknown_data_h1": self.unknown_data_h1,
                "unknown_data_h2": self.unknown_data_h2,
                "unknown_data_h3": self.unknown_data_h3,
                "charmap_max_codepoint": getattr(self, "charmap_max_codepoint", 0),
                "charmap_count": getattr(self, "charmap_count", 0),
                "charmap_nonzero_count": sum(1 for v in getattr(self, "charmap", []) if v),
                "glyph_record_count": getattr(self, "glyph_record_count", len(self.glyphs)),
                "trailing_data_hex": getattr(self, "trailing_data", b"").hex(" ")
            }
        })
        for g in self.glyphs:
            item = {
                "index": g["index"],
                "hex": g["hex"],
                "unknown_data": g.get("unknown_data", 0),  # not studied
                "chars": g.get("chars", []),
                "codepoints": g.get("codepoints", []),
            }
            if use_uv:
                item["uv_x_start"] = g["uv_x_start"]
                item["uv_y_start"] = g["uv_y_start"]
                item["uv_x_end"] = g["uv_x_end"]
                item["uv_y_end"] = g["uv_y_end"]
            else:
                item["px_x_start"] = g["px_x_start"]
                item["px_y_start"] = g["px_y_start"]
                item["px_x_end"] = g["px_x_end"]
                item["px_y_end"] = g["px_y_end"]
            item["padding_left"] = g["padding_left"]
            item["glyph_width"] = g["glyph_width"]
            item["cell_width"] = g["cell_width"]
            output.append(item)
    
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=4)
        except Exception as e:
            self.show_error("Error", f"Failed to write JSON file:\n{str(e)}")
            return

        self.show_info("Export Complete", f"Exported to:\n{export_path}")

    def parse_symbol_delete_text(self, text):
        codepoints = set()
        token_re = re.compile(r".", re.DOTALL)

        def parse_code(token):
            try:
                return self.parse_single_codepoint(token)
            except ValueError:
                return None

        for raw in re.split(r"[\s,;]+", text):
            token = raw.strip()
            if not token:
                continue

            range_match = re.fullmatch(
                r"(U\+[0-9A-Fa-f]{1,6}|0x[0-9A-Fa-f]{1,6}|\d+|.)-(U\+[0-9A-Fa-f]{1,6}|0x[0-9A-Fa-f]{1,6}|\d+|.)",
                token,
                re.DOTALL
            )
            if range_match:
                start = parse_code(range_match.group(1))
                end = parse_code(range_match.group(2))
                if start is not None and end is not None:
                    if start > end:
                        start, end = end, start
                    codepoints.update(range(start, end + 1))
                    continue

            parsed = parse_code(token)
            if parsed is not None:
                codepoints.add(parsed)
                continue

            for match in token_re.finditer(token):
                char = match.group(0)
                if char not in "\r\n\t ":
                    parsed_char = parse_code(char)
                    if parsed_char is not None:
                        codepoints.add(parsed_char)

        return {c for c in codepoints if 0 <= c <= 0x10FFFF}

    def parse_single_codepoint(self, text):
        token = text.strip()
        if not token:
            return None
        if token.upper().startswith("U+"):
            return int(token[2:], 16)
        if token.lower().startswith("0x"):
            return int(token[2:], 16)
        if token.isdigit():
            return int(token, 10)
        return ord(token[0])

    def parse_index_delete_text(self, text):
        indexes = set()
        for raw in re.split(r"[\s,;]+", text):
            token = raw.strip()
            if not token:
                continue

            range_match = re.fullmatch(r"(\d+)-(\d+)", token)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                if start > end:
                    start, end = end, start
                indexes.update(range(start, end + 1))
                continue

            if token.isdigit():
                indexes.add(int(token))

        return indexes

    def add_symbol(self):
        if not self.abc_path or not self.original_data:
            self.show_warning("Error", "Load an .abc file first.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Add Symbol / Glyph Index")
        dlg.setStyleSheet("background-color: #202020; color: white;")
        dlg.resize(380, 170)
        layout = QVBoxLayout(dlg)

        symbol_row = QHBoxLayout()
        symbol_row.addWidget(QLabel("Symbol/codepoint:"))
        symbol_input = QLineEdit()
        symbol_input.setPlaceholderText("Optional: А or U+0410 or 0xC0")
        symbol_input.setStyleSheet("background-color: #333; color: white;")
        symbol_row.addWidget(symbol_input)
        layout.addLayout(symbol_row)

        copy_row = QHBoxLayout()
        copy_row.addWidget(QLabel("Copy glyph index:"))
        copy_index_input = QSpinBox()
        copy_index_input.setRange(0, max(0, getattr(self, "glyph_record_count", len(self.glyphs)) - 1))
        copy_index_input.setValue(0)
        copy_index_input.setStyleSheet("QSpinBox { background-color: #333; color: white; }")
        copy_row.addWidget(copy_index_input)
        layout.addLayout(copy_row)

        rect_row = QHBoxLayout()
        rect_row.addWidget(QLabel("Pixel rect:"))
        rect_input = QLineEdit()
        rect_input.setPlaceholderText("Optional: x0 y0 x1 y1")
        rect_input.setStyleSheet("background-color: #333; color: white;")
        rect_row.addWidget(rect_input)
        layout.addLayout(rect_row)

        metrics_row = QHBoxLayout()
        metrics_row.addWidget(QLabel("Metrics:"))
        metrics_input = QLineEdit()
        metrics_input.setPlaceholderText("Optional: padding width cell_width")
        metrics_input.setStyleSheet("background-color: #333; color: white;")
        metrics_row.addWidget(metrics_input)
        layout.addLayout(metrics_row)

        hint = QLabel("Leave Symbol/codepoint empty to add only a new glyph index.")
        hint.setStyleSheet("color: #aaa;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() != QDialog.Accepted:
            return

        old_charmap = list(getattr(self, "charmap", []))
        symbol_text = symbol_input.text().strip()
        codepoint = None
        if symbol_text:
            try:
                codepoint = self.parse_single_codepoint(symbol_text)
            except ValueError:
                self.show_warning("Invalid Symbol", "Invalid symbol/codepoint value.")
                return

            if codepoint is None or not (0 <= codepoint <= 0xFFFF):
                self.show_warning("Invalid Symbol", "ABC charmap supports codepoints from 0 to 65535.")
                return

            if codepoint < len(old_charmap) and old_charmap[codepoint] != 0:
                self.show_warning("Already Exists", f"This symbol is already mapped to glyph index {old_charmap[codepoint]}.")
                return

        old_record_count = getattr(self, "glyph_record_count", len(self.glyphs))
        source_index = copy_index_input.value()
        if source_index < 0 or source_index >= old_record_count:
            self.show_warning("Invalid Index", "Copy glyph index is outside the glyph table.")
            return

        old_records_start = getattr(self, "charmap_end", 22) + 2
        old_records_end = old_records_start + old_record_count * 24
        if old_records_end > len(self.original_data):
            self.show_error("Error", "ABC glyph table exceeds file size.")
            return

        old_records = [
            self.original_data[old_records_start + i * 24:old_records_start + (i + 1) * 24]
            for i in range(old_record_count)
        ]

        new_record = bytearray(old_records[source_index])
        rect_values = [v for v in re.split(r"[\s,;]+", rect_input.text().strip()) if v]
        metrics_values = [v for v in re.split(r"[\s,;]+", metrics_input.text().strip()) if v]

        if rect_values:
            if len(rect_values) != 4:
                self.show_warning("Invalid Rect", "Pixel rect must contain exactly 4 numbers: x0 y0 x1 y1.")
                return
            try:
                px_x0, px_y0, px_x1, px_y1 = [int(v) for v in rect_values]
            except ValueError:
                self.show_warning("Invalid Rect", "Pixel rect values must be integer numbers.")
                return
            texture_width, texture_height = self.texture_size
            if texture_width <= 0 or texture_height <= 0 or px_x1 <= px_x0 or px_y1 <= px_y0:
                self.show_warning("Invalid Rect", "Pixel rect must fit a positive x0 y0 x1 y1 rectangle.")
                return
            x0 = px_x0 / texture_width
            y0 = px_y0 / texture_height
            x1 = px_x1 / texture_width
            y1 = px_y1 / texture_height
            struct.pack_into("<ffff", new_record, 2, x0, y0, x1, y1)

            glyph_width = px_x1 - px_x0
            struct.pack_into("<hHH", new_record, 18, 0, glyph_width, glyph_width)

        if metrics_values:
            if len(metrics_values) != 3:
                self.show_warning("Invalid Metrics", "Metrics must contain exactly 3 numbers: padding width cell_width.")
                return
            try:
                padding_left, glyph_width, cell_width = [int(v) for v in metrics_values]
            except ValueError:
                self.show_warning("Invalid Metrics", "Metric values must be integer numbers.")
                return
            if not (-32768 <= padding_left <= 32767 and 0 <= glyph_width <= 65535 and 0 <= cell_width <= 65535):
                self.show_warning("Invalid Metrics", "Metric values are outside the supported range.")
                return
            struct.pack_into("<hHH", new_record, 18, padding_left, glyph_width, cell_width)

        new_charmap = old_charmap[:]
        if codepoint is not None and codepoint >= len(new_charmap):
            new_charmap.extend([0] * (codepoint + 1 - len(new_charmap)))
        if len(new_charmap) > 0x10000:
            self.show_warning("Invalid Symbol", "ABC header cannot store a charmap larger than 65535 entries.")
            return

        new_index = old_record_count
        if codepoint is not None:
            new_charmap[codepoint] = new_index
        new_record_count = old_record_count + 1
        new_header = bytearray(self.original_data[:22])
        struct.pack_into("<H", new_header, 20, len(new_charmap) - 1)

        output = bytearray(new_header)
        output.extend(struct.pack(f"<{len(new_charmap)}H", *new_charmap))
        output.extend(struct.pack("<H", new_record_count))
        for record in old_records:
            output.extend(record)
        output.extend(new_record)
        output.extend(self.original_data[old_records_end:])

        old_size = len(self.original_data)
        self.original_data = bytes(output)
        self.refresh_abc_from_memory(dirty=True)

        symbol_line = "Added glyph index only"
        if codepoint is not None:
            display_char = chr(codepoint) if codepoint >= 32 else f"U+{codepoint:04X}"
            symbol_line = f"Added symbol: {display_char} (U+{codepoint:04X})"
        self.show_info(
            "Glyph Added",
            f"{symbol_line}\n"
            f"New glyph index: {new_index}\n"
            f"Copied from index: {source_index}\n"
            f"Size in memory: {old_size} -> {len(output)} bytes\n"
            "Use Save .abc to write the file."
        )

    def refresh_abc_from_memory(self, dirty=False):
        header = self.original_data[:22]
        self.charmap_max_codepoint = int.from_bytes(header[20:22], "little")
        self.charmap_count = self.charmap_max_codepoint + 1
        self.charmap_offset = 22
        self.charmap_end = self.charmap_offset + self.charmap_count * 2
        self.auto_offset = self.charmap_end
        self.charmap = list(struct.unpack_from(f"<{self.charmap_count}H", self.original_data, self.charmap_offset))
        self.glyph_record_count = struct.unpack_from("<H", self.original_data, self.charmap_end)[0]
        self.glyph_to_chars = {}
        for codepoint, glyph_index in enumerate(self.charmap):
            if glyph_index:
                self.glyph_to_chars.setdefault(glyph_index, []).append(codepoint)

        self.glyph_height = struct.unpack("<f", self.original_data[4:8])[0]
        self.unknown_data_h1 = struct.unpack("<f", self.original_data[8:12])[0]
        self.unknown_data_h2 = struct.unpack("<f", self.original_data[12:16])[0]
        self.unknown_data_h3 = struct.unpack("<f", self.original_data[16:20])[0]
        self.offset_dec = self.charmap_end + 2
        self.offset_input.setText(str(self.offset_dec))
        self.manual_offset = False
        self.dirty = dirty
        self.save_abc_btn.setEnabled(True)
        self.extract_glyphs(self.offset_dec, manual=False)
        self.offsets_label.setText("")

    def reload_abc_data(self, path):
        with open(path, "rb") as f:
            self.original_data = f.read()
        self.refresh_abc_from_memory(dirty=False)

    def save_abc(self):
        if not self.original_data:
            self.show_warning("No Data", "Load an .abc file first.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save ABC", self.abc_path or "", "ABC Files (*.abc)")
        if not save_path:
            return

        try:
            with open(save_path, "wb") as f:
                f.write(self.original_data)
        except Exception as e:
            self.show_error("Error", f"Failed to write ABC file:\n{str(e)}")
            return

        self.abc_path = save_path
        self.dirty = False
        self.show_info("Saved", f"Saved to:\n{save_path}")

    def handle_view_double_click(self, event):
        if not self.glyphs:
            return

        scene_pos = self.view.mapToScene(event.pos())
        for glyph in reversed(self.glyphs):
            x0 = glyph["uv_x_start"] * self.texture_size[0] * self.zoom
            y0 = glyph["uv_y_start"] * self.texture_size[1] * self.zoom
            x1 = glyph["uv_x_end"] * self.texture_size[0] * self.zoom
            y1 = glyph["uv_y_end"] * self.texture_size[1] * self.zoom
            rect = QRectF(x0, y0, x1 - x0, y1 - y0)
            if rect.contains(scene_pos):
                self.edit_glyph(glyph)
                return

    def edit_glyph(self, glyph):
        if not self.original_data:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit Glyph {glyph['index']}")
        dlg.setStyleSheet("background-color: #202020; color: white;")
        dlg.resize(420, 260)
        layout = QVBoxLayout(dlg)

        px_row = QHBoxLayout()
        px_row.addWidget(QLabel("Pixel rect:"))
        px_input = QLineEdit(
            f"{glyph['px_x_start']} {glyph['px_y_start']} {glyph['px_x_end']} {glyph['px_y_end']}"
        )
        px_input.setStyleSheet("background-color: #333; color: white;")
        px_row.addWidget(px_input)
        layout.addLayout(px_row)

        uv_row = QHBoxLayout()
        uv_row.addWidget(QLabel("UV rect:"))
        uv_input = QLineEdit(
            f"{glyph['uv_x_start']:.9f} {glyph['uv_y_start']:.9f} {glyph['uv_x_end']:.9f} {glyph['uv_y_end']:.9f}"
        )
        uv_input.setStyleSheet("background-color: #333; color: white;")
        uv_row.addWidget(uv_input)
        layout.addLayout(uv_row)

        metrics_row = QHBoxLayout()
        metrics_row.addWidget(QLabel("Metrics:"))
        metrics_input = QLineEdit(
            f"{glyph['padding_left']} {glyph['glyph_width']} {glyph['cell_width']}"
        )
        metrics_input.setStyleSheet("background-color: #333; color: white;")
        metrics_row.addWidget(metrics_input)
        layout.addLayout(metrics_row)

        unknown_row = QHBoxLayout()
        unknown_row.addWidget(QLabel("Unknown:"))
        unknown_input = QLineEdit(str(glyph.get("unknown_data", 0)))
        unknown_input.setStyleSheet("background-color: #333; color: white;")
        unknown_row.addWidget(unknown_input)
        layout.addLayout(unknown_row)

        chars = "".join(glyph.get("chars", []))
        chars_label = QLabel(f"Chars: {chars if chars else '(none)'}")
        chars_label.setStyleSheet("color: #aaa;")
        layout.addWidget(chars_label)

        hint = QLabel("Edit either Pixel rect or UV rect; Pixel rect is used when changed.")
        hint.setStyleSheet("color: #aaa;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() != QDialog.Accepted:
            return

        try:
            px_values = [v for v in re.split(r"[\s,;]+", px_input.text().strip()) if v]
            uv_values = [v for v in re.split(r"[\s,;]+", uv_input.text().strip()) if v]
            metric_values = [v for v in re.split(r"[\s,;]+", metrics_input.text().strip()) if v]

            if len(metric_values) != 3:
                raise ValueError("Metrics must contain padding width cell_width.")
            padding_left, glyph_width, cell_width = [int(v) for v in metric_values]
            unknown_data = int(unknown_input.text().strip(), 0)

            original_px = f"{glyph['px_x_start']} {glyph['px_y_start']} {glyph['px_x_end']} {glyph['px_y_end']}"
            if px_input.text().strip() != original_px:
                if len(px_values) != 4:
                    raise ValueError("Pixel rect must contain x0 y0 x1 y1.")
                px_x0, px_y0, px_x1, px_y1 = [int(v) for v in px_values]
                if px_x1 <= px_x0 or px_y1 <= px_y0:
                    raise ValueError("Pixel rect must be a positive rectangle.")
                x0 = px_x0 / self.texture_size[0]
                y0 = px_y0 / self.texture_size[1]
                x1 = px_x1 / self.texture_size[0]
                y1 = px_y1 / self.texture_size[1]
            else:
                if len(uv_values) != 4:
                    raise ValueError("UV rect must contain x0 y0 x1 y1.")
                x0, y0, x1, y1 = [float(v) for v in uv_values]

            if not (0 <= unknown_data <= 0xFFFF):
                raise ValueError("Unknown must fit uint16.")
            if not (-32768 <= padding_left <= 32767 and 0 <= glyph_width <= 0xFFFF and 0 <= cell_width <= 0xFFFF):
                raise ValueError("Metrics are outside supported ranges.")
        except ValueError as e:
            self.show_warning("Invalid Glyph Data", str(e))
            return

        record_offset = self.offset_dec + glyph["index"] * 24
        if record_offset + 24 > len(self.original_data):
            self.show_error("Error", "Glyph record offset exceeds file size.")
            return

        data = bytearray(self.original_data)
        struct.pack_into("<H", data, record_offset, unknown_data)
        struct.pack_into("<ffff", data, record_offset + 2, x0, y0, x1, y1)
        struct.pack_into("<hHH", data, record_offset + 18, padding_left, glyph_width, cell_width)
        self.original_data = bytes(data)
        self.dirty = True
        self.extract_glyphs(self.offset_dec, manual=self.manual_offset)

    def delete_symbols(self):
        if not self.abc_path or not self.original_data:
            self.show_warning("Error", "Load an .abc file first.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Delete Symbols")
        dlg.setStyleSheet("background-color: #202020; color: white;")
        dlg.resize(520, 360)
        layout = QVBoxLayout(dlg)

        label = QLabel("Symbols/codepoints to delete:")
        label.setStyleSheet("color: white;")
        layout.addWidget(label)

        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Examples: ABC 0-9 U+0410-U+042F 0x20AC")
        text_edit.setStyleSheet("background-color: #333; color: white;")
        layout.addWidget(text_edit)

        hint = QLabel("Direct text, U+XXXX, 0xXXXX, decimal values, and ranges are supported.")
        hint.setStyleSheet("color: #aaa;")
        layout.addWidget(hint)

        index_label = QLabel("Glyph indexes to delete:")
        index_label.setStyleSheet("color: white;")
        layout.addWidget(index_label)

        index_edit = QTextEdit()
        index_edit.setPlaceholderText("Examples: 12 15 20-30")
        index_edit.setMaximumHeight(80)
        index_edit.setStyleSheet("background-color: #333; color: white;")
        layout.addWidget(index_edit)

        index_hint = QLabel("Indexes are the numbers drawn on the preview/exported as JSON index.")
        index_hint.setStyleSheet("color: #aaa;")
        layout.addWidget(index_hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() != QDialog.Accepted:
            return

        codepoints_to_delete = self.parse_symbol_delete_text(text_edit.toPlainText())
        glyph_indexes_to_delete = self.parse_index_delete_text(index_edit.toPlainText())
        if not codepoints_to_delete and not glyph_indexes_to_delete:
            self.show_warning("No Input", "Enter symbols/codepoints or glyph indexes to delete.")
            return

        old_charmap = list(getattr(self, "charmap", []))
        old_record_count = getattr(self, "glyph_record_count", len(self.glyphs))
        old_records_start = getattr(self, "charmap_end", 22) + 2
        old_records_end = old_records_start + old_record_count * 24
        if old_records_end > len(self.original_data):
            self.show_error("Error", "ABC glyph table exceeds file size.")
            return

        mapped_deleted = [
            codepoint for codepoint in codepoints_to_delete
            if codepoint < len(old_charmap) and old_charmap[codepoint] != 0
        ]
        valid_index_deleted = {
            index for index in glyph_indexes_to_delete
            if 0 <= index < old_record_count
        }
        protected_indices = {0}
        protected_requested = valid_index_deleted & protected_indices
        valid_index_deleted -= protected_indices

        if not mapped_deleted and not valid_index_deleted:
            message = "No entered symbols or glyph indexes are mapped in this ABC file."
            if protected_requested:
                message += "\nIndex 0 is protected."
            self.show_warning("No Matches", message)
            return

        new_charmap = old_charmap[:]
        for codepoint in mapped_deleted:
            new_charmap[codepoint] = 0
        for i, value in enumerate(new_charmap):
            if value in valid_index_deleted:
                new_charmap[i] = 0

        old_records = [
            self.original_data[old_records_start + i * 24:old_records_start + (i + 1) * 24]
            for i in range(old_record_count)
        ]

        keep_old_indices = {0}
        keep_old_indices.update(value for value in new_charmap if value)
        keep_old_indices.difference_update(valid_index_deleted)
        keep_old_indices.update(protected_indices)
        keep_old_indices = sorted(i for i in keep_old_indices if 0 <= i < old_record_count)
        index_map = {old_index: new_index for new_index, old_index in enumerate(keep_old_indices)}

        for i, value in enumerate(new_charmap):
            new_charmap[i] = index_map.get(value, 0) if value else 0

        while len(new_charmap) > 1 and new_charmap[-1] == 0:
            new_charmap.pop()

        new_record_count = len(keep_old_indices)
        new_header = bytearray(self.original_data[:22])
        struct.pack_into("<H", new_header, 20, len(new_charmap) - 1)

        output = bytearray(new_header)
        output.extend(struct.pack(f"<{len(new_charmap)}H", *new_charmap))
        output.extend(struct.pack("<H", new_record_count))
        for old_index in keep_old_indices:
            output.extend(old_records[old_index])
        output.extend(self.original_data[old_records_end:])

        old_size = len(self.original_data)
        self.original_data = bytes(output)
        self.refresh_abc_from_memory(dirty=True)

        removed_glyphs = old_record_count - new_record_count
        removed_bytes = old_size - len(output)
        self.show_info(
            "Symbols Deleted",
            f"Removed mapped symbols: {len(mapped_deleted)}\n"
            f"Removed requested indexes: {len(valid_index_deleted)}\n"
            f"Removed glyph records: {removed_glyphs}\n"
            f"Size in memory: {old_size} -> {len(output)} bytes ({removed_bytes} bytes saved)\n"
            "Use Save .abc to write the file."
        )

    def import_json(self):
        if not self.abc_path or not self.original_data:
            self.show_warning("Error", "Load an .abc file first.")
            return

        json_path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
        if not json_path:
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                imported = json.load(f)
        except Exception as e:
            self.show_error("Error", f"Failed to read JSON:\n{str(e)}")
            return

        # Validate JSON structure
        if not isinstance(imported, list):
            self.show_error("Error", "Invalid JSON structure: expected a list of glyphs.")
            return

        if not imported:
            self.show_error("Error", "JSON file is empty or contains no valid glyphs.")
            return

        data = bytearray(self.original_data)
        offset = self.offset_dec
        stride = 24

        # Find and validate global data in imported JSON
        global_data = None
        for entry in imported:
            if isinstance(entry, dict) and "global" in entry:
                global_data = entry["global"]
                break
        
        # Validate and update header data if found
        if global_data:
            if not isinstance(global_data, dict):
                self.show_error("Error", "Invalid global data structure in JSON.")
                return
            
            # Check for nested structure
            if "header" in global_data:
                self.show_error("Error", "Invalid JSON structure: move header fields from 'global.header' to 'global'")
                return

            # Check for required header fields
            required_fields = {"glyph_height", "unknown_data_h1", "unknown_data_h2", "unknown_data_h3"}
            if not any(field in global_data for field in required_fields):
                self.show_error("Error", "Invalid JSON: missing required header fields in 'global'")
                return
                
            try:
                if "glyph_height" in global_data:
                    struct.pack_into("<f", data, 4, float(global_data["glyph_height"]))
                if "unknown_data_h1" in global_data:
                    struct.pack_into("<f", data, 8, float(global_data["unknown_data_h1"]))
                if "unknown_data_h2" in global_data:
                    struct.pack_into("<f", data, 12, float(global_data["unknown_data_h2"]))
                if "unknown_data_h3" in global_data:
                    struct.pack_into("<f", data, 16, float(global_data["unknown_data_h3"]))
            except (ValueError, TypeError) as e:
                self.show_error("Error", f"Invalid header data values: {str(e)}")
                return
                
        try:
            valid_glyphs = 0
            for glyph in imported:
                # Skip service records like _note or glyph_count
                if not isinstance(glyph, dict):
                    continue
                    
                if "index" not in glyph:
                    continue
                    
                # Validate glyph index
                try:
                    glyph_index = int(glyph["index"])
                    if glyph_index < 0:
                        continue
                except (ValueError, TypeError):
                    continue
                    
                # Now offset points to first glyph, so we calculate position directly
                i = offset + glyph_index * stride
                if i + stride > len(data):
                    continue

                # Validate coordinate data
                has_uv = any(key.startswith("uv_") for key in glyph.keys())
                has_px = any(key.startswith("px_") for key in glyph.keys())
                
                if not (has_uv or has_px):
                    continue
                    
                try:
                    if has_uv:
                        x0 = float(glyph["uv_x_start"])
                        y0 = float(glyph["uv_y_start"])
                        x1 = float(glyph["uv_x_end"])
                        y1 = float(glyph["uv_y_end"])
                    else:  # has_px
                        x0 = float(glyph["px_x_start"]) / self.texture_size[0]
                        y0 = float(glyph["px_y_start"]) / self.texture_size[1]
                        x1 = float(glyph["px_x_end"]) / self.texture_size[0]
                        y1 = float(glyph["px_y_end"]) / self.texture_size[1]
                except (ValueError, TypeError, KeyError):
                    continue

                # Validate and write glyph data
                try:
                    unknown_data = int(glyph.get("unknown_data", struct.unpack_from("<H", data, i)[0]))
                    cell_width = int(glyph.get("cell_width", struct.unpack_from("<H", data, i + 22)[0]))
                    width_px = int(glyph.get("glyph_width", struct.unpack_from("<H", data, i + 20)[0]))
                    padding_left_val = int(glyph.get("padding_left", struct.unpack_from("<h", data, i + 18)[0]))
                    
                    struct.pack_into("<H", data, i, unknown_data)
                    struct.pack_into("<H", data, i + 22, cell_width)
                    struct.pack_into("<ffff", data, i + 2, x0, y0, x1, y1)
                    struct.pack_into("<hH", data, i + 18, padding_left_val, width_px)
                    
                    valid_glyphs += 1
                except (ValueError, TypeError, struct.error):
                    continue

            if valid_glyphs == 0:
                self.show_warning("Warning", "No valid glyphs found in JSON file.")
                return

            self.original_data = bytes(data)
            self.refresh_abc_from_memory(dirty=True)
            self.show_info("Success", f"ABC updated in memory.\nUpdated glyphs: {valid_glyphs}\nUse Save .abc to write the file.")

        except Exception as e:
            self.show_error("Error", f"Failed to apply changes:\n{str(e)}")

    def refresh_view(self):
        self.scene.clear()
        
        # Add texture if available
        if hasattr(self, "pixmap"):
            pix_item = QGraphicsPixmapItem(self.pixmap.scaled(
                int(self.pixmap.width() * self.zoom),
                int(self.pixmap.height() * self.zoom),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.scene.addItem(pix_item)

        # Draw glyphs regardless of texture presence
        if self.glyphs:
            pen = QPen(QColor(0, 255, 0), 1, Qt.PenStyle.SolidLine)
            font = QFont("Arial", 8)
            font.setBold(True)

            for g in self.glyphs:
                x0 = int(g["uv_x_start"] * self.texture_size[0] * self.zoom)
                y0 = int(g["uv_y_start"] * self.texture_size[1] * self.zoom)
                x1 = int(g["uv_x_end"] * self.texture_size[0] * self.zoom)
                y1 = int(g["uv_y_end"] * self.texture_size[1] * self.zoom)
                rect = QRectF(x0, y0, x1 - x0, y1 - y0)
                self.scene.addRect(rect, pen)

                index_text = str(g["index"])
                text_item = self.scene.addText(index_text, font)
                if text_item:
                    text_item.setDefaultTextColor(QColor("white"))
                    text_item.setPos(x0 + 2, y0 + 2)

    def increment_offset(self):
        try:
            val = int(self.offset_input.text())
            self.offset_input.setText(str(val + 1))
        except ValueError:
            self.show_warning("Error", "Invalid offset value.")

    def decrement_offset(self):
        try:
            val = int(self.offset_input.text())
            self.offset_input.setText(str(max(0, val - 1)))
        except ValueError:
            self.show_warning("Error", "Invalid offset value.")

    def apply_offset(self):
        try:
            offset = int(self.offset_input.text())
            self.offset_dec = offset
            self.manual_offset = True
            self.extract_glyphs(offset, manual=True)

            if not self.glyphs:
                self.show_warning("No Glyphs", "No valid glyphs found at this offset.")
        except Exception as e:
            self.show_warning("Invalid", "Invalid decimal offset.")

    def apply_texture_resolution(self):
        """Apply manually entered texture resolution"""
        try:
            width = int(self.texture_width_input.text())
            height = int(self.texture_height_input.text())
            if width <= 0 or height <= 0:
                self.show_warning("Error", "Texture resolution must be positive numbers.")
                return
            self.texture_size = (width, height)
            
            # Update pixel coordinates for existing glyphs
            if self.glyphs:
                for glyph in self.glyphs:
                    glyph["px_x_start"] = int(glyph["uv_x_start"] * width)
                    glyph["px_y_start"] = int(glyph["uv_y_start"] * height)
                    glyph["px_x_end"] = int(glyph["uv_x_end"] * width)
                    glyph["px_y_end"] = int(glyph["uv_y_end"] * height)
            
            self.refresh_view()
            self.show_info("Success", f"Texture resolution updated to {width}x{height}")
        except ValueError:
            self.show_warning("Error", "Invalid texture resolution values.")

    def zoom_in(self):
        self.zoom = min(3.0, self.zoom + 0.1)
        self.zoom_label.setText(f"{int(self.zoom * 100)}%")
        self.glyph_count_label.setText(f"Glyphs: {len(self.glyphs)}")
        self.refresh_view()

    def zoom_out(self):
        self.zoom = max(0.1, self.zoom - 0.1)
        self.zoom_label.setText(f"{int(self.zoom * 100)}%")
        self.glyph_count_label.setText(f"Glyphs: {len(self.glyphs)}")
        self.refresh_view()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ABCFontEditor()
    editor.resize(960, 720)
    editor.show()
    sys.exit(app.exec_())
