"""
Seed script — carga 12 perfiles sintéticos en Appwrite para pruebas de la tesis.
Crea cuentas de auth + documentos en user_profiles + interacciones entre usuarios.

Uso:
    python seed.py            # crea todo
    python seed.py --clean    # elimina los perfiles seed antes de crear
"""

import sys
import json
from typing import cast

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.users import Users
from appwrite.id import ID
from appwrite.exception import AppwriteException

from app.config import settings
from app.models.schemas import UserProfileSchema, PreferenceWeightsSchema
from app.services.content_based import update_embedding_vector

# ──────────────────────────────────────────────
# Cliente Appwrite (admin)
# ──────────────────────────────────────────────
client = Client()
client.set_endpoint(settings.appwrite_endpoint)
client.set_project(settings.appwrite_project_id)
client.set_key(settings.appwrite_api_key)

db    = Databases(client)
users = Users(client)

DB_ID = settings.database_id

COLLECTIONS = {
    "profiles":     "user_profiles",
    "weights":      "user_preference_weights",
    "interactions": "interactions",
}

# ──────────────────────────────────────────────
# Datos de los 12 perfiles sintéticos
# Coordenadas reales de distritos de Lima
# ──────────────────────────────────────────────
PROFILES_DATA = [
    {
        "name": "Lucía Torres",
        "email": "lucia.torres@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "female", "birth_date": "2001-03-15",
            "occupation": "student",
            "budget_min": 400, "budget_max": 700,
            "preferred_zone": "Miraflores",
            "preferred_lat": -12.1211, "preferred_lng": -77.0282,
            "search_radius_km": 5,
            "schedule": "morning", "cleanliness_level": 4, "noise_tolerance": 2,
            "has_pets": False, "accepts_pets": False,
            "smokes": False, "accepts_smokers": False, "has_car": False,
            "age_range_min": 18, "age_range_max": 28,
            "gender_preference": "female",
            "bio": "Estudiante de Medicina, ordenada y tranquila. Busco compañera estudiante.",
        },
    },
    {
        "name": "Carlos Mendoza",
        "email": "carlos.mendoza@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "male", "birth_date": "1998-07-22",
            "occupation": "employed",
            "budget_min": 600, "budget_max": 900,
            "preferred_zone": "San Isidro",
            "preferred_lat": -12.0931, "preferred_lng": -77.0365,
            "search_radius_km": 6,
            "schedule": "flexible", "cleanliness_level": 4, "noise_tolerance": 3,
            "has_pets": False, "accepts_pets": False,
            "smokes": False, "accepts_smokers": False, "has_car": True,
            "age_range_min": 22, "age_range_max": 35,
            "gender_preference": "any",
            "bio": "Ingeniero de software, trabajo remoto. Limpio y respetuoso.",
        },
    },
    {
        "name": "Valeria Quispe",
        "email": "valeria.quispe@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "female", "birth_date": "2000-11-08",
            "occupation": "student",
            "budget_min": 350, "budget_max": 600,
            "preferred_zone": "Barranco",
            "preferred_lat": -12.1473, "preferred_lng": -77.0217,
            "search_radius_km": 4,
            "schedule": "night", "cleanliness_level": 3, "noise_tolerance": 4,
            "has_pets": True, "accepts_pets": True,
            "smokes": False, "accepts_smokers": False, "has_car": False,
            "age_range_min": 18, "age_range_max": 26,
            "gender_preference": "female",
            "bio": "Diseñadora gráfica en formación. Tengo un gato. Ambiente creativo.",
        },
    },
    {
        "name": "Diego Ríos",
        "email": "diego.rios@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "male", "birth_date": "1996-05-30",
            "occupation": "freelancer",
            "budget_min": 500, "budget_max": 800,
            "preferred_zone": "Surco",
            "preferred_lat": -12.1497, "preferred_lng": -76.9972,
            "search_radius_km": 8,
            "schedule": "flexible", "cleanliness_level": 3, "noise_tolerance": 3,
            "has_pets": False, "accepts_pets": True,
            "smokes": False, "accepts_smokers": False, "has_car": True,
            "age_range_min": 22, "age_range_max": 35,
            "gender_preference": "any",
            "bio": "Fotógrafo freelance. Horarios variables, muy tranquilo en casa.",
        },
    },
    {
        "name": "Andrea López",
        "email": "andrea.lopez@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "female", "birth_date": "1997-01-19",
            "occupation": "employed",
            "budget_min": 700, "budget_max": 1000,
            "preferred_zone": "La Molina",
            "preferred_lat": -12.0832, "preferred_lng": -76.9452,
            "search_radius_km": 7,
            "schedule": "morning", "cleanliness_level": 5, "noise_tolerance": 2,
            "has_pets": False, "accepts_pets": False,
            "smokes": False, "accepts_smokers": False, "has_car": True,
            "age_range_min": 23, "age_range_max": 32,
            "gender_preference": "female",
            "bio": "Contadora. Muy ordenada, madrugo para el gym. Casa tranquila.",
        },
    },
    {
        "name": "Sebastián Castro",
        "email": "sebastian.castro@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "male", "birth_date": "2001-09-12",
            "occupation": "student",
            "budget_min": 400, "budget_max": 650,
            "preferred_zone": "San Borja",
            "preferred_lat": -12.1077, "preferred_lng": -77.0002,
            "search_radius_km": 5,
            "schedule": "night", "cleanliness_level": 3, "noise_tolerance": 4,
            "has_pets": False, "accepts_pets": False,
            "smokes": True, "accepts_smokers": True, "has_car": False,
            "age_range_min": 18, "age_range_max": 27,
            "gender_preference": "any",
            "bio": "Estudiante de Comunicaciones. Salgo mucho, gamer de noche.",
        },
    },
    {
        "name": "Camila Rojas",
        "email": "camila.rojas@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "female", "birth_date": "2001-06-25",
            "occupation": "student",
            "budget_min": 350, "budget_max": 550,
            "preferred_zone": "Jesús María",
            "preferred_lat": -12.0733, "preferred_lng": -77.0480,
            "search_radius_km": 4,
            "schedule": "morning", "cleanliness_level": 4, "noise_tolerance": 2,
            "has_pets": False, "accepts_pets": False,
            "smokes": False, "accepts_smokers": False, "has_car": False,
            "age_range_min": 18, "age_range_max": 26,
            "gender_preference": "female",
            "bio": "Psicología UNMSM. Tranquila, me gusta leer y estudiar en casa.",
        },
    },
    {
        "name": "Miguel Flores",
        "email": "miguel.flores@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "male", "birth_date": "1995-12-03",
            "occupation": "employed",
            "budget_min": 500, "budget_max": 750,
            "preferred_zone": "Lince",
            "preferred_lat": -12.0844, "preferred_lng": -77.0358,
            "search_radius_km": 6,
            "schedule": "flexible", "cleanliness_level": 3, "noise_tolerance": 3,
            "has_pets": True, "accepts_pets": True,
            "smokes": False, "accepts_smokers": False, "has_car": False,
            "age_range_min": 24, "age_range_max": 38,
            "gender_preference": "any",
            "bio": "Administrador de empresas. Tengo un perro pequeño, muy amigable.",
        },
    },
    {
        "name": "Isabella Vargas",
        "email": "isabella.vargas@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "female", "birth_date": "1999-04-17",
            "occupation": "freelancer",
            "budget_min": 450, "budget_max": 700,
            "preferred_zone": "San Miguel",
            "preferred_lat": -12.0775, "preferred_lng": -77.0847,
            "search_radius_km": 5,
            "schedule": "flexible", "cleanliness_level": 4, "noise_tolerance": 3,
            "has_pets": False, "accepts_pets": True,
            "smokes": False, "accepts_smokers": False, "has_car": False,
            "age_range_min": 20, "age_range_max": 30,
            "gender_preference": "female",
            "bio": "Marketing digital. Trabajo desde casa. Ambientes creativos y relajados.",
        },
    },
    {
        "name": "Rodrigo Sánchez",
        "email": "rodrigo.sanchez@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "male", "birth_date": "2002-02-28",
            "occupation": "student",
            "budget_min": 300, "budget_max": 500,
            "preferred_zone": "Pueblo Libre",
            "preferred_lat": -12.0774, "preferred_lng": -77.0631,
            "search_radius_km": 4,
            "schedule": "night", "cleanliness_level": 2, "noise_tolerance": 5,
            "has_pets": False, "accepts_pets": False,
            "smokes": True, "accepts_smokers": True, "has_car": False,
            "age_range_min": 18, "age_range_max": 25,
            "gender_preference": "any",
            "bio": "Sistemas UNI. Noctámbulo, música y videojuegos.",
        },
    },
    {
        "name": "Fernanda Díaz",
        "email": "fernanda.diaz@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "female", "birth_date": "1996-08-11",
            "occupation": "employed",
            "budget_min": 600, "budget_max": 850,
            "preferred_zone": "Magdalena del Mar",
            "preferred_lat": -12.0904, "preferred_lng": -77.0720,
            "search_radius_km": 5,
            "schedule": "morning", "cleanliness_level": 5, "noise_tolerance": 2,
            "has_pets": False, "accepts_pets": False,
            "smokes": False, "accepts_smokers": False, "has_car": True,
            "age_range_min": 24, "age_range_max": 35,
            "gender_preference": "female",
            "bio": "Nutricionista. Muy ordenada y respetuosa. Casa limpia y silenciosa.",
        },
    },
    {
        "name": "Alejandro Chávez",
        "email": "alejandro.chavez@seed.test",
        "password": "Seed1234!",
        "profile": {
            "gender": "male", "birth_date": "1994-10-05",
            "occupation": "freelancer",
            "budget_min": 450, "budget_max": 700,
            "preferred_zone": "Chorrillos",
            "preferred_lat": -12.1700, "preferred_lng": -77.0200,
            "search_radius_km": 8,
            "schedule": "flexible", "cleanliness_level": 3, "noise_tolerance": 3,
            "has_pets": False, "accepts_pets": True,
            "smokes": False, "accepts_smokers": False, "has_car": True,
            "age_range_min": 24, "age_range_max": 40,
            "gender_preference": "any",
            "bio": "Desarrollador web freelance. Tranquilo, respeto los espacios.",
        },
    },
]

