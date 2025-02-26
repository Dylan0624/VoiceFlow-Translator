# VoiceFlow Translator

一個基於 PyQt6 開發的語音轉文字、翻譯及總結工具，支援多種語言之間的轉換與智慧總結功能。

## 功能特點

![alt text](<CleanShot 2025-02-26 at 22.13.22@2x-1.png>)

- 支援拖放或選擇音訊檔案
- 使用 OpenAI Whisper 進行語音辨識
- 支援多種 Whisper 模型（tiny 到 large）
- 多語言翻譯支援（英文、中文(簡體/繁體)、法文、西班牙文、德文）
- 支援簡繁體中文轉換
- 使用本地 Ollama 模型進行語音內容總結
- 總結結果可直接翻譯
- 可調整字體大小
- 支援匯出語音辨識、翻譯及總結結果

## 系統需求

- Python 3.8+
- CUDA 支援（可選，用於 GPU 加速）
- 足夠的磁碟空間（用於下載 Whisper 及 Ollama 模型）
- Ollama 服務（本地運行，用於總結功能）

## 安裝步驟

1. 克隆專案：
```bash
git clone https://github.com/Dylan0624/voiceflow-translator.git
cd voiceflow-translator
```

2. 安裝相依套件：
```bash
pip install -r requirements.txt
```

3. 啟動 Ollama 服務（用於總結功能）：
```bash
ollama serve
```

## 使用方法

1. 執行主程式：
```bash
python main.py
```

2. 在應用程序中：
   * 選擇或拖放音訊檔案
   * 選擇合適的 Whisper 模型
   * 選擇原始語言和目標翻譯語言
   * 點擊「語音辨識」進行語音轉文字
   * 點擊「翻譯」將辨識結果翻譯成目標語言
   * 選擇 Ollama 模型並點擊「總結語音內容」，生成總結
   * 點擊「翻譯總結」將總結翻譯成目標語言

## 支援的音訊格式

* MP3 (.mp3)
* WAV (.wav)
* M4A (.m4a)

## 注意事項

* 首次運行時會自動下載所需的 Whisper 模型文件
* 若選擇的 Ollama 模型未下載，程式會嘗試自動下載（需要網路連接）
* 翻譯功能需要網路連接，總結功能需本地 Ollama 服務運行
* GPU 加速需要安裝 CUDA 相關套件

## 授權說明

本專案採用 MIT 授權條款 - 詳見 LICENSE 文件

## 貢獻指南

歡迎提交 Issue 和 Pull Request。請確保您的程式碼符合現有的程式碼風格。

## 修改說明

1. **專案名稱**
   - 將原本的 "Speech Translation Tool" 改為 "VoiceFlow Translator"，並更新 GitHub 路徑為 voiceflow-translator。

2. **功能特點**
   - 新增「使用本地 Ollama 模型進行語音內容總結」和「總結結果可直接翻譯」，反映新增的總結功能。
   - 在語言支援中明確提到「中文(簡體/繁體)」。

3. **系統需求與安裝步驟**
   - 新增 Ollama 服務作為系統需求。
   - 在安裝步驟中加入啟動 Ollama 服務的指令。

4. **使用方法**
   - 更新使用說明，包含總結和總結翻譯的操作步驟。

5. **依賴更新**
   - 在 requirements.txt 中新增 ollama>=0.1.0，確保總結功能的依賴明確。