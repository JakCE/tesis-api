import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from math import radians, sin, cos, sqrt, atan2
import json
from app.models.schemas import UserProfileSchema, PreferenceWeightsSchema

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en km entre dos coordenadas."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def build_feature_vector(
    user: UserProfileSchema,
    candidate: UserProfileSchema,
    weights: PreferenceWeightsSchema
) -> np.ndarray:
    """
    Construye un vector de compatibilidad entre user y candidate.
    Cada dimensión representa qué tan compatibles son en ese criterio.
    Valores en [0, 1] donde 1 = perfectamente compatibles.
    """
    features = []

    # 1. Budget — overlap entre rangos presupuestarios
    overlap = min(user.budget_max, candidate.budget_max) - max(user.budget_min, candidate.budget_min)
    budget_range = max(user.budget_max, candidate.budget_max) - min(user.budget_min, candidate.budget_min)
    budget_score = max(0, overlap / budget_range) if budget_range > 0 else 1.0
    features.append(budget_score * weights.w_budget)

    # 2. Zona — distancia haversine normalizada por radio de búsqueda
    if user.preferred_lat != 0 and candidate.preferred_lat != 0:
        dist = haversine_distance(
            user.preferred_lat, user.preferred_lng,
            candidate.preferred_lat, candidate.preferred_lng
        )
        max_radius = max(user.search_radius_km, candidate.search_radius_km)
        zone_score = max(0, 1 - (dist / max_radius)) if max_radius > 0 else 0.5
    else:
        zone_score = 0.5  # sin coordenadas, neutral
    features.append(zone_score * weights.w_zone)

    # 3. Horario — coincidencia exacta o flexible
    schedule_map = {"morning": 0, "flexible": 1, "night": 2}
    s1 = schedule_map.get(user.schedule, 1)
    s2 = schedule_map.get(candidate.schedule, 1)
    if s1 == s2:
        schedule_score = 1.0
    elif abs(s1 - s2) == 1 or user.schedule == "flexible" or candidate.schedule == "flexible":
        schedule_score = 0.6
    else:
        schedule_score = 0.2
    features.append(schedule_score * weights.w_schedule)

    # 4. Limpieza — diferencia normalizada
    cleanliness_score = 1 - abs(user.cleanliness_level - candidate.cleanliness_level) / 4
    features.append(cleanliness_score * weights.w_cleanliness)

    # 5. Ruido — diferencia normalizada
    noise_score = 1 - abs(user.noise_tolerance - candidate.noise_tolerance) / 4
    features.append(noise_score * weights.w_noise)

    # 6. Mascotas — compatibilidad cruzada
    pets_ok = True
    if user.has_pets and not candidate.accepts_pets:
        pets_ok = False
    if candidate.has_pets and not user.accepts_pets:
        pets_ok = False
    features.append((1.0 if pets_ok else 0.0) * weights.w_pets)

    # 7. Tabaco — compatibilidad cruzada
    smoking_ok = True
    if user.smokes and not candidate.accepts_smokers:
        smoking_ok = False
    if candidate.smokes and not user.accepts_smokers:
        smoking_ok = False
    features.append((1.0 if smoking_ok else 0.0) * weights.w_smoking)

    # 8. Edad — si la edad del candidato cae en el rango preferido del usuario
    try:
        from datetime import date
        birth = date.fromisoformat(candidate.birth_date)
        today = date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        age_ok = user.age_range_min <= age <= user.age_range_max
        age_score = 1.0 if age_ok else 0.3
    except Exception:
        age_score = 0.5
    features.append(age_score * weights.w_age)

    # 9. Género — preferencia del usuario vs género del candidato
    gender_ok = (
        user.gender_preference == "any" or
        user.gender_preference == candidate.gender
    )
    features.append((1.0 if gender_ok else 0.0) * weights.w_gender)

    return np.array(features)

def compute_content_score(
    user: UserProfileSchema,
    candidate: UserProfileSchema,
    weights: PreferenceWeightsSchema
) -> float:
    """
    Calcula el content-based score entre user y candidate.
    Retorna un valor en [0, 1].
    """
    vec = build_feature_vector(user, candidate, weights)
    # Score = suma ponderada de compatibilidades (ya están ponderadas por weights)
    return float(np.sum(vec))

def update_embedding_vector(
    user: UserProfileSchema,
    weights: PreferenceWeightsSchema
) -> str:
    """
    Genera el embedding_vector del usuario basado en sus atributos.
    Se guarda como JSON string en Appwrite.
    """
    raw = [
        user.budget_min / 5000,
        user.budget_max / 5000,
        user.preferred_lat / 90 if user.preferred_lat != 0 else 0,
        user.preferred_lng / 180 if user.preferred_lng != 0 else 0,
        user.search_radius_km / 30,
        {"morning": 0.0, "flexible": 0.5, "night": 1.0}.get(user.schedule, 0.5),
        user.cleanliness_level / 5,
        user.noise_tolerance / 5,
        1.0 if user.has_pets else 0.0,
        1.0 if user.accepts_pets else 0.0,
        1.0 if user.smokes else 0.0,
        1.0 if user.accepts_smokers else 0.0,
        user.age_range_min / 99,
        user.age_range_max / 99,
        {"male": 0.0, "any": 0.5, "female": 1.0}.get(user.gender_preference, 0.5),
    ]
    return json.dumps([round(v, 4) for v in raw])