# ──────────────────────────────────────────────
# Interacciones seed para calentar el collaborative filter
# (from_index, to_index, action)
# ──────────────────────────────────────────────
INTERACTIONS_SEED = [
    (0, 6, "like"),    # Lucía → Camila
    (0, 5, "dislike"), # Lucía → Sebastián
    (6, 0, "like"),    # Camila → Lucía
    (6, 8, "like"),    # Camila → Isabella
    (1, 3, "like"),    # Carlos → Diego
    (1, 4, "like"),    # Carlos → Andrea
    (1, 11, "like"),   # Carlos → Alejandro
    (3, 1, "like"),    # Diego → Carlos
    (3, 7, "like"),    # Diego → Miguel
    (4, 10, "like"),   # Andrea → Fernanda
    (4, 1, "like"),    # Andrea → Carlos
    (10, 4, "like"),   # Fernanda → Andrea
    (10, 8, "like"),   # Fernanda → Isabella
    (8, 6, "like"),    # Isabella → Camila
    (8, 10, "like"),   # Isabella → Fernanda
    (2, 7, "like"),    # Valeria → Miguel
    (2, 5, "dislike"), # Valeria → Sebastián
    (7, 3, "like"),    # Miguel → Diego
    (7, 11, "like"),   # Miguel → Alejandro
    (5, 9, "like"),    # Sebastián → Rodrigo
    (9, 5, "like"),    # Rodrigo → Sebastián
    (11, 3, "like"),   # Alejandro → Diego
    (11, 7, "like"),   # Alejandro → Miguel
    (0, 8, "skip"),    # Lucía → Isabella
    (1, 2, "skip"),    # Carlos → Valeria
]


