import os
import json
import nltk
import numpy as np
from sentence_transformers import SentenceTransformer

# ================= 配置部分 =================
nltk_data_dir = os.path.expanduser("~/nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)  # 强制指定数据路径


# ================= 核心功能 =================
def split_into_chunks(text, max_sentences=3, max_chars=500):
    """智能分块函数"""
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = []
    char_count = 0

    for sent in sentences:
        sent_len = len(sent)

        # 满足任一条件则新建块
        if (len(current_chunk) >= max_sentences) or (char_count + sent_len > max_chars):
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            char_count = 0

        current_chunk.append(sent)
        char_count += sent_len

    # 添加最后一个块
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# ================= 执行流程 =================
if __name__ == "__main__":
    # 1. 读取文本
    with open("documents/read_en.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # 2. 分块处理
    chunks = split_into_chunks(text, max_sentences=3, max_chars=500)

    # 3. 生成向量
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(chunks)

    # ================= 验证逻辑 =================
    # 验证嵌入维度 (384维)
    assert embeddings.shape[1] == 384, f"维度错误！当前维度：{embeddings.shape[1]}"
    print(f"\n✅ 验证通过：所有嵌入向量均为 384 维")

    # 保存 numpy 格式
    os.makedirs("output", exist_ok=True)
    np.save("output/embeddings.npy", embeddings)
    print("✅ 向量已保存至 output/embeddings.npy")

    # 验证第一个 chunk 的句子数量
    first_chunk = chunks[0]
    sentences_in_chunk = nltk.sent_tokenize(first_chunk)
    print("\n🔍 首块内容验证：")
    print(f"文本内容：\n{first_chunk}\n")
    print(f"包含句子数：{len(sentences_in_chunk)}")
    print("实际句子列表：")
    for i, sent in enumerate(sentences_in_chunk, 1):
        print(f"{i}. {sent}")

    # ================= 保存结构化数据 =================
    output_data = [
        {
            "chunk_id": idx,
            "text": chunk,
            "embedding": embedding.tolist(),  # 转换为列表
            "char_count": len(chunk),
            "sentence_count": len(nltk.sent_tokenize(chunk))
        }
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    with open("output/chunks.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("\n✅ 结构化数据已保存至 output/chunks.json")

# 预期输出示例
"""
✅ 验证通过：所有嵌入向量均为 384 维
✅ 向量已保存至 output/embeddings.npy

🔍 首块内容验证：
文本内容：
This is the first sentence. Second sentence here. Third sentence ends.

包含句子数：3
实际句子列表：
1. This is the first sentence.
2. Second sentence here.
3. Third sentence ends.

✅ 结构化数据已保存至 output/chunks.json
"""