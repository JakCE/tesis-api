from app.services.content_based import compute_content_score, update_embedding_vector
from app.services.collaborative import compute_collab_score
from app.services.appwrite_service import (
    get_user_profile,
    get_user_weights,
    get_visible_profiles,
    get_all_interactions,
    tablesdb,
    DB_ID,
    COLLECTIONS,
)
from app.models.schemas import RecommendationResult

MODEL_VERSION = "v1.0"

def get_recommendations(user_id: str, limit: int = 10) -> list[RecommendationResult]:
    """
    Genera recomendaciones híbridas para un usuario.
    NO guarda logs — el router los guarda en background.
    """
    user    = get_user_profile(user_id)
    weights = get_user_weights(user_id)

    if not user:
        return []

    # Actualizar embedding_vector si cambió
    new_embedding = update_embedding_vector(user, weights)
    if user.embedding_vector != new_embedding:
        tablesdb.update_row(
            database_id = DB_ID,
            table_id    = COLLECTIONS["profiles"],
            row_id      = user_id,
            data        = {"embedding_vector": new_embedding}
        )

    candidates   = get_visible_profiles(exclude_user_id=user_id)
    interactions = get_all_interactions()
    all_user_ids = [user_id] + [c.id for c in candidates]

    results = []
    for candidate in candidates:
        content_score = compute_content_score(user, candidate, weights)
        collab_score  = compute_collab_score(
            user_id      = user_id,
            candidate_id = candidate.id,
            interactions = interactions,
            all_user_ids = all_user_ids,
        )
        alpha        = weights.alpha
        hybrid_score = alpha * content_score + (1 - alpha) * collab_score

        results.append(RecommendationResult(
            user_id       = candidate.id,
            content_score = round(content_score, 4),
            collab_score  = round(collab_score, 4),
            hybrid_score  = round(hybrid_score, 4),
            alpha_used    = alpha,
        ))

    results.sort(key=lambda r: r.hybrid_score, reverse=True)
    return results[:limit]
