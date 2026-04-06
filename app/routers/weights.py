from fastapi import APIRouter
from app.models.schemas import WeightsSaveRequest
from app.services.appwrite_service import get_user_weights, save_user_weights

router = APIRouter(prefix="/weights", tags=["weights"])

@router.get("/{user_id}")
def fetch_weights(user_id: str):
    w = get_user_weights(user_id)
    return {
        "w_budget":      w.w_budget,
        "w_zone":        w.w_zone,
        "w_schedule":    w.w_schedule,
        "w_cleanliness": w.w_cleanliness,
        "w_noise":       w.w_noise,
        "w_pets":        w.w_pets,
        "w_smoking":     w.w_smoking,
        "w_age":         w.w_age,
        "w_gender":      w.w_gender,
    }

@router.put("/{user_id}")
def update_weights(user_id: str, request: WeightsSaveRequest):
    raw = {
        "w_budget":      request.w_budget,
        "w_zone":        request.w_zone,
        "w_schedule":    request.w_schedule,
        "w_cleanliness": request.w_cleanliness,
        "w_noise":       request.w_noise,
        "w_pets":        request.w_pets,
        "w_smoking":     request.w_smoking,
        "w_age":         request.w_age,
        "w_gender":      request.w_gender,
    }
    total = sum(raw.values())
    if total > 0:
        normalized = {k: round(v / total, 4) for k, v in raw.items()}
    else:
        normalized = raw
    save_user_weights(user_id, normalized)
    return {"status": "saved", "weights": normalized}
