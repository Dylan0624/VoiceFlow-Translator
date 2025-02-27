# UI/ProcessingWidget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTextEdit, QFileDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from function.SpeechTranslator import SpeechTranslator
from UI.DownloadDialog import DownloadDialog

class Worker(QThread):
    finished = pyqtSignal(object)
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

class ProcessingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.speech_translator = None
        self.lang_mapping = {"英文": "en", "中文(簡體)": "zh", "中文": "zh", "中文(繁體)": "zh", "法文": "fr", "西班牙文": "es", "德文": "de"}
        self.current_worker = None  # 用於追蹤當前運行中的 Worker
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        file_layout = QHBoxLayout()
        self.drag_drop_label = QLabel("拖曳音訊檔案到此區域")
        self.drag_drop_label.setMinimumHeight(50)
        self.drag_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_drop_label.setStyleSheet("QLabel { border: 2px dashed #aaa; }")
        file_layout.addWidget(self.drag_drop_label)

        self.select_file_button = QPushButton("選取檔案")
        self.select_file_button.clicked.connect(self.parent.file_list_widget.open_file_dialog)
        file_layout.addWidget(self.select_file_button)
        layout.addLayout(file_layout)

        model_layout = QHBoxLayout()
        self.model_label = QLabel("選擇語音辨識模型:")
        model_layout.addWidget(self.model_label)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large"])
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        translation_lang_layout = QHBoxLayout()
        self.source_lang_label = QLabel("原文語言:")
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["英文", "中文(簡體)", "中文", "法文", "西班牙文", "德文"])
        self.source_lang_combo.setCurrentText("英文")
        translation_lang_layout.addWidget(self.source_lang_label)
        translation_lang_layout.addWidget(self.source_lang_combo)

        self.target_lang_label = QLabel("翻譯目標語言:")
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["中文(繁體)", "英文", "中文", "法文", "西班牙文", "德文"])
        self.target_lang_combo.setCurrentText("中文(繁體)")
        translation_lang_layout.addWidget(self.target_lang_label)
        translation_lang_layout.addWidget(self.target_lang_combo)
        layout.addLayout(translation_lang_layout)

        self.transcribe_button = QPushButton("語音辨識")
        self.transcribe_button.clicked.connect(self.perform_transcription)
        layout.addWidget(self.transcribe_button)

        self.transcription_text_edit = QTextEdit()
        self.transcription_text_edit.setPlaceholderText("語音辨識結果 (原文) 將顯示於此...")
        layout.addWidget(self.transcription_text_edit)

        self.translate_button = QPushButton("翻譯")
        self.translate_button.clicked.connect(self.perform_translation)
        layout.addWidget(self.translate_button)

        self.translation_text_edit = QTextEdit()
        self.translation_text_edit.setPlaceholderText("翻譯結果將顯示於此...")
        layout.addWidget(self.translation_text_edit)

        summary_layout = QHBoxLayout()
        self.summary_model_label = QLabel("選擇總結模型:")
        summary_layout.addWidget(self.summary_model_label)

        self.summary_model_combo = QComboBox()
        self.load_ollama_models()
        summary_layout.addWidget(self.summary_model_combo)

        self.summarize_button = QPushButton("總結語音內容")
        self.summarize_button.clicked.connect(self.perform_summarization)
        summary_layout.addWidget(self.summarize_button)

        self.translate_summary_button = QPushButton("翻譯總結")
        self.translate_summary_button.clicked.connect(self.perform_summary_translation)
        summary_layout.addWidget(self.translate_summary_button)
        layout.addLayout(summary_layout)

        self.summary_text_edit = QTextEdit()
        self.summary_text_edit.setPlaceholderText("總結結果將顯示於此（可能為簡體中文，建議將原文語言設為中文(簡體)）...")
        layout.addWidget(self.summary_text_edit)

    def load_ollama_models(self):
        models = self.parent.file_list_widget.ollama_client.check_available_models()
        self.summary_model_combo.clear()
        self.summary_model_combo.addItems(models)

    def perform_transcription(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "警告", "正在處理中，請稍候。")
            return
        file_path = self.parent.file_list_widget.file_paths[0] if self.parent.file_list_widget.file_paths else None
        if not file_path:
            self.transcription_text_edit.setPlainText("請先選擇或拖曳一個音訊檔案。")
            return
        self.speech_translator = SpeechTranslator(whisper_model_name=self.model_combo.currentText())
        self.run_worker(self.speech_translator.speech_to_text, file_path, result_key="transcription", process_name="語音辨識")

    def perform_translation(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "警告", "正在處理中，請稍候。")
            return
        if not self.speech_translator:
            self.translation_text_edit.setPlainText("請先進行語音辨識。")
            return
        text = self.transcription_text_edit.toPlainText().strip()
        if not text:
            self.translation_text_edit.setPlainText("沒有可翻譯的文字。")
            return
        self.set_translation_params()
        self.run_worker(self.speech_translator.translate_text, text, result_key="translation", process_name="翻譯")

    def perform_summarization(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "警告", "正在處理中，請稍候。")
            return
        text = self.transcription_text_edit.toPlainText().strip()
        if not text:
            self.summary_text_edit.setPlainText("請先進行語音辨識以提供內容。")
            return
        model_name = self.summary_model_combo.currentText()
        self.run_worker(self.parent.file_list_widget.ollama_client.generate_summary, text, model_name, result_key="summary", process_name="總結")

    def perform_summary_translation(self):
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "警告", "正在處理中，請稍候。")
            return
        if not self.speech_translator:
            self.summary_text_edit.setPlainText("請先進行語音辨識並生成總結。")
            return
        text = self.summary_text_edit.toPlainText().strip()
        if not text or text in ["正在生成總結...", "請先進行語音辨識以提供內容。"]:
            self.summary_text_edit.setPlainText("沒有可翻譯的總結內容。")
            return
        self.set_translation_params()
        self.run_worker(self.speech_translator.translate_text, text, result_key="summary", process_name="總結翻譯")

    def run_worker(self, fn, *args, result_key, process_name):
        text_edit = {
            "transcription": self.transcription_text_edit,
            "translation": self.translation_text_edit,
            "summary": self.summary_text_edit
        }[result_key]
        text_edit.setPlainText(f"正在{process_name}...")
        self.current_worker = Worker(fn, *args)
        self.current_worker.finished.connect(lambda result: self.on_finished(result, result_key))
        self.current_worker.error.connect(lambda error: self.on_error(error, result_key))
        self.current_worker.finished.connect(self.clear_worker)  # 清理完成後的 Worker
        self.current_worker.start()

    def on_finished(self, result, result_key):
        text_edit = {
            "transcription": self.transcription_text_edit,
            "translation": self.translation_text_edit,
            "summary": self.summary_text_edit
        }[result_key]
        if result_key == "summary" and isinstance(result, str) and "model" in result and "not found" in result:
            model_name = self.summary_model_combo.currentText()
            reply = QMessageBox.question(
                self, "模型不可用",
                f"模型 '{model_name}' 未在本地找到。是否要下載該模型？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog = DownloadDialog(model_name, self.parent.file_list_widget.ollama_client, self)
                dialog.exec()
                self.load_ollama_models()
                if model_name in self.parent.file_list_widget.ollama_client.check_available_models():
                    self.perform_summarization()
                else:
                    text_edit.setPlainText(f"模型 {model_name} 下載失敗，無法進行總結。")
            else:
                text_edit.setPlainText("請選擇一個已安裝的模型或下載新模型。")
        else:
            text_edit.setPlainText(result)
            if self.parent.current_file:
                self.parent.results.setdefault(self.parent.current_file, {})[result_key] = result
            if result_key == "transcription":
                self.translation_text_edit.clear()
                self.summary_text_edit.clear()

    def on_error(self, error, result_key):
        text_edit = {
            "transcription": self.transcription_text_edit,
            "translation": self.translation_text_edit,
            "summary": self.summary_text_edit
        }[result_key]
        text_edit.setPlainText(f"{result_key.capitalize()}發生錯誤: {str(error)}")

    def set_translation_params(self):
        source_lang = self.lang_mapping.get(self.source_lang_combo.currentText(), "en")
        target_lang_text = self.target_lang_combo.currentText()
        target_traditional = target_lang_text == "中文(繁體)"
        target_lang = self.lang_mapping.get(target_lang_text, "zh") if target_lang_text in ["中文(繁體)", "中文"] else self.lang_mapping.get(target_lang_text, "en")
        self.speech_translator.set_translation_params(source_lang, target_lang, target_traditional)

    def save_transcript(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "儲存語音辨識結果", "", "文字檔案 (*.txt);;所有檔案 (*)")
        if file_name:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.transcription_text_edit.toPlainText())

    def save_translation(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "儲存翻譯結果", "", "文字檔案 (*.txt);;所有檔案 (*)")
        if file_name:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.translation_text_edit.toPlainText())

    def update_display(self, current_file, result):
        self.transcription_text_edit.setPlainText(result.get("transcription", ""))
        self.translation_text_edit.setPlainText(result.get("translation", ""))
        self.summary_text_edit.setPlainText(result.get("summary", ""))

    def set_font(self, font):
        self.drag_drop_label.setFont(font)
        self.select_file_button.setFont(font)
        self.transcribe_button.setFont(font)
        self.translate_button.setFont(font)
        self.summarize_button.setFont(font)
        self.translate_summary_button.setFont(font)
        self.model_combo.setFont(font)
        self.source_lang_combo.setFont(font)
        self.target_lang_combo.setFont(font)
        self.summary_model_combo.setFont(font)
        self.model_label.setFont(font)
        self.source_lang_label.setFont(font)
        self.target_lang_label.setFont(font)
        self.summary_model_label.setFont(font)
        self.transcription_text_edit.setFont(font)
        self.translation_text_edit.setFont(font)
        self.summary_text_edit.setFont(font)

    def clear_worker(self):
        self.current_worker = None  # 清理完成的 Worker

    def close(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.quit()
            self.current_worker.wait()