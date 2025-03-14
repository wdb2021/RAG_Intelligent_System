# 智能对话系统 - MultiSession ChatBot

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

多用户智能对话系统，支持会话管理、流式响应和文件摘要生成。通过模块化设计实现功能解耦，提供稳定的对话服务和灵活的功能扩展。

## 🌟 核心功能

### 会话管理
- 多会话支持：`/create` `/switch` `/delete`
- 自动持久化：原子化写入防止数据损坏
- 历史追溯：JSON格式存储对话记录

### 智能处理
- 双模式响应：流式/同步响应自由切换
- 上下文感知：自动维护对话上下文
- 摘要生成：实时更新对话摘要

### 文件处理
- 文本摘要：支持.txt/.md等格式
- 智能解析：结构化内容提取
- 会话绑定：摘要自动关联会话

## 🚀 快速开始

### 环境要求
```bash
Python >= 3.8
pip install -r requirements.txt  # 包含openai python-dotenv
```
# 配置设置 (.env)
#### OpenAI 配置
OPENAI_API_KEY=sk-your-key
OPENAI_API_URL=https://api.openai.com/v1
MAIN_MODEL=gpt-3.5-turbo

#### 摘要服务配置
SUMMARY_API_KEY=sk-your-key
SUMMARY_API_URL=https://api.openai.com/v1
SUMMARY_MODEL=gpt-3.5-turbo-16k

#### 存储配置
SESSION_STORAGE_PATH=./sessions
SUMMARY_STORAGE_PATH=./summaries

# 启动系统
python main.py

# 🛠️ 使用指南
### 会话命令
/create test_session  # 创建会话
/switch test_session  # 切换会话
/list                 # 列出所有会话

### 文件处理
/read document.txt    # 分析文本文件

### 系统控制
/save     # 手动保存当前会话
/help     # 查看帮助信息
/exit     # 安全退出系统

# 📂 项目结构
chat-system/
├── config.py         # 配置管理中心
├── processor.py      # AI处理引擎
├── session_manager.py # 会话生命周期管理
├── chat_interface.py # 用户交互接口
├── message.py        # 消息结构定义
├── summary_processor.py # 摘要生成器
└── main.py           # 系统入口

# 🔧 模块设计

模块	                职责	        关键特性
SessionManager	 会话存储管理	 原子化操作/自动加载
ChatProcessor	 AI响应生成	 流式处理/上下文管理
SummaryProcessor 内容摘要	 文件解析/结构化输出
ChatInterface	 用户交互	 命令解析/状态管理

# ⚙️ 配置参数说明

### 核心参数
configInstance = AppConfig()
#### API端点配置
model_api_url = "https://api.openai.com/v1"  
#### 超时设置
api_timeout = 30.0  
#### 流式模式开关
enable_stream_mode = True

### 存储策略
#### 会话存储路径
session_storage_path = Path("./sessions")  
#### 摘要存储路径
summary_storage_path = Path("./summaries")
