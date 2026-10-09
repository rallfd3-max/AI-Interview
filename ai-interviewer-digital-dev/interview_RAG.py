import os
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
import json
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv, find_dotenv

# coding=utf-8
load_dotenv()

if os.getenv('DISABLE_RAG') == 'True':
    def search(str):
        return str
else:
    def split_into_chunks(doc_file):
        with open(doc_file, 'r', encoding='UTF-8') as f:
            text = f.read()  # 此时 text 是标准 Unicode 字符串

        # 现在可以安全地按句号分割
        return [chunk.replace('\n', '') for chunk in text.split("。")]


    embedding_model = SentenceTransformer("all-MPNet-base-v2")
    cross_encoder = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')


    def embed_chunk(chunk: str):
        embedding = embedding_model.encode(chunk)
        return embedding.tolist()


    def search(query, top_bi, top_k):
        import time
        start_time = time.time()
        with open("companyInfo_embeddings.json", "r", encoding="utf-8") as f:
            records = json.load(f)
        end_time = time.time()
        print(f"读取文件耗时: {end_time - start_time:.2f} 秒")
        start_time = time.time()
        query_vec = embed_chunk(query)
        query_vec = [query_vec]
        doc_embs = np.array([rec["embedding"] for rec in records])
        sims = cosine_similarity(query_vec, doc_embs)[0]
        # 取前 top_k 召回
        idx_bi = np.argsort(sims)[::-1][:top_bi]
        candidates = [records[i] for i in idx_bi]
        end_time = time.time()
        print(f"召回耗时: {end_time - start_time:.2f} 秒")
        # 重排
        start_time = time.time()

        pairs = [(query, rec["chunk"]) for rec in candidates]
        scores = cross_encoder.predict(pairs)
        end_time = time.time()
        print(f"重排耗时: {end_time - start_time:.2f} 秒")

        # 排序并选 top_final
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        top_records = [(candidates[i]["chunk"], float(scores[i])) for i in sorted_indices]
        return top_records


if __name__ == "__main__":
    # # 存储文件代码
    # doc_file = "companyInfo.txt"
    # chunks = split_into_chunks(doc_file)
    # embeddings = [embed_chunk(chunk) for chunk in chunks]
    # print(len(embeddings))
    # print(embeddings[0])
    # data = [
    #     {"chunk": chunk, "embedding": emb}
    #     for chunk, emb in zip(chunks, embeddings)
    # ]
    #
    # # 保存为 JSON 文件
    # with open("companyInfo_embeddings.json", "w", encoding="utf-8") as fo:
    #     json.dump(data, fo, ensure_ascii=False, indent=2)

    query = "五险一金情况"
    print(search(query, top_k=2, top_bi=5))
