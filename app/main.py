from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import recommendations, interactions, matches, weights, explain, auth

app = FastAPI(title="Roomie Matching API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://tesis-roomie-front.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations.router)
app.include_router(interactions.router)
app.include_router(matches.router)
app.include_router(weights.router)
app.include_router(explain.router)
app.include_router(auth.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug/appwrite")
def debug_appwrite():
    """Verifica que la API key puede leer la DB de Appwrite."""
    try:
        from app.services.appwrite_service import tablesdb, DB_ID, COLLECTIONS
        res = tablesdb.list_rows(
            database_id = DB_ID,
            table_id    = COLLECTIONS["profiles"],
        )
        return {
            "status": "ok",
            "keys":   list(res.keys()),
            "total":  res.get("total"),
            "sample": list(res.values())[1][:1] if len(res) > 1 else [],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
