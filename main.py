# main.py
from config import configInstance
from session_manager import SessionManager
from chat_interface import ChatInterface
from processor import ChatProcessor
from summary_processor import SummaryProcessor


def initialize_system() -> ChatInterface:
    """系统初始化核心"""
    try:
        # 初始化会话管理系统
        session_mgr = SessionManager(configInstance.session_storage_path)

        # 初始化AI处理器
        ai_processor = ChatProcessor()
        # 新增：初始化摘要处理器
        summary_processor = SummaryProcessor()

        # 构建对话接口
        return ChatInterface(
            session_manager=session_mgr,
            processor=ai_processor,
            summary_processor=summary_processor
        )
    except Exception as e:
        raise RuntimeError(f"系统初始化失败: {str(e)}")


def main():
    """应用程序主入口"""
    print("🔧 正在启动智能对话系统...")
    try:
        chat_system = initialize_system()
        print("\n✅ 系统组件加载完成")
        print(f"🏷️ 对话模型: {configInstance.model_type}")
        print(f"📁 会话存储: {configInstance.session_storage_path}\n")
        chat_system.run()
    except KeyboardInterrupt:
        print("\n🛑 用户主动终止操作")
    except Exception as e:
        print(f"\n🔥 严重错误: {str(e)}")
        exit(1)
    finally:
        print("\n✨ 感谢使用，期待下次对话！")


if __name__ == "__main__":
    main()