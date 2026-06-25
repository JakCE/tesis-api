from fastapi import APIRouter, HTTPException, Header
from appwrite.query import Query
from appwrite.exception import AppwriteException
from typing import cast, Optional
import secrets
from app.config import settings
from app.models.schemas import RecoverPasswordRequest
from app.services.appwrite_service import users_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/recover-password", status_code=200)
def recover_password(
    request: RecoverPasswordRequest,
    x_recovery_key: Optional[str] = Header(None),
):
    """
    Reset directo de password sin flujo de email: las cuentas de prueba
    usan correos de prueba que nunca podrian completar una verificacion real.
    Busca el usuario por email con la API key (admin) y actualiza el password.

    Protegido por un secreto compartido (header X-Recovery-Key) para que no
    sea invocable por cualquiera en internet que descubra el endpoint —
    sin esto, cualquiera podria resetear la cuenta de cualquier usuario
    con solo conocer su email.
    """
    if not settings.recovery_secret or not x_recovery_key or \
       not secrets.compare_digest(x_recovery_key, settings.recovery_secret):
        raise HTTPException(status_code=401, detail="No autorizado")

    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

    try:
        res = cast(dict, users_service.list(
            queries=[Query.equal("email", request.email)]
        ))
    except AppwriteException as e:
        raise HTTPException(status_code=400, detail=str(e.message))

    if res.get("total", 0) == 0:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")

    user_id = res["users"][0]["$id"]
    try:
        users_service.update_password(user_id=user_id, password=request.new_password)
    except AppwriteException as e:
        raise HTTPException(status_code=400, detail=str(e.message))

    return {"status": "ok"}
