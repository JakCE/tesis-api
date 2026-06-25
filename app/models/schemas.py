from pydantic import BaseModel
from typing import Optional

class UserProfileSchema(BaseModel):
    id:                str
    user_id:           str
    gender:            str
    birth_date:        str
    occupation:        str
    budget_min:        float
    budget_max:        float
    preferred_zone:    str
    preferred_lat:     float
    preferred_lng:     float
    search_radius_km:  float
    schedule:          str
    cleanliness_level: int
    noise_tolerance:   int
    has_pets:          bool
    accepts_pets:      bool
    smokes:            bool
    accepts_smokers:   bool
    has_car:           bool
    age_range_min:     int
    age_range_max:     int
    gender_preference: str
    bio:               Optional[str] = ""
    embedding_vector:  Optional[str] = ""
    is_visible:        bool

class PreferenceWeightsSchema(BaseModel):
    user_id:       str
    w_budget:      float = 0.20
    w_zone:        float = 0.20
    w_schedule:    float = 0.15
    w_cleanliness: float = 0.15
    w_noise:       float = 0.10
    w_pets:        float = 0.05
    w_smoking:     float = 0.05
    w_age:         float = 0.05
    w_gender:      float = 0.05
    alpha:         float = 0.70

class RecommendationRequest(BaseModel):
    user_id:     str
    limit:       int = 10

class RecommendationResult(BaseModel):
    user_id:       str
    content_score: float
    collab_score:  float
    hybrid_score:  float
    alpha_used:    float

class InteractionRequest(BaseModel):
    from_user_id: str
    to_user_id:   str
    action:       str  # like / dislike / skip

class MatchRequest(BaseModel):
    user_a_id:           str
    user_b_id:           str
    compatibility_score: float

class RecoverPasswordRequest(BaseModel):
    email:        str
    new_password: str

class WeightsSaveRequest(BaseModel):
    w_budget:      float
    w_zone:        float
    w_schedule:    float
    w_cleanliness: float
    w_noise:       float
    w_pets:        float
    w_smoking:     float
    w_age:         float
    w_gender:      float