# UI/MainWindow.py (PyQt6 版本)
import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .FileListWidget import FileListWidget
from .ProcessingWidget import ProcessingWidget
from .FontManager import FontManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoiceFlow Translator")
        self.setGeometry(100, 100, 1000, 600)
        self.results = {}
        self.current_file = None

        self.init_ui()
        self.font_manager = FontManager(self)
        self.create_menu_bar()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.file_list_widget = FileListWidget(self)
        self.processing_widget = ProcessingWidget(self)

        main_layout.addWidget(self.file_list_widget, 1)
        main_layout.addWidget(self.processing_widget, 3)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("檔案")
        file_menu.addAction("儲存語音辨識結果", self.save_transcript)
        file_menu.addAction("儲存翻譯結果", self.save_translation)
        file_menu.addSeparator()
        file_menu.addAction("結束", self.close)

        view_menu = menu_bar.addMenu("檢視")
        view_menu.addAction("放大字體 (110%)", self.font_manager.increase_font)
        view_menu.addAction("縮小字體 (90%)", self.font_manager.decrease_font)
        view_menu.addAction("重設字體", self.font_manager.reset_font)

    def save_transcript(self):
        self.processing_widget.save_transcript()

    def save_translation(self):
        self.processing_widget.save_translation()

    def update_display(self):
        self.processing_widget.update_display(self.current_file, self.results.get(self.current_file, {}))

    def resizeEvent(self, event):
        self.font_manager.resize(self.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.file_list_widget.close()
        self.processing_widget.close()  # 清理 ProcessingWidget 的 Worker
        self.results.clear()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())