import json
import numpy as np
import faiss
import os
import time
from sentence_transformers import SentenceTransformer

# ============== 配置常量 ==============
EMBEDDINGS_PATH = "output/embeddings.npy"
METADATA_PATH = "output/chunks.json"
INDEX_PATH = "output/faiss_index.bin"
RESULTS_DIR = "output/search_results"


# ============== 索引构建 ==============
def build_faiss_index():
    """基于现有向量文件构建FAISS索引"""
    # 加载预存向量
    embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)

    # 手动归一化（假设之前未归一化）
    if not np.allclose(np.linalg.norm(embeddings, axis=1), 1.0):
        faiss.normalize_L2(embeddings)

    # 创建索引
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # 内积=余弦相似度
    index.add(embeddings)

    # 保存索引
    faiss.write_index(index, INDEX_PATH)
    print(f"✅ 索引构建完成，包含 {index.ntotal} 个向量")


# ============== 检索器类 ==============
class VectorRetriever:
    def __init__(self):
        """加载预存资源"""
        self.index = faiss.read_index(INDEX_PATH)
        self.embeddings = np.load(EMBEDDINGS_PATH)
        with open(METADATA_PATH, "r") as f:
            self.metadata = json.load(f)

        # 验证数据一致性
        assert len(self.metadata) == self.index.ntotal, "数据与索引不匹配！"

    def search(self, query_text, top_k=5):
        """执行语义检索"""
        # 加载编码模型
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # 生成查询向量
        query_embed = model.encode([query_text], convert_to_tensor=True).cpu().numpy()
        query_embed = query_embed.astype(np.float32)
        faiss.normalize_L2(query_embed)

        # 检索
        distances, indices = self.index.search(query_embed, top_k)

        # 组装结果
        return [
            {
                "score": float(distances[0][i]),
                **self.metadata[idx]  # 包含所有元数据字段
        }
        for i, idx in enumerate(indices[0])
        ]

    def save_results(self, results, query_text=None):
        """将结果保存为结构化 JSON 文件"""
        os.makedirs(RESULTS_DIR, exist_ok=True)

        # 生成唯一文件名
        timestamp = int(time.time())
        query_hash = str(abs(hash(query_text)))[:6] if query_text else ""
        filename = f"result_{timestamp}_{query_hash}.json"
        filepath = os.path.join(RESULTS_DIR, filename)

        # 构建结果数据结构
        output = {
            "query": query_text,
            "timestamp": timestamp,
            "results": [
                {
                    "chunk_id": res["chunk_id"],
                    "score": res["score"],
                    "text_preview": res["text"][:100],  # 前100字符预览
                    "full_text_path": METADATA_PATH,  # 指向完整元数据
                    "char_count": res["char_count"],
                    "sentence_count": res["sentence_count"]
                }
                for res in results
            ]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"✅ 结果已保存至：{filepath}")
        return filepath

# ============== 使用示例 ==============
if __name__ == "__main__":
    # 步骤1：构建索引（只需运行一次）
    build_faiss_index()

    # 步骤2：初始化检索器
    retriever = VectorRetriever()

    # 步骤3：执行查询
    query = "What's the DeepSeek-R1-Zero: Pure RL Training Basic Model"
    results = retriever.search(query, top_k=2)

    # 保存结果
    retriever.save_results(results, query)

    # 打印验证
    print("\n检索结果摘要：")
    for res in results:
        print(f"[ID:{res['chunk_id']}] Score: {res['score']:.3f}")
        print(f"Text: {res['text'][:100]}...\n{'-' * 50}")
        print(f"Sentences: {res['sentence_count']}  Chars: {res['char_count']}\n{'-' * 50}")
