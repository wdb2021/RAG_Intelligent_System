"""
session_manager.py - 多用户会话管理
功能：
1. 创建/删除会话实例
2. 管理会话历史存储
3. 提供会话选择接口
"""

import json
from message import Message
from pathlib import Path
from typing import Dict, List
from config import configInstance
from datetime import datetime

class SessionManager:
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = Path(session_dir)
        self.sessions: Dict[str, list] = {}  # 改为存储原生列表（原：ChatMessageHistory）
        self.active_session = None
        # 初始化时加载已有会话
        self._load_sessions()

    def _ensure_dir(self):
        """确保存储目录存在"""
        self.session_dir.mkdir(exist_ok=True, parents=True)

    def _load_sessions(self):
        """加载所有历史会话（严格校验一致性）"""
        self._ensure_dir()
        for file in self.session_dir.glob("session_*.json"):
            # 从文件名提取 session_id
            file_session_id = file.stem.split("_")[1]

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data_session_id = data.get("session_id")

                # 校验一致性
                if file_session_id != data_session_id:
                    print(
                        f"警告: 文件 {file.name} 的 session_id 不匹配（文件ID: {file_session_id}, 数据ID: {data_session_id}），已跳过")
                    continue

                # 加载消息
                messages = [
                    Message(role=msg["role"], content=msg["content"])
                    for msg in data["messages"]
                ]
                self.sessions[file_session_id] = messages

    def _save_session(self, session_id: str):
        """保存会话到文件（原子化写入）"""
        self._ensure_dir()
        temp_file = self.session_dir / f"temp_{session_id}.json"
        target_file = self.session_dir / f"session_{session_id}.json"

        try:
            messages = self.sessions[session_id]
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "session_id": session_id,
                        "messages": [m.to_dict() for m in messages]
                    },
                    f,
                    ensure_ascii=False,  # 显示可读中文
                    indent=2
                )
            temp_file.replace(target_file)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def create_session(self, session_id: str):
        """创建新会话并持久化（防文件冲突）"""
        if session_id in self.sessions:
            raise ValueError(f"会话 {session_id} 已存在")

        # 检查文件是否已存在
        target_file = self.session_dir / f"session_{session_id}.json"
        if target_file.exists():
            raise FileExistsError(f"会话文件 {target_file} 已存在，请选择不同ID")

        self.sessions[session_id] = []
        self._save_session(session_id)

    def save_session(self, session_id: str):
        """安全保存方法（防止循环触发）"""
        if session_id not in self.sessions:
            raise KeyError(f"无效会话ID: {session_id}")

        # 添加循环触发防护
        if not hasattr(self, '_saving'):
            self._saving = True
            try:
                self._save_session(session_id)
                print(f"会话 {session_id} 保存完成")
            finally:
                del self._saving

    def delete_session(self, session_id: str):
        """删除会话及其存储文件"""
        if session_id not in self.sessions:
            return

        file_path = self.session_dir / f"session_{session_id}.json"
        if file_path.exists():
            file_path.unlink(missing_ok=True) #静默处理，支持并发

        del self.sessions[session_id]
        if self.active_session == session_id:
            self.active_session = None

    def list_sessions(self) -> List[str]:
        """获取所有会话ID"""
        return list(self.sessions.keys())

    def get_history(self, session_id: str) -> "HistoryWrapper":
        # 显式传递session_id到闭包
        def save_closure():
            self._save_session(session_id)  # ✅ 正确捕获当前session_id

        return HistoryWrapper(
            messages=self.sessions[session_id],
            save_fn=save_closure  # 🚩 使用闭包替代lambda
            # save_fn=lambda: self.   _save_session(session_id)
        )

    def set_active(self, session_id: str) -> None:
        """设置当前活动会话"""
        if session_id in self.sessions:
            self.active_session = session_id
        else:
            print("会话不存在")

    def get_active_history(self) -> list:
        """获取当前活动会话的历史存储"""
        print("SYSTEMCALL_get_history")
        return self.sessions.get(self.active_session, [])

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


class HistoryWrapper:
    """带自动保存功能的包装器（添加批量添加消息支持）"""

    def __init__(self, messages: list, save_fn: callable):
        self.messages = messages
        self._save_fn = save_fn  # 保存闭包

    def add_message(self, message: Message):
        """添加单条消息"""
        if not isinstance(message, Message):
            raise TypeError(f"必须使用 Message 类型，实际传入: {type(message)}")
        self.messages.append(message)
        self._save_fn()
        print(f"【添加消息】角色: {message.role}")

    def add_messages(self, messages: list):
        """批量添加消息"""
        for msg in messages:
            if not isinstance(msg, Message):
                raise TypeError(f"消息必须为 Message 类型，实际类型: {type(msg)}")
            self.messages.append(msg)
        self._save_fn()
        print(f"【批量添加】共 {len(messages)} 条消息")

    def clear(self):
        """清空消息历史"""
        self.messages.clear()
        self._save_fn()

    def manual_save(self):
        """手动触发保存"""
        self._save_fn()
