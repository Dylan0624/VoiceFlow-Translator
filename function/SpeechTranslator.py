# function/SpeechTranslator.py
import re
import sys
import opencc
import whisper
from transformers import pipeline
import torch  # 用來檢查 GPU 可用性
import warnings
warnings.filterwarnings('ignore', category=UserWarning)


class SpeechTranslator:
    """
    此模組提供 SpeechTranslator 類別，具有以下功能：
      - 使用 OpenAI 的 Whisper 模型將語音轉成文字
      - 清理並分割文字句子
      - 使用 Helsinki-NLP 的 Opus MT 模型進行翻譯，支援使用者指定翻譯的原文與目標語言

    可用的 Whisper 模型（截至目前版本）：
      - "tiny"
      - "tiny.en"
      - "base"
      - "base.en"
      - "small"
      - "small.en"
      - "medium"
      - "medium.en"
      - "large"
    """

    def __init__(
        self,
        whisper_model_name="medium.en",
        translator_device=None,
        source_lang="en",
        target_lang="zh",
        target_traditional=False,
    ):
        """
        初始化 SpeechTranslator

        Args:
            whisper_model_name (str): 用於語音辨識的 Whisper 模型名稱。
            translator_device: 翻譯 pipeline 使用的裝置；若為 None 則依作業系統自動選擇。
            source_lang (str): 翻譯原文語言的語言代碼（例如 "en", "zh", "fr"）。
            target_lang (str): 翻譯目標語言的語言代碼。
            target_traditional (bool): 若為 True，且 target_lang 為 "zh"，則將輸出轉為繁體中文。
        """
        self.whisper_model_name = whisper_model_name
        self.whisper_model = whisper.load_model(self.whisper_model_name)
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.target_traditional = target_traditional

        if translator_device is None:
            if sys.platform == "darwin":
                translator_device = "mps"
            else:
                translator_device = 0 if torch.cuda.is_available() else -1

        model_name = f"Helsinki-NLP/opus-mt-{self.source_lang}-{self.target_lang}"
        self.translator = pipeline("translation", model=model_name, device=translator_device)

    def set_translation_params(
        self, source_lang="en", target_lang="zh", target_traditional=False, translator_device=None
    ):
        """
        更新翻譯參數，並重建翻譯 pipeline

        Args:
            source_lang (str): 原文語言代碼。
            target_lang (str): 目標語言代碼。
            target_traditional (bool): 是否將中文輸出轉為繁體（僅 target_lang 為 "zh" 時有效）。
            translator_device: 翻譯 pipeline 使用的裝置；若為 None 則自動選擇。
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.target_traditional = target_traditional

        if translator_device is None:
            if sys.platform == "darwin":
                translator_device = "mps"
            else:
                translator_device = 0 if torch.cuda.is_available() else -1 

        model_name = f"Helsinki-NLP/opus-mt-{self.source_lang}-{self.target_lang}"
        self.translator = pipeline("translation", model=model_name, device=translator_device)

    def speech_to_text(self, audio_file):
        """
        使用 Whisper 將音訊檔案轉為文字

        Args:
            audio_file (str): 音訊檔案的路徑。

        Returns:
            str: 辨識後的文字。
        """
        result = self.whisper_model.transcribe(audio_file)
        return result["text"]

    @staticmethod
    def clean_text(text):
        """
        清理並標準化文字（移除多餘空格、調整標點符號前空格）

        Args:
            text (str): 要清理的文字。

        Returns:
            str: 清理後的文字。
        """
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,.!?])", r"\1", text)
        return text

    def split_into_sentences(self, text):
        """
        將文字根據標點分句

        Args:
            text (str): 要分句的文字。

        Returns:
            list: 各句文字的列表。
        """
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [self.clean_text(s) for s in sentences if s.strip()]

    def translate_chunk(self, chunk):
        """
        翻譯單一文字區塊

        Args:
            chunk (str): 要翻譯的文字區塊。

        Returns:
            str: 翻譯結果；若發生錯誤則回傳原文字區塊。
        """
        try:
            result = self.translator(chunk, max_length=512)
            return result[0]["translation_text"]
        except Exception as e:
            print(f"翻譯錯誤: {str(e)}")
            print(f"問題文本: {chunk}")
            return chunk

    def post_process_chinese(self, text):
        """
        後處理中文文字（移除多餘空格、調整標點符號、添加換行）

        Args:
            text (str): 中文文字。

        Returns:
            str: 處理後的中文文字。
        """
        text = re.sub(r"\s+", "", text)
        text = text.replace(" ,", "，")
        text = text.replace(" .", "。")
        text = text.replace(" ?", "？")
        text = text.replace(" !", "！")
        text = text.replace("，", "，\n")
        text = text.replace("。", "。\n")
        text = text.replace("？", "？\n")
        text = text.replace("！", "！\n")
        return text

    def translate_text(self, input_text, batch_size=3):
        """
        將輸入文字進行翻譯，依 batch_size 分批翻譯

        Args:
            input_text (str): 要翻譯的文字。
            batch_size (int): 每批翻譯的句子數，預設為 3。

        Returns:
            str or None: 翻譯後的文字；若發生錯誤則回傳 None。
        """
        try:
            sentences = self.split_into_sentences(input_text)
            translated_parts = []

            for i in range(0, len(sentences), batch_size):
                batch = sentences[i : i + batch_size]
                batch_text = " ".join(batch)
                translation = self.translate_chunk(batch_text)
                translated_parts.append(translation)

            combined_text = "".join(translated_parts)
            if self.target_lang == "zh":
                combined_text = self.post_process_chinese(combined_text)
                if self.target_traditional:
                    converter = opencc.OpenCC("s2t")
                    combined_text = converter.convert(combined_text)
            return combined_text
        except Exception as e:
            print(f"翻譯過程發生錯誤: {str(e)}")
            return None

    @staticmethod
    def format_output(text):
        """
        格式化輸出文字，移除前後空白

        Args:
            text (str): 要格式化的文字。

        Returns:
            str: 格式化後的文字。
        """
        return text.strip()
