from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from fuzzywuzzy import fuzz
from langdetect import detect
import numpy as np
import asyncio
import logging

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class FuzzySearch:
    def __init__(self, file_list: list[str], device: str = "cuda"):
        self.device = torch.device(device)

        self.file_names = file_list
        self.semantic_model = None
        self.translator_zh2en = None
        self.translator_en2zh = None
        self.file_vectors = None

    async def init_models(self):
        await asyncio.to_thread(self._load_models)
        self.file_vectors = await asyncio.to_thread(self._precompute_vectors)
        console.print(f"  [green]✓[/green] 向量编码完成 ([dim]{len(self.file_names)} 文件, {self.file_vectors.shape[1]} 维[/dim])")
        if self.device.type == "cuda":
            self.file_vectors = self.file_vectors.to(self.device)
            console.print(f"  [green]✓[/green] 已传输到 [dim]{self.device}[/dim]")

    def _load_models(self):
        self.semantic_model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            device=self.device,
        )
        console.print("  [green]✓[/green] 语义模型加载完成")
        self.translator_zh2en = pipeline(
            model="Helsinki-NLP/opus-mt-zh-en",
            device=self.device,
        )
        console.print("  [green]✓[/green] 中译英模型加载完成")
        self.translator_en2zh = pipeline(
            model="Helsinki-NLP/opus-mt-en-zh",
            device=self.device,
        )
        console.print("  [green]✓[/green] 英译中模型加载完成")

    def _precompute_vectors(self):
        return self.semantic_model.encode(
            self.file_names,
            convert_to_tensor=True,
            show_progress_bar=False,
            device=self.device,
        )

    async def translate_text(self, text: str) -> str:
        try:
            if detect(text) == "zh":
                logger.info("keyword is zh")
                result = await asyncio.to_thread(self.translator_zh2en, text)
                return result[0]["translation_text"]
            else:
                logger.info("keyword is en")
                return text
        except Exception as e:
            logger.warning(f"翻译失败: {e}")
            return text

    async def search(self, keyword: str, limit: int = 5):
        translated = await self.translate_text(keyword)
        query_vec = self.semantic_model.encode(
            [translated], convert_to_tensor=True, device=self.device
        )[0]

        if self.file_vectors is not None and len(self.file_vectors) > 0:
            file_vectors_normalized = self.file_vectors / self.file_vectors.norm(
                dim=1, keepdim=True
            )
            query_vec_normalized = query_vec / query_vec.norm()
            semantic_scores = file_vectors_normalized @ query_vec_normalized.T
            semantic_scores_np = semantic_scores.cpu().numpy()
        else:
            semantic_scores_np = np.zeros(len(self.file_names))

        fuzzy_scores = []
        for fn in self.file_names:
            filename_lower = fn.lower()
            translated_lower = translated.lower()
            path_parts = Path(fn).stem.lower().split("_")

            partial_score = fuzz.partial_ratio(translated_lower, filename_lower) / 100
            token_score = (
                fuzz.token_set_ratio(translated_lower, " ".join(path_parts)) / 100
            )
            fuzzy_score = max(partial_score, token_score)

            match_bonus = 1.0
            if any(part == translated_lower for part in path_parts):
                match_bonus *= 3.0
            elif any(translated_lower in part for part in path_parts):
                match_bonus *= 2.0
            elif translated_lower in filename_lower:
                match_bonus *= 1.5

            fuzzy_scores.append(fuzzy_score * match_bonus)

        semantic_weight = 0.2 if translated.isascii() else 0.4
        final_scores = (semantic_weight * semantic_scores_np) + (
            (1 - semantic_weight) * np.array(fuzzy_scores)
        )

        top_indices = np.argsort(final_scores)[::-1][:limit]
        results = [
            {"name": self.file_names[i], "score": f"{final_scores[i]:.2f}"}
            for i in top_indices
        ]
        return results
