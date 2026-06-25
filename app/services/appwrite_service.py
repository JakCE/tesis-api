from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.users import Users
from appwrite.query import Query
from appwrite.id import ID
from app.config import settings
from app.models.schemas import UserProfileSchema, PreferenceWeightsSchema
from typing import Optional, cast

client = Client()
client.set_endpoint(settings.appwrite_endpoint)
client.set_project(settings.appwrite_project_id)
client.set_key(settings.appwrite_api_key)

tablesdb     = TablesDB(client)
users_service = Users(client)

DB_ID = settings.database_id

COLLECTIONS = {
    "profiles":           "user_profiles",
    "weights":            "user_preference_weights",
    "interactions":       "interactions",
    "matches":            "matches",
    "recommendation_log": "recommendation_log",
}

def _doc_to_profile(doc: dict) -> UserProfileSchema:
    return UserProfileSchema(
        id                = doc["$id"],
        user_id           = doc.get("user_id", doc["$id"]),
        gender            = doc.get("gender", "other"),
        birth_date        = doc.get("birth_date", ""),
        occupation        = doc.get("occupation", "other"),
        budget_min        = doc.get("budget_min", 0),
        budget_max        = doc.get("budget_max", 0),
        preferred_zone    = doc.get("preferred_zone", ""),
        preferred_lat     = doc.get("preferred_lat", 0),
        preferred_lng     = doc.get("preferred_lng", 0),
        search_radius_km  = doc.get("search_radius_km", 5),
        schedule          = doc.get("schedule", "flexible"),
        cleanliness_level = doc.get("cleanliness_level", 3),
        noise_tolerance   = doc.get("noise_tolerance", 3),
        has_pets          = doc.get("has_pets", False),
        accepts_pets      = doc.get("accepts_pets", False),
        smokes            = doc.get("smokes", False),
        accepts_smokers   = doc.get("accepts_smokers", False),
        has_car           = doc.get("has_car", False),
        age_range_min     = doc.get("age_range_min", 18),
        age_range_max     = doc.get("age_range_max", 99),
        gender_preference = doc.get("gender_preference", "any"),
        bio               = doc.get("bio", ""),
        embedding_vector  = doc.get("embedding_vector", ""),
        is_visible        = doc.get("is_visible", True),
    )

def get_visible_profiles(exclude_user_id: str) -> list[UserProfileSchema]:
    res = cast(dict, tablesdb.list_rows(
        database_id = DB_ID,
        table_id    = COLLECTIONS["profiles"],
        queries     = [
            Query.equal("is_visible", True),
            Query.limit(100),
        ]
    ))
    return [
        _doc_to_profile(doc)
        for doc in res["rows"]
        if doc["$id"] != exclude_user_id
    ]

def get_user_profile(user_id: str) -> Optional[UserProfileSchema]:
    try:
        doc = cast(dict, tablesdb.get_row(
            database_id = DB_ID,
            table_id    = COLLECTIONS["profiles"],
            row_id      = user_id,
        ))
        return _doc_to_profile(doc)
    except Exception:
        return None

def get_user_weights(user_id: str) -> PreferenceWeightsSchema:
    try:
        res = cast(dict, tablesdb.list_rows(
            database_id = DB_ID,
            table_id    = COLLECTIONS["weights"],
            queries     = [Query.equal("user_id", user_id)]
        ))
        if res["total"] > 0:
            doc: dict = res["rows"][0]
            return PreferenceWeightsSchema(
                user_id       = user_id,
                w_budget      = doc.get("w_budget", 0.20),
                w_zone        = doc.get("w_zone", 0.20),
                w_schedule    = doc.get("w_schedule", 0.15),
                w_cleanliness = doc.get("w_cleanliness", 0.15),
                w_noise       = doc.get("w_noise", 0.10),
                w_pets        = doc.get("w_pets", 0.05),
                w_smoking     = doc.get("w_smoking", 0.05),
                w_age         = doc.get("w_age", 0.05),
                w_gender      = doc.get("w_gender", 0.05),
                alpha         = doc.get("alpha", 0.70),
            )
    except Exception:
        pass
    return PreferenceWeightsSchema(user_id=user_id)

def save_user_weights(user_id: str, weights: dict) -> None:
    res = cast(dict, tablesdb.list_rows(
        database_id = DB_ID,
        table_id    = COLLECTIONS["weights"],
        queries     = [Query.equal("user_id", user_id)]
    ))
    data = {"user_id": user_id, **weights}
    if res["total"] > 0:
        row_id = res["rows"][0]["$id"]
        tablesdb.update_row(
            database_id = DB_ID,
            table_id    = COLLECTIONS["weights"],
            row_id      = row_id,
            data        = weights,
        )
    else:
        tablesdb.create_row(
            database_id = DB_ID,
            table_id    = COLLECTIONS["weights"],
            row_id      = ID.unique(),
            data        = data,
        )

def get_all_interactions() -> list[dict]:
    res = cast(dict, tablesdb.list_rows(
        database_id = DB_ID,
        table_id    = COLLECTIONS["interactions"],
        queries     = [Query.limit(500)]
    ))
    return res["rows"]

def save_recommendation_log(
    user_id: str,
    recommended_user_id: str,
    content_score: float,
    collab_score: float,
    hybrid_score: float,
    alpha_used: float,
    model_version: str = "v1.0"
) -> None:
    tablesdb.create_row(
        database_id = DB_ID,
        table_id    = COLLECTIONS["recommendation_log"],
        row_id      = ID.unique(),
        data        = {
            "user_id":             user_id,
            "recommended_user_id": recommended_user_id,
            "content_score":       round(content_score, 4),
            "collab_score":        round(collab_score, 4),
            "hybrid_score":        round(hybrid_score, 4),
            "alpha_used":          alpha_used,
            "model_version":       model_version,
            "was_interacted":      False,
        }
    )
