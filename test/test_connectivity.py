from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from session_manager import SessionManager
from chat_interface import ChatInterface
from config import configInstance  # 使用统一的配置实例


def test_model_connection():
    """测试模型是否能正常调用"""
    try:
        # 创建临时测试模型实例
        test_llm = ChatOpenAI(
            openai_api_key=configInstance.openai_api_key,
            base_url=configInstance.model_api_url,
            model=configInstance.model_type,
            temperature=0,
            max_retries=1,
            timeout=10
        )

        # 发送测试请求
        response = test_llm.invoke("请回复'服务状态正常'")

        # 验证响应结果
        if "正常" in response.content:
            print("✅ 模型连接测试通过")
            print(response.content)
            return True
        else:
            print("⚠️ 收到异常响应:", response.content)
            return False

    except Exception as e:
        print("❌ 模型连接测试失败:")
        print(f"错误类型: {type(e).__name__}")
        print(f"详细信息: {str(e)}")
        print("\n请检查以下配置:")
        print(f"1. API 密钥: {'已配置' if configInstance.openai_api_key else '未配置'}")
        print(f"2. API 端点: {configInstance.model_api_url}")
        print(f"3. 模型类型: {configInstance.model_type}")
        return False



def initialize_system():
    """系统初始化函数（完全基于配置类）"""

    # 1. 初始化带自定义端点的模型
    llm = ChatOpenAI(
        openai_api_key=configInstance.openai_api_key,  # 从配置实例获取
        base_url=configInstance.model_api_url,  # 自定义API端点
        model=configInstance.model_type,  # 配置中的模型类型
        temperature=0.7,
        timeout=30  # 建议添加超时配置
    )

    # 2. 构建可维护的提示模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个知识渊博的助手"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    # 3. 构建可复用链
    processing_chain = prompt_template | llm

    # 4. 初始化带验证的会话管理器
    session_manager = SessionManager()

    # 5. 配置历史感知链
    chain_with_history = RunnableWithMessageHistory(
        processing_chain,
        history_factory=lambda session_id: session_manager.get_history(session_id),
        input_messages_key="input",
        history_messages_key="history"
    )

    # 6. 创建可配置的交互接口
    return ChatInterface(
        chain=chain_with_history,
        session_manager=session_manager,
        ai_prefix="助手",
        user_prefix="用户",
        max_retries=3  # 可添加到配置类
    )


if __name__ == "__main__":
    # 先执行连接测试
    if test_model_connection():
        # 测试通过后初始化系统
        try:
            chat_system = initialize_system()
            print("\n" + "=" * 50)
            chat_system.run()
        except Exception as e:
            print(f"系统运行时错误: {str(e)}")
            exit(1)
    else:
        print("🛑 启动中止，请先修复配置问题")
        exit(1)