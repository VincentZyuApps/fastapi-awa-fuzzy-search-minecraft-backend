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
    def __init__(self, file_list):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 初始化多语言模型
        self.semantic_model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            device=self.device
        ) 

        # 初始化翻译管道
        self.translator_zh2en = pipeline(
            task="translation",
            model="Helsinki-NLP/opus-mt-zh-en",
            num_workers=0
            # device=-1,
        )  # 网页2
        self.translator_en2zh = pipeline(
            task="translation",
            model="Helsinki-NLP/opus-mt-en-zh",
            num_workers=0
            # device=-1,
        )

        # 预计算文件向量
        self.file_names = file_list
        self.file_vectors = self._precompute_vectors()  # 启动时预加载

    def _precompute_vectors(self):
        """预计算所有文件名的语义向量"""
        return self.semantic_model.encode(
            self.file_names,
            convert_to_numpy=True,
            show_progress_bar=True
        )

    async def translate_text(self, text: str) -> str:
        """异步翻译处理"""
        try:
            if detect(text) == 'zh':
                print("keyword is zh")
                return await asyncio.to_thread(
                    self.translator_zh2en,
                    # text, max_length=512
                    generate_kwargs={"max_length": 512}  # 字典包裹参数
                )[0]['translation_text']

            else:
                print("keyword is en")
                return text

        except Exception as e:
            print(f"[error]翻译失败: {str(e)}")
            return text  # 失败时返回原文


    def _hybrid_similarity(self, query_vec, filename, translated):
        filename_lower = filename.lower()
        translated_lower = translated.lower()
        path_parts = Path(filename).stem.lower().split('_')

        # 增强型匹配规则
        exact_in_path = any(part == translated_lower for part in path_parts)
        substring_in_path = any(translated_lower in part for part in path_parts)
        substring_in_fullname = translated_lower in filename_lower

        # 模糊匹配得分
        partial_score = fuzz.partial_ratio(translated_lower, filename_lower) / 100
        token_score = fuzz.token_set_ratio(translated_lower, ' '.join(path_parts)) / 100
        fuzzy_score = max(partial_score, token_score)

        # 匹配奖励机制
        match_bonus = 1.0
        if exact_in_path:
            match_bonus *= 3.0  # 路径部分精确匹配
        elif substring_in_path:
            match_bonus *= 2.0  # 路径部分子串匹配
        elif substring_in_fullname:
            match_bonus *= 1.5  # 全路径子串匹配

        # 语义得分
        idx = self.file_names.index(filename)
        semantic_score = np.dot(query_vec, self.file_vectors[idx])

        # 动态权重调整（英文查询侧重模糊匹配）
        semantic_weight = 0.2 if translated_lower.isascii() else 0.4
        fuzzy_weight = 1 - semantic_weight

        return (semantic_weight * semantic_score) + (fuzzy_weight * fuzzy_score) * match_bonus

    async def search(self, keyword: str, limit: int = 5):
        """综合搜索入口"""
        # 语言处理（网页4）
        translated = await self.translate_text(keyword)
        # 语义向量化
        query_vec = self.semantic_model.encode([translated])[0]

        # 并行计算相似度
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: [
                (fn, self._hybrid_similarity(query_vec, fn, translated))
                for fn in self.file_names
            ]
        )

        # 结果排序
        sorted_results = sorted(scores, key=lambda x: x[1], reverse=True)[:limit]
        return [{"name": name, "score": f"{score:.2f}"} for name, score in sorted_results]
