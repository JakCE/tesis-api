from fastapi import APIRouter, HTTPException
from app.models.schemas import InteractionRequest
from app.services.appwrite_service import tablesdb, DB_ID, COLLECTIONS
from appwrite.id import ID
from appwrite.query import Query
from typing import cast

router = APIRouter(prefix="/interactions", tags=["interactions"])

@router.post("/", status_code=201)
def save_interaction(request: InteractionRequest):
    if request.action not in ("like", "dislike", "skip"):
        raise HTTPException(status_code=400, detail="action must be like, dislike or skip")

    doc = cast(dict, tablesdb.create_row(
        database_id = DB_ID,
        table_id    = COLLECTIONS["interactions"],
        row_id      = ID.unique(),
        data        = {
            "from_user_id": request.from_user_id,
            "to_user_id":   request.to_user_id,
            "action":       request.action,
        }
    ))
    return {"id": doc["$id"], "status": "saved"}

@router.get("/mutual/{from_user_id}/{to_user_id}")
def check_mutual_like(from_user_id: str, to_user_id: str):
    res = cast(dict, tablesdb.list_rows(
        database_id = DB_ID,
        table_id    = COLLECTIONS["interactions"],
        queries     = [
            Query.equal("from_user_id", to_user_id),
            Query.equal("to_user_id", from_user_id),
            Query.equal("action", "like"),
            Query.limit(1),
        ]
    ))
    return {"mutual": res.get("total", 0) > 0}

@router.get("/seen/{user_id}")
def get_seen_user_ids(user_id: str):
    # "skip" no se considera decision definitiva: el perfil debe poder
    # volver a aparecer en el feed tras un reload. Solo like/dislike excluyen.
    res = cast(dict, tablesdb.list_rows(
        database_id = DB_ID,
        table_id    = COLLECTIONS["interactions"],
        queries     = [
            Query.equal("from_user_id", user_id),
            Query.equal("action", ["like", "dislike"]),
            Query.limit(500),
        ]
    ))
    ids = [row["to_user_id"] for row in res.get("rows", [])]
    return {"user_ids": ids}
