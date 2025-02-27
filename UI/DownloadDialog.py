# UI/DownloadDialog.py 
import subprocess
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

class Worker(QThread):
    finished = pyqtSignal(bool)
    error = pyqtSignal(Exception)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)

class DownloadDialog(QDialog):
    def __init__(self, model_name, ollama_client, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"下載模型: {model_name}")
        self.setMinimumSize(300, 150)
        self.setModal(True)  # 設定為模態對話框，避免與主窗口互動
        self.ollama_client = ollama_client
        self.model_name = model_name
        self.completed = False

        self.init_ui()
        self.start_download()

    def init_ui(self):
        # 佈局
        layout = QVBoxLayout()

        # 進度條
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 取消按鈕
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        # 定時器模擬進度（若有真實進度可替換）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # 每 100 毫秒更新一次

    def start_download(self):
        # 在工作執行緒中啟動下載
        self.worker = Worker(self.ollama_client.pull_model, self.model_name)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_download_error)
        self.worker.start()

    def update_progress(self):
        """模擬進度更新，若 ollama 提供真實進度可替換此邏輯"""
        if self.completed:
            self.timer.stop()
            self.accept()  # 下載完成後關閉對話框
            return
        current_value = self.progress_bar.value()
        if current_value < 95:  # 保持低於 100，直到完成
            self.progress_bar.setValue(current_value + 1)

    def on_download_finished(self, success):
        self.completed = True
        self.progress_bar.setValue(100)
        if not success:
            QMessageBox.warning(self, "下載失敗", f"無法下載模型 {self.model_name}。")

    def on_download_error(self, error):
        self.completed = True
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "錯誤", f"下載模型時發生錯誤: {str(error)}")
        self.reject()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    from function.ollama_client import OllamaClient  # 假設路徑正確
    app = QApplication(sys.argv)
    client = OllamaClient()
    dialog = DownloadDialog("test-model", client)
    dialog.exec()
    sys.exit(app.exec())