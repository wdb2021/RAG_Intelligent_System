from pathlib import Path
from typing import List, Union
from openai import OpenAI
from config import configInstance
from message import Message
from datetime import datetime
import json

class SummaryProcessor:
    """支持对话与文件摘要的二合一处理器"""

    def __init__(self):
        self.client = OpenAI(
            api_key=configInstance.summary_api_key,
            base_url=configInstance.summary_api_url,
            timeout=configInstance.api_timeout
        )

    # ---------- 原有对话摘要功能（保持不变） ----------
    def generate_summary(self, messages: List[Message]) -> str:
        """生成对话摘要（完全兼容原有调用）"""
        prompt = self._build_dialog_prompt(messages)
        return self._call_summary_api(prompt)

    def _build_dialog_prompt(self, messages: List[Message]) -> str:
        """构建对话提示词（保持原有逻辑）"""
        recent_dialogue = "\n".join(
            f"{msg.role}: {msg.content}"
            for msg in messages[-5:]
        )
        return f"请用最简洁的中文总结以下对话的核心内容（不超过100字）：\n{recent_dialogue}"

    # ---------- 新增文件摘要功能 ----------
    def generate_file_summary(self, file_path: Union[str, Path], max_length: int = 300) -> str:
        """
        生成文件摘要（新增功能）
        :param file_path: 文本文件路径（支持.txt/.md等）
        :param max_length: 摘要最大长度（默认300字）
        """
        try:
            content = self._read_file(file_path)
            prompt = self._build_file_prompt(content, max_length)
            return self._call_summary_api(prompt)
        except Exception as e:
            return f"摘要生成失败: {str(e)}"

    def _read_file(self, path: Union[str, Path]) -> str:
        """安全读取文本文件"""
        print("reading...")
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")
        if file_path.stat().st_size > 1_048_576:  # 1MB限制
            raise ValueError("文件大小超过1MB限制")
        return file_path.read_text(encoding='utf-8')

    def _build_file_prompt(self, content: str, max_length: int) -> str:
        """构建文件摘要提示词"""
        truncated = content[:2000]  # 限制输入长度
        return f"""请根据以下文件内容生成结构化摘要（不超过{max_length}字）：
1. 核心主题
2. 关键论点/发现
3. 重要数据/案例
4. 结论/建议

文件内容：
{truncated}"""

    # ---------- 共用核心逻辑 ----------
    def _call_summary_api(self, prompt: str) -> str:
        """统一调用摘要API"""
        response = self.client.chat.completions.create(
            model=configInstance.summary_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=configInstance.summary_temperature  # 使用原有配置
        )
        return response.choices[0].message.content

    def save_summary(self, session_id: str, summary: str):
        """保存摘要到独立文件"""
        summary_path = configInstance.summary_storage_path / f"summary_{session_id}.json"

        data = {
            "session_id": session_id,
            "summary": summary,
            "updated_at": datetime.now().isoformat()
        }
        with open(summary_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("summary saved")


    def load_summary(self, session_id: str) -> str:
        """加载最新摘要"""
        print("SYSTEMCALL_load_summary")
        summary_path = configInstance.summary_storage_path / f"summary_{session_id}.json"
        if not summary_path.exists():
            return ""
        try:
            with open(summary_path, 'r') as f:
                return json.load(f)["summary"]
        except:
            return ""
