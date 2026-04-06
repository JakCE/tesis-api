from fastapi import APIRouter, HTTPException
from math import radians, sin, cos, sqrt, atan2
from datetime import date
from app.services.appwrite_service import get_user_profile, get_user_weights
from app.config import settings

router = APIRouter(prefix="/explain", tags=["explain"])


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _dimension_scores(profile_a, profile_b, weights) -> list[dict]:
    """
    Returns per-dimension raw scores (0-100) and weights (0-100).
    Mirrors the logic in content_based.py but returns unweighted scores.
    """
    dims = []

    # 1. Presupuesto
    overlap = min(profile_a.budget_max, profile_b.budget_max) - max(profile_a.budget_min, profile_b.budget_min)
    budget_range = max(profile_a.budget_max, profile_b.budget_max) - min(profile_a.budget_min, profile_b.budget_min)
    budget_score = max(0.0, overlap / budget_range) if budget_range > 0 else 1.0
    dims.append({"name": "Presupuesto", "score": round(budget_score * 100), "weight": round(weights.w_budget * 100)})

    # 2. Zona
    if profile_a.preferred_lat != 0 and profile_b.preferred_lat != 0:
        dist = _haversine_km(profile_a.preferred_lat, profile_a.preferred_lng,
                             profile_b.preferred_lat, profile_b.preferred_lng)
        max_r = max(profile_a.search_radius_km, profile_b.search_radius_km)
        zone_score = max(0.0, 1 - (dist / max_r)) if max_r > 0 else 0.5
    else:
        zone_score = 0.5
    dims.append({"name": "Zona geográfica", "score": round(zone_score * 100), "weight": round(weights.w_zone * 100)})

    # 3. Horario
    smap = {"morning": 0, "flexible": 1, "night": 2}
    s1, s2 = smap.get(profile_a.schedule, 1), smap.get(profile_b.schedule, 1)
    if s1 == s2:
        sched = 1.0
    elif abs(s1 - s2) == 1 or profile_a.schedule == "flexible" or profile_b.schedule == "flexible":
        sched = 0.6
    else:
        sched = 0.2
    dims.append({"name": "Horario", "score": round(sched * 100), "weight": round(weights.w_schedule * 100)})

    # 4. Limpieza
    clean = 1 - abs(profile_a.cleanliness_level - profile_b.cleanliness_level) / 4
    dims.append({"name": "Limpieza", "score": round(clean * 100), "weight": round(weights.w_cleanliness * 100)})

    # 5. Ruido
    noise = 1 - abs(profile_a.noise_tolerance - profile_b.noise_tolerance) / 4
    dims.append({"name": "Tolerancia al ruido", "score": round(noise * 100), "weight": round(weights.w_noise * 100)})

    # 6. Mascotas
    pets_ok = not (
        (profile_a.has_pets and not profile_b.accepts_pets) or
        (profile_b.has_pets and not profile_a.accepts_pets)
    )
    dims.append({"name": "Mascotas", "score": 100 if pets_ok else 0, "weight": round(weights.w_pets * 100)})

    # 7. Tabaco
    smoke_ok = not (
        (profile_a.smokes and not profile_b.accepts_smokers) or
        (profile_b.smokes and not profile_a.accepts_smokers)
    )
    dims.append({"name": "Fumadores", "score": 100 if smoke_ok else 0, "weight": round(weights.w_smoking * 100)})

    # 8. Edad
    try:
        birth = date.fromisoformat(profile_b.birth_date)
        today = date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        age_ok = profile_a.age_range_min <= age <= profile_a.age_range_max
        age_score = 1.0 if age_ok else 0.3
    except Exception:
        age_score = 0.5
    dims.append({"name": "Rango de edad", "score": round(age_score * 100), "weight": round(weights.w_age * 100)})

    # 9. Género
    gender_ok = (
        profile_a.gender_preference == "any" or
        profile_a.gender_preference == profile_b.gender
    )
    dims.append({"name": "Preferencia de género", "score": 100 if gender_ok else 0, "weight": round(weights.w_gender * 100)})

    return dims


@router.get("/{user_a_id}/{user_b_id}")
def explain_compatibility(user_a_id: str, user_b_id: str):
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="Groq API key not configured")

    profile_a = get_user_profile(user_a_id)
    profile_b = get_user_profile(user_b_id)
    if not profile_a or not profile_b:
        raise HTTPException(status_code=404, detail="Profile not found")

    weights = get_user_weights(user_a_id)
    dimensions = _dimension_scores(profile_a, profile_b, weights)

    # Weighted total (mirrors hybrid content score)
    total_score = round(sum(
        d["score"] / 100 * d["weight"] / 100
        for d in dimensions
    ) * 100)

    # Build a compact summary for the prompt
    dim_lines = "\n".join(
        f"- {d['name']}: {d['score']}% de compatibilidad (importancia para el usuario: {d['weight']}%)"
        for d in dimensions
    )

    prompt = (
        f"Eres el asistente de compatibilidad de RoomieMatch, una app para encontrar roomies.\n\n"
        f"Dos usuarios tienen una compatibilidad total del {total_score}%.\n\n"
        f"Desglose por dimensión:\n{dim_lines}\n\n"
        f"Explica en español, con tono amigable y motivador (máximo 3 párrafos cortos, sin bullets):\n"
        f"1. Los puntos fuertes de esta compatibilidad.\n"
        f"2. Las áreas donde pueden diferir y cómo gestionarlo.\n"
        f"3. Una recomendación final breve de si vale la pena iniciar conversación.\n"
        f"No menciones los porcentajes exactos, habla de forma natural. Máximo 180 palabras."
    )

    try:
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        explanation = response.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq error: {str(e)}")

    return {
        "explanation": explanation,
        "total_score": total_score,
        "dimensions":  dimensions,
    }
