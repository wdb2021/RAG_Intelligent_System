# test_summary.py
from pathlib import Path
import pytest
from message import Message
from session_manager import SessionManager
from summary_processor import SummaryProcessor
from config import configInstance

# 初始化组件
mgr = SessionManager(session_dir="../sessions")
processor = SummaryProcessor()

# 确保目录存在
Path("../documents").mkdir(exist_ok=True)
Path("../summaries").mkdir(exist_ok=True)

# 创建测试文件（若不存在）
test_file = Path("../documents/read.txt")
if not test_file.exists():
    test_file.write_text("""量子计算利用量子比特实现并行计算，相比经典计算机在特定问题上具有指数级加速优势...
                         主要应用领域包括：1) 密码学破解 2) 药物分子模拟 3) 优化问题求解...""")


def test_file_summary():
    try:
        # 生成文件摘要
        summary = processor.generate_file_summary(
            file_path="../documents/read.txt",
            max_length=200
        )
        print("✅ 生成的摘要内容:\n", summary)

        # 保存摘要到指定会话
        mgr.save_summary(session_id="user1", summary=summary)
        print(f"📥 摘要已保存至: {configInstance.summary_storage_path}/summary_user1.json")

    except Exception as e:
        pytest.fail(f"❌ 测试失败: {str(e)}")
