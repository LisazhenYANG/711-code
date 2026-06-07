"""
向量化 / RAG - 用于"没选类别"时的语义召回。

两个实现:
- MockEmbedding: 词袋归一化向量,纯本地,不需要外部服务。
                 把 POI 的 tags+intro 切词建立词袋,把 query 也用同样方式编码。
- (可扩展) 真实 embedding 模型: 接 sentence-transformers / OpenAI embedding /
                                  DeepSeek embedding API,改 EmbeddingProvider 即可。

候选召回逻辑见 graph/nodes.py 的 candidates 节点。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import math
import re
from typing import Iterable


_TOKEN_PAT = re.compile(r"[\u4e00-\u9fff]|[A-Za-z]+")


def _tokenize(text: str) -> list[str]:
    """简陋的中英混合切词:中文按字符,英文按单词。生产换 jieba / 真 embedding。"""
    if not text:
        return []
    return [t.lower() for t in _TOKEN_PAT.findall(text)]


class EmbeddingProvider(ABC):
    @abstractmethod
    def encode_text(self, text: str) -> dict[str, float]:
        """文本 -> 稀疏向量(词->权重)。"""

    @abstractmethod
    def encode_poi(self, poi: dict) -> dict[str, float]:
        """POI -> 稀疏向量(用 tags + intro + sub_category)。"""

    @staticmethod
    def cosine(va: dict[str, float], vb: dict[str, float]) -> float:
        if not va or not vb:
            return 0.0
        common = set(va) & set(vb)
        if not common:
            return 0.0
        dot = sum(va[k] * vb[k] for k in common)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


class MockEmbedding(EmbeddingProvider):
    """词袋 + TF 归一化,语义召回够用。"""

    def encode_text(self, text: str) -> dict[str, float]:
        toks = _tokenize(text)
        if not toks:
            return {}
        vec: dict[str, float] = {}
        for t in toks:
            vec[t] = vec.get(t, 0) + 1.0
        # L2 归一
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def encode_poi(self, poi: dict) -> dict[str, float]:
        parts: list[str] = []
        parts.extend(poi.get("tags", []))
        if poi.get("intro"):
            parts.append(poi["intro"])
        if poi.get("category_sub"):
            parts.append(poi["category_sub"])
        if poi.get("category_main"):
            parts.append(poi["category_main"])
        return self.encode_text(" ".join(parts))


_default_embedder: EmbeddingProvider | None = None


def get_embedder() -> EmbeddingProvider:
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = MockEmbedding()
    return _default_embedder
