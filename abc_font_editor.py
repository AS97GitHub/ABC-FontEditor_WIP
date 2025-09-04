import os
import struct
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QHBoxLayout, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QLineEdit, QMessageBox, QComboBox, QSpinBox, QDialog, QDialogButtonBox,
    QSizePolicy
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
        layout.addWidget(self.view, stretch=1)

        # Buttons
        bottom_row = QHBoxLayout()
        self.load_texture_btn = QPushButton("Load Texture")
        self.load_abc_btn = QPushButton("Load .abc")
        self.export_json_btn = QPushButton("Export to JSON")
        self.import_json_btn = QPushButton("Import from JSON")
        for btn in [self.load_texture_btn, self.load_abc_btn, self.export_json_btn, self.import_json_btn]:
            btn.setStyleSheet("background-color: #333333; color: white;")
        self.export_json_btn.setEnabled(False)
        self.import_json_btn.setEnabled(False)

        bottom_row.addWidget(self.load_texture_btn)
        bottom_row.addWidget(self.load_abc_btn)
        bottom_row.addWidget(self.export_json_btn)
        bottom_row.addWidget(self.import_json_btn)
        layout.addLayout(bottom_row)

        self.load_texture_btn.clicked.connect(self.load_texture)
        self.load_abc_btn.clicked.connect(self.load_abc)
        self.export_json_btn.clicked.connect(self.export_json)
        self.import_json_btn.clicked.connect(self.import_json)

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

        # Determine auto_offset from header
        if len(self.original_data) < 22:
            self.show_warning("Error", "ABC file too small.")
            return
        header = self.original_data[:22]
        self.auto_offset = int.from_bytes(header[20:22], "little") * 2
        
        # Extract header data (bytes 4-19)
        self.glyph_height = struct.unpack("<f", self.original_data[4:8])[0]
        self.unknown_data_h1 = struct.unpack("<f", self.original_data[8:12])[0]
        self.unknown_data_h2 = struct.unpack("<f", self.original_data[12:16])[0]
        self.unknown_data_h3 = struct.unpack("<f", self.original_data[16:20])[0]
        self.offset_dec = self.auto_offset + 26  # First glyph offset
        self.offset_input.setText(str(self.offset_dec))
        self.manual_offset = False
        self.extract_glyphs(self.offset_dec, manual=False)

        # Update combined offset label (hidden)
        self.offsets_label.setText("")

        self.export_json_btn.setEnabled(True)
        self.import_json_btn.setEnabled(True)

    def extract_glyphs(self, offset, manual=False):
        data = self.original_data
        auto_offset = getattr(self, 'auto_offset', None)
        if auto_offset is None or auto_offset + 24 > len(data):
            self.show_warning("Invalid Offset", "Offset exceeds file size.")
            return

        # Always extract the service block for export/import (26 bytes total)
        self.special_block = data[auto_offset:auto_offset+26]

        # Determine start position for glyphs
        # Now offset points to first glyph, so we don't need to skip service block
        i = offset
        index = 0
        temp_glyphs = []
        while i + 24 <= len(data):
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
                "_unknown_data": "Unknown data field (purpose not studied)"
            }
        })
        # Add global parameters
        output.append({
            "global": {
                "glyph_height": self.glyph_height,
                "unknown_data_h1": self.unknown_data_h1,
                "unknown_data_h2": self.unknown_data_h2,
                "unknown_data_h3": self.unknown_data_h3
            }
        })
        for g in self.glyphs:
            item = {
                "index": g["index"],
                "hex": g["hex"],
                "unknown_data": g.get("unknown_data", 0),  # not studied
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
                
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Modified ABC", "", "ABC Files (*.abc)")
            if not save_path:
                return

            try:
                with open(save_path, "wb") as f:
                    f.write(data)
            except Exception as e:
                self.show_error("Error", f"Failed to write ABC file:\n{str(e)}")
                return

            self.show_info("Success", "ABC file updated and saved.")

            # Automatically reload the saved file after import
            self.abc_path = save_path
            try:
                with open(save_path, "rb") as f:
                    self.original_data = f.read()
            except Exception as e:
                self.show_error("Error", f"Failed to reload saved ABC file:\n{str(e)}")
                return
            # Re-run load logic
            header = self.original_data[:22]
            self.auto_offset = int.from_bytes(header[20:22], "little") * 2
            self.offset_dec = self.auto_offset + 26 # First glyph offset
            self.offset_input.setText(str(self.offset_dec))
            self.manual_offset = False
            self.extract_glyphs(self.offset_dec, manual=False)
            self.offsets_label.setText("")

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
