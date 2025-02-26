# function/ollama_client.py
import ollama
import subprocess
import time

class OllamaClient:
    """Ollama 客戶端，用於管理本地模型並生成總結"""
    # 預定義常用模型列表
    PREDEFINED_MODELS = [
        "deepseek-r1:1.5b",  # DeepSeek-R1-Distill-Qwen-1.5B
        "deepseek-r1:7b",    # DeepSeek-R1-Distill-Qwen-7B
        "deepseek-r1:8b",    # DeepSeek-R1-Distill-Llama-8B
        "deepseek-r1:14b",   # DeepSeek-R1-Distill-Qwen-14B
        "deepseek-r1:32b",   # DeepSeek-R1-Distill-Qwen-32B
        "deepseek-r1:70b",   # DeepSeek-R1-Distill-Llama-70B
        "llama3:8b",         # LLaMA 3 8B (假設常用版本)
        "qwen:7b",           # Qwen 7B (假設常用版本)
    ]

    def __init__(self, preferred_model="deepseek-r1:14b"):
        self.preferred_model = preferred_model

    def check_available_models(self):
        """檢查本地已安裝的 Ollama 模型，並返回預定義模型與本地模型的合併列表"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')[1:]  # 跳過表頭
            local_models = [line.split()[0] for line in lines if line]  # 提取本地模型名稱
        except subprocess.CalledProcessError:
            local_models = []

        # 合併預定義模型與本地模型，去除重複並排序
        all_models = sorted(set(self.PREDEFINED_MODELS + local_models))
        return all_models if all_models else ["無可用模型"]

    def pull_model(self, model_name):
        """自動拉取指定的 Ollama 模型"""
        print(f"正在下載模型 {model_name}...")
        try:
            subprocess.run(['ollama', 'pull', model_name], check=True)
            print(f"模型 {model_name} 下載完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"無法下載模型 {model_name}: {e}")
            return False

    def select_model(self, model_name):
        """選擇指定的模型，若不在本地則嘗試拉取"""
        available_models = self.check_available_models()
        
        if "無可用模型" in available_models:
            if self.pull_model(model_name):
                time.sleep(5)  # 等待模型載入
                if model_name in self.check_available_models():
                    return model_name
                return None
            return None
        
        if model_name in available_models:
            return model_name
        else:
            print(f"模型 {model_name} 未在本地找到，正在嘗試下載...")
            if self.pull_model(model_name):
                time.sleep(5)
                if model_name in self.check_available_models():
                    return model_name
            return None if "無可用模型" in available_models else available_models[0]

    def generate_summary(self, text, model_name=None):
        """使用指定的 Ollama 模型生成語音辨識內容的總結"""
        if not model_name:
            model_name = self.preferred_model
        
        selected_model = self.select_model(model_name)
        if not selected_model:
            return f"無法生成總結：模型 {model_name} 不可用或下載失敗"

        prompt = f"請總結以下語音辨識內容，保持簡潔且重點清晰：\n\n{text}"

        try:
            response = ollama.chat(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]
        except Exception as e:
            return f"總結生成失敗: {str(e)}"

if __name__ == "__main__":
    client = OllamaClient()
    print("可用模型:", client.check_available_models())
    sample_text = "今天天氣很好，我們決定去公園散步。公園裡有很多花和鳥，景色很美麗。我們還帶了一些食物，準備在那裡野餐。"
    print("\n總結:\n", client.generate_summary(sample_text))