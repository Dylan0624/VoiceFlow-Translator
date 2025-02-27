# function/ollama_client.py
import ollama
import subprocess
import time

class OllamaClient:
    PREDEFINED_MODELS = [
        "deepseek-r1:1.5b", "deepseek-r1:7b", "deepseek-r1:8b", "deepseek-r1:14b",
        "deepseek-r1:32b", "deepseek-r1:70b", "llama3:8b", "qwen:7b",
    ]

    def __init__(self, preferred_model="deepseek-r1:14b"):
        self.preferred_model = preferred_model

    def check_available_models(self):
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')[1:]
            local_models = [line.split()[0] for line in lines if line]
        except subprocess.CalledProcessError:
            local_models = []
        all_models = sorted(set(self.PREDEFINED_MODELS + local_models))
        return all_models if all_models else ["無可用模型"]

    def pull_model(self, model_name):
        print(f"正在下載模型 {model_name}...")
        try:
            subprocess.run(['ollama', 'pull', model_name], check=True)
            print(f"模型 {model_name} 下載完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"無法下載模型 {model_name}: {e}")
            return False

    def select_model(self, model_name):
        available_models = self.check_available_models()
        if "無可用模型" in available_models or model_name not in available_models:
            return None
        return model_name

    def generate_summary(self, text, model_name=None):
        if not model_name:
            model_name = self.preferred_model
        selected_model = self.select_model(model_name)
        if not selected_model:
            return f"無法生成總結：模型 {model_name} 不可用，請先下載"
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