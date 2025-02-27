# UI/FontManager.py
from PyQt6.QtGui import QFont
import sys

class FontManager:
    def __init__(self, parent):
        self.parent = parent
        self.font_scale = 1
        self.base_font_size = parent.height() // 50
        self.current_font_size = int(self.base_font_size * self.font_scale)
        self.font_family = "Microsoft JhengHei" if sys.platform.startswith("win") else "Helvetica Neue" if sys.platform == "darwin" else "Arial"
        self.update_font()

    def increase_font(self):
        self.font_scale *= 1.1
        self.update_font()

    def decrease_font(self):
        self.font_scale *= 0.9
        self.update_font()

    def reset_font(self):
        self.font_scale = 1.0
        self.update_font()

    def resize(self, height):
        self.base_font_size = height // 50
        self.update_font()

    def update_font(self):
        self.current_font_size = int(self.base_font_size * self.font_scale)
        font = QFont(self.font_family, self.current_font_size)
        self.parent.file_list_widget.set_font(font)
        self.parent.processing_widget.set_font(font)