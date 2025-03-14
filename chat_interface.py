"""
chat_interface.py - 完整的对话接口实现
"""

from pathlib import Path
from typing import Generator
from config import configInstance
from message import Message
from session_manager import SessionManager
from processor import ChatProcessor
from summary_processor import SummaryProcessor


class ChatInterface:
    def __init__(self, session_manager: SessionManager,
                 processor: ChatProcessor,
                 summary_processor: SummaryProcessor,):
        """
        初始化对话接口
        :param session_manager: 会话管理实例
        :param processor: AI 处理引擎
        """
        self.session_mgr = session_manager
        self.processor = processor
        self.summary_processor = summary_processor

        self.stream_mode = configInstance.enable_stream_mode
        self.ai_prefix = configInstance.ai_prefix
        self.user_prefix = configInstance.user_prefix

        # 命令映射（支持完整形式和简写）
        self.command_map = {
            # 会话管理
            "create": self._create_session, "c": self._create_session,
            "delete": self._delete_session, "d": self._delete_session,
            "switch": self._switch_session, "s": self._switch_session,
            # 数据操作
            "list": self._list_sessions, "l": self._list_sessions,
            "save": self._save_session, "sv": self._save_session,
            # 系统控制
            "exit": self._exit, "e": self._exit,
            "help": self._show_help, "h": self._show_help,
            # 新增文件处理命令
            "read": self._handle_read, "r": self._handle_read,
        }

    def run(self):
        """主运行循环"""
        self._show_welcome()

        while True:
            try:
                self._show_status()
                user_input = input(f"{self.user_prefix} > ").strip()

                if user_input.startswith("/"):
                    self._handle_command(user_input[1:])
                else:
                    self._process_message(user_input)

            except KeyboardInterrupt:
                self._handle_interrupt()
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")

    # ----------------- 核心功能 -----------------
    def _process_message(self, text: str):
        """处理用户消息"""
        if not self._validate_active_session():
            return

        try:
            if self.stream_mode:
                self._handle_stream_response(text)
            else:
                self._handle_sync_response(text)
        except Exception as e:
            print(f"\n⚠️ 处理失败: {str(e)}")
            self._auto_save_session()

    def _handle_stream_response(self, text: str):
        """处理流式响应"""
        session_id = self.session_mgr.active_session
        print(f"{self.ai_prefix} > ", end="", flush=True)
        response_chunks = []

        try:
            # 调用处理器的流式接口
            for chunk in self.processor.stream(self.session_mgr, session_id, text):
                print(chunk, end="", flush=True)
                response_chunks.append(chunk)
        finally:
            # 确保保存完整响应
            print("\n" + "-"*40)

    def _handle_sync_response(self, text: str):
        """处理同步响应"""
        session_id = self.session_mgr.active_session
        response = self.processor.process(self.session_mgr, session_id, text)
        print(f"\n{self.ai_prefix} > {response}\n{'─'*40}")

    # ----------------- 会话管理 -----------------
    def _validate_active_session(self) -> bool:
        """验证当前是否有活跃会话"""
        if not self.session_mgr.active_session:
            print("\n⚠️ 请先创建或选择会话（使用 /create 或 /switch）")
            return False
        return True

    def _auto_save_session(self):
        """自动保存当前会话"""
        if self.session_mgr.active_session:
            self.session_mgr.save_session(self.session_mgr.active_session)


    # ----------------- 用户界面 -----------------
    def _show_welcome(self):
        """显示欢迎信息"""
        print(f"\n{'='*40}")
        print(f"🌟 {self.user_prefix}/{self.ai_prefix} 智能对话系统")
        print(f"📂 会话存储路径: {configInstance.session_storage_path}")
        print(f"🚀 当前模式: {'流式' if self.stream_mode else '同步'}")
        print("="*40)
        self._show_help([])

    def _show_status(self):
        """显示当前会话状态"""
        active_session = self.session_mgr.active_session or "无"
        sessions = self.session_mgr.list_sessions()
        print(f"\n🔍 当前会话: {active_session}")
        print(f"📜 可用会话({len(sessions)}): {', '.join(sessions) or '无'}")

    def _show_help(self, _):
        """显示帮助信息"""
        help_text = f"""
        🆘 命令帮助（[]内为简写）:
        /create [/c] <名称>  创建新会话
        /switch [/s] <名称>  切换会话
        /delete [/d] <名称>  删除会话
        /list   [/l]        列出所有会话
        /save   [/sv]       保存当前会话
        /exit   [/e]        退出系统
        /help   [/h]        显示本帮助
        /read [address] [/r] 获取外部知识库
        """
        print(help_text)

    # ----------------- 命令处理 -----------------
    def _handle_command(self, cmd: str):
        """处理用户命令"""
        lower_cmd = cmd.lower().strip()
        parts = lower_cmd.split(maxsplit=1)
        cmd_key = parts[0]
        args = parts[1].split() if len(parts) > 1 else []

        handler = self.command_map.get(cmd_key, self._invalid_command)
        handler(args)

    def _create_session(self, args):
        """创建会话 /create [/c]"""
        if not args:
            raise ValueError("缺少会话名称\n用法: /create <名称> 或简写 /c <名称>")
        self.session_mgr.create_session(args[0])
        self.session_mgr.set_active(args[0])
        print(f"\n✅ 已创建会话: {args[0]}")

    def _switch_session(self, args):
        """切换会话 /switch [/s]"""
        if not args:
            raise ValueError("缺少会话名称\n用法: /switch <名称> 或简写 /s <名称>")
        self.session_mgr.set_active(args[0])
        print(f"\n✅ 已切换到会话: {args[0]}")

    def _delete_session(self, args):
        """删除会话 /delete [/d]"""
        if not args:
            raise ValueError("缺少会话名称\n用法: /delete <名称> 或简写 /d <名称>")
        self.session_mgr.delete_session(args[0])
        print(f"\n✅ 已删除会话: {args[0]}")

    def _list_sessions(self, _):
        """列出会话 /list [/l]"""
        sessions = self.session_mgr.list_sessions()
        if not sessions:
            print("\n📭 当前没有活跃会话")
        else:
            print("\n📜 活跃会话列表:")
            for sess in sessions:
                print(f" - {sess}")

    def _save_session(self, _):
        """保存会话 /save [/sv]"""
        if not self.session_mgr.active_session:
            raise ValueError("没有需要保存的活跃会话")
        self.session_mgr.save_session(self.session_mgr.active_session)
        print(f"\n💾 已保存当前会话: {self.session_mgr.active_session}")

    def _exit(self, _=None):
        """退出系统 /exit [/e]"""
        print("\n👋 感谢使用，再见！")
        exit(0)

    def _invalid_command(self, _):
        print("\n⚠️ 无效命令，输入 /help 或 /h 查看帮助")

    def _handle_interrupt(self):
        """处理键盘中断"""
        print("\n⚠️ 操作中断，正在尝试自动保存...")
        self._auto_save_session()
        print("\n🛑 用户主动终止操作")
        exit(1)

    def _handle_read(self, args):
        """处理文件读取命令 /read [/r]"""
        if not args:
            raise ValueError("缺少文件路径\n用法: /read <文件路径> 或简写 /r <文件路径>")

        # 检查会话是否激活
        if not self.session_mgr.active_session:
            print("\n⚠️ 请先创建或选择会话（使用 /create 或 /switch）")
            return

        file_path = Path(args[0])
        try:
            # 调用摘要处理器生成摘要
            summary = self.summary_processor.generate_file_summary(file_path)
            print(f"\n📝 生成摘要成功:\n{summary}")

            # 保存到当前会话
            self.session_mgr.save_summary(
                session_id=self.session_mgr.active_session,
                summary=summary
            )
            print(f"💾 摘要已保存至会话: {self.session_mgr.active_session}")
        except Exception as e:
            print(f"\n❌ 文件处理失败: {str(e)}")