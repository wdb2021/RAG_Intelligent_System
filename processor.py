# processor.py
from typing import Generator

from future.backports.http.client import responses
from openai import OpenAI
from message import Message
from config import configInstance
import threading
from session_manager import SessionManager

class ChatProcessor:
    """对话处理引擎（完全配置驱动）"""

    def __init__(self):
        self.client = OpenAI(
            api_key=configInstance.openai_api_key,
            base_url=configInstance.model_api_url,
            timeout=configInstance.api_timeout
        )
        # 摘要处理器
        self.summary_client = OpenAI(
            api_key=configInstance.summary_api_key,
            base_url=configInstance.summary_api_url,
            timeout=configInstance.api_timeout
        )

    def process(self, session_mgr, session_id: str, text: str) -> str:
        """同步处理消息 (响应生成后才能看到结果)"""
        context = self._build_context(session_mgr, session_id, text)

        try:
            # 直接获取内容字符串而非响应对象
            response_content = self._get_response(context, stream=False)

            # 安全保存（使用字符串而非对象）
            self._save_history(session_mgr, session_id, text, response_content)

            # 异步更新摘要（保持原有逻辑）
            self._async_update_summary(session_mgr, session_id)
            return response_content

        except Exception as e:
            # 新增异常回滚（防止脏数据）
            session_mgr.rollback(session_id)
            raise RuntimeError(f"处理失败: {str(e)}")

    def stream(self, session_mgr, session_id: str, text: str) -> Generator[str, None, None]:
        """流式处理消息 (实时响应)"""
        context = self._build_context(session_mgr, session_id, text)
        stream = self._get_response(context, stream=True)

        full_response = []
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_response.append(content)
                yield content

        self._save_history(session_mgr, session_id, text, "".join(full_response))
        self._async_update_summary(session_mgr, session_id)  # 新增异步调用摘要处理器

    def _build_context(self, session_mgr, session_id: str, text: str) -> list:
        """构建符合 OpenAI 格式的上下文"""
        return [
            {"role": "system", "content": "你是一个知识渊博的助手"},
            *[msg.to_openai_format() for msg in session_mgr.get_history(session_id).messages],
            {"role": "user", "content": text}
        ]

    def _get_response(self, messages: list, stream: bool):
        """调用 OpenAI API（统一入口）"""
        response = self.client.chat.completions.create(
            model=configInstance.model_type,
            messages=messages,
            temperature=configInstance.temperature,
            stream=stream
        )
        if not stream:
            # 同步调用返回内容字符串
            return response.choices[0].message.content
        else:
            # 流式调用返回原始生成器
            return response

    def _save_history(self, session_mgr, session_id: str, user_input: str, ai_response: str):
        """保存对话记录到会话管理器"""
        history = session_mgr.get_history(session_id)
        history.add_messages([
            Message(role="user", content=user_input),
            Message(role="assistant", content=ai_response)
        ])

    # 新增摘要更新
    def _async_update_summary(self, session_mgr, session_id: str):
        """异步摘要更新"""
        def update_task():
            try:
                # 独立获取历史副本（不修改原历史）
                history_copy = [msg.copy() for msg in session_mgr.get_history(session_id).messages]

                prompt = f"请总结以下对话：\n{self._format_messages(history_copy[-5:])}"

                # 使用独立客户端调用
                summary = self.summary_client.chat.completions.create(
                    model=configInstance.summary_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=configInstance.temperature
                ).choices[0].message.content
                session_mgr.save_summary(session_id, summary)

            except Exception as e:
                print(f"摘要更新失败: {str(e)}")

        threading.Thread(target=update_task).start()

    def _format_messages(self, messages: list) -> str:
        """辅助格式化方法"""
        return "\n".join(f"{msg.role}: {msg.content}" for msg in messages)
