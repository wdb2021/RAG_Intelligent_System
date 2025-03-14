# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

class AppConfig:
    """统一应用程序配置（支持会话管理/OpenAI/交互界面）"""

    def __init__(self):
        load_dotenv(override=True)

        # main model 配置
        self.openai_api_key = self._get_required("OPENAI_API_KEY")
        self.model_api_url = self._get_required("OPENAI_API_URL")
        self.model_type = self._get_required("MAIN_MODEL")
        self.api_timeout = float(os.getenv("TIMEOUT", "30.0"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))

        # 摘要模型配置（新增）
        self.summary_api_key = self._get_required("SUMMARY_API_KEY")
        self.summary_api_url = self._get_required("SUMMARY_API_URL")
        self.summary_model = self._get_required("SUMMARY_MODEL")
        self.summary_temperature = float(os.getenv("SUMMARY_TEMPERATURE", "0.2"))

        # 会话管理配置
        self.session_storage_path = self._get_path("SESSION_STORAGE_PATH", "./sessions")
        self.summary_storage_path = self._get_path("SUMMARY_STORAGE_PATH", "./summaries")

        # 交互界面配置
        self.ai_prefix = os.getenv("AI_PREFIX", "助手")
        self.user_prefix = os.getenv("USER_PREFIX", "用户")
        self.enable_stream_mode = os.getenv("ENABLE_STREAM_MODE", "true").lower() == "true"

    def _get_required(self, key: str) -> str:
        """获取必需配置项"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"必需配置项缺失: {key}")
        return value

    def _get_path(self, key: str, default: str) -> Path:
        """获取路径配置（自动创建目录）"""
        path_str = os.getenv(key, default)
        path = Path(path_str).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

# 初始化配置实例
configInstance = AppConfig()

if __name__ == "__main__":
    # 打印配置验证结果
    print("配置验证通过 ✅")
    print(configInstance)
    print("After load:", os.getenv("MAIN_MODEL"))
    print("After load:", os.getenv("SUMMARY_MODEL"))
