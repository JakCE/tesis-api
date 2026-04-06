from fastapi import APIRouter
from app.models.schemas import MatchRequest
from app.services.appwrite_service import tablesdb, DB_ID, COLLECTIONS
from appwrite.id import ID
from typing import cast

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("/", status_code=201)
def create_match(request: MatchRequest):
    doc = cast(dict, tablesdb.create_row(
        database_id = DB_ID,
        table_id    = COLLECTIONS["matches"],
        row_id      = ID.unique(),
        data        = {
            "user_a_id":           request.user_a_id,
            "user_b_id":           request.user_b_id,
            "compatibility_score": round(request.compatibility_score, 4),
            "status":              "active",
        }
    ))
    return {"id": doc["$id"], "status": "created"}