def _build_profile_schema(user_id: str, data: dict) -> UserProfileSchema:
    return UserProfileSchema(
        id                = user_id,
        user_id           = user_id,
        gender            = data["gender"],
        birth_date        = data["birth_date"],
        occupation        = data["occupation"],
        budget_min        = data["budget_min"],
        budget_max        = data["budget_max"],
        preferred_zone    = data["preferred_zone"],
        preferred_lat     = data["preferred_lat"],
        preferred_lng     = data["preferred_lng"],
        search_radius_km  = data["search_radius_km"],
        schedule          = data["schedule"],
        cleanliness_level = data["cleanliness_level"],
        noise_tolerance   = data["noise_tolerance"],
        has_pets          = data["has_pets"],
        accepts_pets      = data["accepts_pets"],
        smokes            = data["smokes"],
        accepts_smokers   = data["accepts_smokers"],
        has_car           = data["has_car"],
        age_range_min     = data["age_range_min"],
        age_range_max     = data["age_range_max"],
        gender_preference = data["gender_preference"],
        bio               = data["bio"],
        embedding_vector  = "",
        is_visible        = True,
    )


def clean_seed() -> None:
    print("🗑  Eliminando perfiles seed anteriores...")
    emails = {p["email"] for p in PROFILES_DATA}
    res = cast(dict, db.list_documents(DB_ID, COLLECTIONS["profiles"]))
    for doc in res["documents"]:
        doc_id = doc["$id"]
        # intenta borrar el doc de perfil
        try:
            db.delete_document(DB_ID, COLLECTIONS["profiles"], doc_id)
            print(f"   Perfil eliminado: {doc_id}")
        except AppwriteException:
            pass
        # intenta borrar el usuario auth
        try:
            users.delete(doc_id)
            print(f"   Auth eliminado:   {doc_id}")
        except AppwriteException:
            pass


