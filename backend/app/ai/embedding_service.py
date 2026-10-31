"""
Semantic similarity (spec section 11). Default backend: TF-IDF + cosine
similarity (scikit-learn) - pure Python, no model download, works fully
offline. Optional upgrade: sentence-transformers, enabled by installing it
and setting USE_SENTENCE_EMBEDDINGS=true - produces better semantic
matches (e.g. "predictive modeling" <-> "classification models") but
needs ~2GB for PyTorch + model weights and internet access to
huggingface.co on first run. The app is fully functional on TF-IDF alone.
"""
import os

_st_model = None
_st_load_failed = False
USE_SENTENCE_EMBEDDINGS = os.getenv("USE_SENTENCE_EMBEDDINGS", "false").lower() == "true"


def _try_load_sentence_transformer():
    global _st_model, _st_load_failed
    if _st_model is not None or _st_load_failed:
        return _st_model
    try:
        from sentence_transformers import SentenceTransformer
        from app.database.config import settings
        _st_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    except Exception:
        _st_load_failed = True
        _st_model = None
    return _st_model


def similarity(text_a: str, text_b: str) -> float:
    text_a, text_b = (text_a or "").strip(), (text_b or "").strip()
    if not text_a or not text_b:
        return 0.0

    if USE_SENTENCE_EMBEDDINGS:
        model = _try_load_sentence_transformer()
        if model is not None:
            import numpy as np
            emb = model.encode([text_a, text_b])
            a, b = emb[0], emb[1]
            denom = np.linalg.norm(a) * np.linalg.norm(b)
            return max(0.0, min(1.0, float(np.dot(a, b) / denom))) if denom else 0.0

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    try:
        tfidf = TfidfVectorizer(stop_words="english").fit_transform([text_a, text_b])
    except ValueError:
        return 0.0
    return max(0.0, min(1.0, float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])))
