# fuzzy_search.py
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from fuzzywuzzy import fuzz
from langdetect import detect
import numpy as np
import asyncio


class FuzzySearch:
    # 构造函数现在接受 device 参数
    def __init__(self, file_list, device: str = None):
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
        print(f"Using device: {self.device}")
        
        self.file_names = file_list
        self.semantic_model = None
        self.translator_zh2en = None
        self.translator_en2zh = None
        self.file_vectors = None


    async def init_models(self):
        """异步加载模型和预计算向量"""
        # 使用 asyncio.to_thread 包装同步的、I/O 密集型操作，防止阻塞
        await asyncio.to_thread(self._load_models)
        self.file_vectors = await asyncio.to_thread(self._precompute_vectors)
        # 将向量张量移到 GPU
        if self.device.type == 'cuda':
            self.file_vectors = self.file_vectors.to(self.device)
            print("File vectors loaded onto GPU.")


    def _load_models(self):
        """同步加载所有模型并指定设备"""
        # 初始化多语言模型
        self.semantic_model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            device=self.device
        )
        # 初始化翻译管道，确保在 GPU 上运行
        self.translator_zh2en = pipeline(
            task="translation",
            model="Helsinki-NLP/opus-mt-zh-en",
            device=self.device  # 明确指定使用 GPU
        )
        self.translator_en2zh = pipeline(
            task="translation",
            model="Helsinki-NLP/opus-mt-en-zh",
            device=self.device  # 明确指定使用 GPU
        )


    def _precompute_vectors(self):
        """预计算所有文件名的语义向量"""
        # 使用 convert_to_tensor 并指定 device，直接在 GPU 上生成向量
        return self.semantic_model.encode(
            self.file_names,
            convert_to_tensor=True,
            show_progress_bar=True,
            device=self.device
        )

    async def translate_text(self, text: str) -> str:
        """异步翻译处理"""
        try:
            if detect(text) == 'zh':
                print("keyword is zh")
                result = await asyncio.to_thread(self.translator_zh2en, text)
                return result[0]['translation_text']
            else:
                print("keyword is en")
                return text

        except Exception as e:
            print(f"[error]翻译失败: {str(e)}")
            return text  # 失败时返回原文


    def _hybrid_similarity_np(self, query_vec, filename, translated):
        """
        这个方法在 GPU 优化后不再需要，但保留以作参考。
        """
        filename_lower = filename.lower()
        translated_lower = translated.lower()
        path_parts = Path(filename).stem.lower().split('_')

        # 模糊匹配得分
        partial_score = fuzz.partial_ratio(translated_lower, filename_lower) / 100
        token_score = fuzz.token_set_ratio(translated_lower, ' '.join(path_parts)) / 100
        fuzzy_score = max(partial_score, token_score)

        # 匹配奖励机制
        match_bonus = 1.0
        if any(part == translated_lower for part in path_parts):
            match_bonus *= 3.0
        elif any(translated_lower in part for part in path_parts):
            match_bonus *= 2.0
        elif translated_lower in filename_lower:
            match_bonus *= 1.5

        # 语义得分
        idx = self.file_names.index(filename)
        semantic_score = np.dot(query_vec, self.file_vectors[idx].cpu().numpy())

        # 动态权重调整
        semantic_weight = 0.2 if translated_lower.isascii() else 0.4
        fuzzy_weight = 1 - semantic_weight

        return (semantic_weight * semantic_score) + (fuzzy_weight * fuzzy_score) * match_bonus


    async def search(self, keyword: str, limit: int = 5):
        """综合搜索入口，利用 GPU 加速向量计算"""
        # 语言处理
        translated = await self.translate_text(keyword)
        # 语义向量化，直接在 GPU 上执行
        query_vec = self.semantic_model.encode(
            [translated],
            convert_to_tensor=True,
            device=self.device
        )[0]

        # 使用 PyTorch 计算所有文件向量和查询向量的余弦相似度
        # 这步操作完全在 GPU 上并行执行
        if self.file_vectors is not None and len(self.file_vectors) > 0:
            # 归一化向量以进行余弦相似度计算
            # 向量的 L2 范数（torch.linalg.norm）
            file_vectors_normalized = self.file_vectors / self.file_vectors.norm(dim=1, keepdim=True)
            query_vec_normalized = query_vec / query_vec.norm()

            # 计算点积，得到余弦相似度
            semantic_scores = file_vectors_normalized @ query_vec_normalized.T

            # 将结果从 GPU 移回 CPU 并转换为 NumPy
            semantic_scores_np = semantic_scores.cpu().numpy()
        else:
            semantic_scores_np = np.zeros(len(self.file_names))

        # 异步计算模糊匹配得分
        fuzzy_scores = []
        for fn in self.file_names:
            filename_lower = fn.lower()
            translated_lower = translated.lower()
            path_parts = Path(fn).stem.lower().split('_')

            # 模糊匹配得分
            partial_score = fuzz.partial_ratio(translated_lower, filename_lower) / 100
            token_score = fuzz.token_set_ratio(translated_lower, ' '.join(path_parts)) / 100
            fuzzy_score = max(partial_score, token_score)

            # 匹配奖励机制
            match_bonus = 1.0
            if any(part == translated_lower for part in path_parts):
                match_bonus *= 3.0
            elif any(translated_lower in part for part in path_parts):
                match_bonus *= 2.0
            elif translated_lower in filename_lower:
                match_bonus *= 1.5
            
            # 将模糊得分和奖励合并
            fuzzy_scores.append(fuzzy_score * match_bonus)

        # 组合得分
        semantic_weight = 0.2 if translated.isascii() else 0.4
        final_scores = (semantic_weight * semantic_scores_np) + ((1 - semantic_weight) * np.array(fuzzy_scores))

        # 排序并返回结果
        top_indices = np.argsort(final_scores)[::-1][:limit]
        results = [
            {"name": self.file_names[i], "score": f"{final_scores[i]:.2f}"}
            for i in top_indices
        ]
        return results