def run_seed() -> None:
    created_ids: list[str] = []

    print("\n👤 Creando usuarios...\n")
    for entry in PROFILES_DATA:
        name  = entry["name"]
        email = entry["email"]
        pwd   = entry["password"]
        pdata = entry["profile"]

        # 1. Crear cuenta auth
        try:
            user = cast(dict, users.create(
                user_id  = ID.unique(),
                email    = email,
                password = pwd,
                name     = name,
            ))
            uid = user["$id"]
            print(f"  ✔ Auth creado:   {name} ({uid})")
        except AppwriteException as e:
            print(f"  ✘ Auth falló para {name}: {e.message}")
            continue

        # 2. Calcular embedding_vector
        schema  = _build_profile_schema(uid, pdata)
        weights = PreferenceWeightsSchema(user_id=uid)
        embedding = update_embedding_vector(schema, weights)

        # 3. Crear documento en user_profiles
        doc_data = {
            "user_id":           uid,
            "gender":            pdata["gender"],
            "birth_date":        pdata["birth_date"],
            "occupation":        pdata["occupation"],
            "budget_min":        pdata["budget_min"],
            "budget_max":        pdata["budget_max"],
            "preferred_zone":    pdata["preferred_zone"],
            "preferred_lat":     pdata["preferred_lat"],
            "preferred_lng":     pdata["preferred_lng"],
            "search_radius_km":  pdata["search_radius_km"],
            "schedule":          pdata["schedule"],
            "cleanliness_level": pdata["cleanliness_level"],
            "noise_tolerance":   pdata["noise_tolerance"],
            "has_pets":          pdata["has_pets"],
            "accepts_pets":      pdata["accepts_pets"],
            "smokes":            pdata["smokes"],
            "accepts_smokers":   pdata["accepts_smokers"],
            "has_car":           pdata["has_car"],
            "age_range_min":     pdata["age_range_min"],
            "age_range_max":     pdata["age_range_max"],
            "gender_preference": pdata["gender_preference"],
            "bio":               pdata["bio"],
            "embedding_vector":  embedding,
            "is_visible":        True,
        }
        try:
            db.create_document(DB_ID, COLLECTIONS["profiles"], uid, doc_data)
            print(f"  ✔ Perfil creado: {name}")
            created_ids.append(uid)
        except AppwriteException as e:
            print(f"  ✘ Perfil falló para {name}: {e.message}")

    print(f"\n✅ {len(created_ids)} perfiles creados.\n")

    # 4. Crear interacciones
    if len(created_ids) < len(PROFILES_DATA):
        print("⚠  No se crearon todos los perfiles, saltando interacciones.")
        return

    print("🤝 Creando interacciones...\n")
    ok = 0
    for from_idx, to_idx, action in INTERACTIONS_SEED:
        from_id = created_ids[from_idx]
        to_id   = created_ids[to_idx]
        try:
            db.create_document(
                DB_ID,
                COLLECTIONS["interactions"],
                ID.unique(),
                {
                    "from_user_id": from_id,
                    "to_user_id":   to_id,
                    "action":       action,
                }
            )
            ok += 1
        except AppwriteException as e:
            print(f"  ✘ Interacción {from_idx}→{to_idx}: {e.message}")

    print(f"✅ {ok}/{len(INTERACTIONS_SEED)} interacciones creadas.\n")
    print("🎉 Seed completo. Credenciales de prueba:")
    print("   Email:    lucia.torres@seed.test")
    print("   Password: Seed1234!")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean_seed()
    run_seed()
