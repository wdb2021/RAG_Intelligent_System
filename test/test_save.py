from session_manager import SessionManager
from langchain_core.messages import HumanMessage, AIMessage
def test_session_path_safety():
    #manager = SessionManager()
    #manager.create_session("../../etc/passwd")  # 应自动消毒为合法文件名

#def integration_test():
    # 初始化
    print("integration test")
    manager = SessionManager(session_dir="./test_sessions")

    # 创建会话
    manager.create_session("123")

    # 获取包装器
    history = manager.get_history("123")

    # 添加消息
    history.add_message(HumanMessage(content="第一条消息"))
    history.add_message(AIMessage(content="AI回复"))

    # 强制保存
    manager.save_session("123")

    # 重新加载验证
    new_manager = SessionManager(session_dir="./test_sessions")
    reloaded = new_manager.get_history("123")
    assert len(reloaded.messages) == 2, "消息未正确持久化"
    print("集成测试通过 ✅")