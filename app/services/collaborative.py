import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.services.appwrite_service import get_all_interactions

def build_interaction_matrix(
    interactions: list[dict],
    all_user_ids: list[str]
) -> tuple[np.ndarray, dict, dict]:
    """
    Construye la matriz de interacciones usuario x usuario.
    like=1, skip=0, dislike=-1
    """
    action_map = {"like": 1.0, "skip": 0.0, "dislike": -1.0}
    idx_map  = {uid: i for i, uid in enumerate(all_user_ids)}
    n = len(all_user_ids)
    matrix = np.zeros((n, n))

    for interaction in interactions:
        from_id = interaction.get("from_user_id")
        to_id   = interaction.get("to_user_id")
        action  = interaction.get("action", "skip")
        if from_id in idx_map and to_id in idx_map:
            i = idx_map[from_id]
            j = idx_map[to_id]
            matrix[i][j] = action_map.get(action, 0.0)

    return matrix, idx_map, {i: uid for uid, i in idx_map.items()}

def compute_collab_score(
    user_id: str,
    candidate_id: str,
    interactions: list[dict],
    all_user_ids: list[str]
) -> float:
    """
    Calcula el collaborative filtering score usando User-Based KNN.
    Encuentra usuarios similares al user_id y predice si le gustaría el candidate.
    Retorna un valor en [0, 1].
    """
    if len(all_user_ids) < 3:
        return 0.5  # cold start — sin suficientes usuarios

    matrix, idx_map, _ = build_interaction_matrix(interactions, all_user_ids)

    if user_id not in idx_map or candidate_id not in idx_map:
        return 0.5

    user_idx      = idx_map[user_id]
    candidate_idx = idx_map[candidate_id]
    user_vector   = matrix[user_idx].reshape(1, -1)

    # Similitud coseno entre el usuario y todos los demás
    similarities = cosine_similarity(user_vector, matrix)[0]
    similarities[user_idx] = 0  # excluir al propio usuario

    # Top 5 usuarios más similares (KNN k=5)
    k = min(5, len(all_user_ids) - 1)
    top_k_indices = np.argsort(similarities)[-k:]

    # Predicción ponderada por similitud
    numerator   = 0.0
    denominator = 0.0
    for idx in top_k_indices:
        sim   = similarities[idx]
        score = matrix[idx][candidate_idx]
        if sim > 0:
            numerator   += sim * score
            denominator += abs(sim)

    if denominator == 0:
        return 0.5

    # Normalizar de [-1,1] a [0,1]
    raw_score = numerator / denominator
    return float((raw_score + 1) / 2)