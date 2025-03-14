# message.py
# # 替换 langchain 的 BaseMessage，定义自己的消息结构
from dataclasses import dataclass

#dataclass装饰器无需手动构建
@dataclass
class Message:
    role: str  # "user" 或 "assistant"
    content: str

    def to_dict(self):
        return {"role": self.role, "content": self.content}

    def to_openai_format(self) -> dict:
        """转换为OpenAI API兼容格式"""
        return self.to_dict()

    def copy(self) -> "Message":
        """创建消息副本"""
        return Message(role=self.role, content=self.content)