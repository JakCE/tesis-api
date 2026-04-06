from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import RecommendationRequest, RecommendationResult
from app.services.hybrid import get_recommendations, MODEL_VERSION
from app.services.appwrite_service import save_recommendation_log

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

def _save_logs(user_id: str, results: list[RecommendationResult]) -> None:
    for r in results:
        try:
            save_recommendation_log(
                user_id             = user_id,
                recommended_user_id = r.user_id,
                content_score       = r.content_score,
                collab_score        = r.collab_score,
                hybrid_score        = r.hybrid_score,
                alpha_used          = r.alpha_used,
                model_version       = MODEL_VERSION,
            )
        except Exception:
            pass  # log fallido no debe romper nada

@router.post("/", response_model=list[RecommendationResult])
def recommend(request: RecommendationRequest, background_tasks: BackgroundTasks):
    results = get_recommendations(user_id=request.user_id, limit=request.limit)
    if not results and results is not None:
        # lista vacía es válida (sin candidatos), solo falla si el user no existe
        pass
    if results is None:
        raise HTTPException(status_code=404, detail="User not found")

    background_tasks.add_task(_save_logs, request.user_id, results)
    return results
