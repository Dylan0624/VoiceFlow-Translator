# UI/FileListWidget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from function.SpeechTranslator import SpeechTranslator
from function.ollama_client import OllamaClient
import os

class BatchProcessor(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    result = pyqtSignal(str, str, object)
    error = pyqtSignal(str, str, Exception)

    def __init__(self, files, fn, result_key, extra_args_func=None):
        super().__init__()
        self.files = files
        self.fn = fn
        self.result_key = result_key
        self.extra_args_func = extra_args_func
        self.is_running = True

    def run(self):
        for i, file_path in enumerate(self.files, 1):
            if not self.is_running:
                break
            self.progress.emit(i, file_path)
            try:
                args = [file_path] if self.result_key == "transcription" else [self.extra_args_func(file_path)] + ([] if not self.extra_args_func else self.extra_args_func(file_path)[1:])
                result = self.fn(*args)
                self.result.emit(file_path, self.result_key, result)
            except Exception as e:
                self.error.emit(file_path, self.result_key, e)
        self.finished.emit()

    def stop(self):
        self.is_running = False

class FileListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.speech_translator = None
        self.ollama_client = OllamaClient(preferred_model="deepseek-r1:14b")
        self.file_paths = []
        self.batch_processor = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("檔案列表"))
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.on_file_selected)
        layout.addWidget(self.file_list)

        file_buttons = QHBoxLayout()
        self.add_files_button = QPushButton("新增檔案")
        self.add_files_button.clicked.connect(self.open_file_dialog)
        file_buttons.addWidget(self.add_files_button)

        self.clear_list_button = QPushButton("清空列表")
        self.clear_list_button.clicked.connect(self.clear_file_list)
        file_buttons.addWidget(self.clear_list_button)
        layout.addLayout(file_buttons)

        batch_buttons = QVBoxLayout()
        self.batch_transcribe_button = QPushButton("依序轉換")
        self.batch_transcribe_button.clicked.connect(self.batch_transcribe)
        batch_buttons.addWidget(self.batch_transcribe_button)

        self.batch_translate_button = QPushButton("依序翻譯")
        self.batch_translate_button.clicked.connect(self.batch_translate)
        batch_buttons.addWidget(self.batch_translate_button)

        self.batch_summarize_button = QPushButton("依序總結")
        self.batch_summarize_button.clicked.connect(self.batch_summarize)
        batch_buttons.addWidget(self.batch_summarize_button)

        self.stop_batch_button = QPushButton("停止批次處理")
        self.stop_batch_button.clicked.connect(self.stop_batch)
        self.stop_batch_button.setEnabled(False)
        batch_buttons.addWidget(self.stop_batch_button)

        self.batch_status_label = QLabel("批次處理狀態：閒置")
        batch_buttons.addWidget(self.batch_status_label)
        layout.addLayout(batch_buttons)

    def open_file_dialog(self):
        file_names, _ = QFileDialog.getOpenFileNames(
            self, "選擇音訊檔案", os.path.dirname(os.path.dirname(__file__)), "音訊檔案 (*.m4a *.mp3 *.wav);;所有檔案 (*)"
        )
        if file_names:
            self.file_paths.extend(file_names)
            self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        for i, file_path in enumerate(self.file_paths, 1):
            item = QListWidgetItem(f"{i}. {os.path.basename(file_path)}")
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.file_list.addItem(item)

    def clear_file_list(self):
        self.file_paths.clear()
        self.parent.results.clear()
        self.file_list.clear()
        self.parent.current_file = None
        self.parent.update_display()
        self.batch_status_label.setText("批次處理狀態：閒置")

    def on_file_selected(self, item):
        self.parent.current_file = item.data(Qt.ItemDataRole.UserRole)
        self.parent.update_display()

    def batch_transcribe(self):
        if not self.file_paths:
            QMessageBox.warning(self, "警告", "請先載入音訊檔案。")
            return
        self.speech_translator = SpeechTranslator(whisper_model_name=self.parent.processing_widget.model_combo.currentText())
        self.start_batch(self.speech_translator.speech_to_text, "transcription")

    def batch_translate(self):
        if not self.file_paths or not self.speech_translator:
            QMessageBox.warning(self, "警告", "請先進行語音轉換。")
            return
        self.parent.processing_widget.set_translation_params()
        self.start_batch(self.speech_translator.translate_text, "translation", lambda fp: [self.parent.results.get(fp, {}).get("transcription", "")])

    def batch_summarize(self):
        if not self.file_paths:
            QMessageBox.warning(self, "警告", "請先進行語音轉換以提供內容。")
            return
        self.start_batch(self.ollama_client.generate_summary, "summary", lambda fp: [self.parent.results.get(fp, {}).get("transcription", ""), self.parent.processing_widget.summary_model_combo.currentText()])

    def start_batch(self, fn, result_key, extra_args_func=None):
        if self.batch_processor and self.batch_processor.isRunning():
            QMessageBox.warning(self, "警告", "已有批次處理任務在執行中。")
            return
        self.batch_processor = BatchProcessor(self.file_paths, fn, result_key, extra_args_func)
        self.batch_processor.progress.connect(self.on_batch_progress)
        self.batch_processor.result.connect(self.on_batch_result)
        self.batch_processor.error.connect(self.on_batch_error)
        self.batch_processor.finished.connect(self.on_batch_finished)
        self.batch_status_label.setText(f"批次處理狀態：開始 ({result_key})")
        self.set_batch_buttons_enabled(False)
        self.batch_processor.start()

    def on_batch_progress(self, index, file_path):
        self.batch_status_label.setText(f"批次處理狀態：處理中 {index}/{len(self.file_paths)}")
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                item.setText(f"{index}. {os.path.basename(file_path)} (處理中)")
                break

    def on_batch_result(self, file_path, result_key, result):
        self.parent.results.setdefault(file_path, {})[result_key] = result
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                item.setText(f"{i+1}. {os.path.basename(file_path)}")
                break
        if file_path == self.parent.current_file:
            self.parent.update_display()

    def on_batch_error(self, file_path, result_key, error):
        self.parent.results.setdefault(file_path, {})[result_key] = f"處理錯誤: {str(error)}"
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                item.setText(f"{i+1}. {os.path.basename(file_path)} (錯誤)")
                break
        if file_path == self.parent.current_file:
            self.parent.update_display()

    def on_batch_finished(self):
        self.batch_status_label.setText("批次處理狀態：完成")
        self.set_batch_buttons_enabled(True)
        self.update_file_list()

    def stop_batch(self):
        if self.batch_processor and self.batch_processor.isRunning():
            self.batch_processor.stop()
            self.batch_status_label.setText("批次處理狀態：已停止")
            self.set_batch_buttons_enabled(True)

    def set_batch_buttons_enabled(self, enabled):
        self.batch_transcribe_button.setEnabled(enabled)
        self.batch_translate_button.setEnabled(enabled)
        self.batch_summarize_button.setEnabled(enabled)
        self.stop_batch_button.setEnabled(not enabled)

    def close(self):
        if self.batch_processor and self.batch_processor.isRunning():
            self.batch_processor.stop()
            self.batch_processor.wait()

    def set_font(self, font):
        self.file_list.setFont(font)
        self.add_files_button.setFont(font)
        self.clear_list_button.setFont(font)
        self.batch_transcribe_button.setFont(font)
        self.batch_translate_button.setFont(font)
        self.batch_summarize_button.setFont(font)
        self.stop_batch_button.setFont(font)
        self.batch_status_label.setFont(font)