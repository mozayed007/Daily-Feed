"""User and personalization models"""

from .user import (
    ArticleFeedback,
    OnboardingData,
    PersonalizedDigestModel,
    PersonalizedDigestResponse,
    UserCreate,
    UserInteractionCreate,
    UserInteractionModel,
    UserInteractionResponse,
    UserModel,
    UserPreferencesModel,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserResponse,
    UserStats,
)

__all__ = [
    # SQLAlchemy Models
    "UserModel",
    "UserPreferencesModel",
    "UserInteractionModel",
    "PersonalizedDigestModel",
    # Pydantic Schemas
    "UserCreate",
    "UserResponse",
    "UserPreferencesUpdate",
    "UserPreferencesResponse",
    "UserInteractionCreate",
    "UserInteractionResponse",
    "ArticleFeedback",
    "PersonalizedDigestResponse",
    "OnboardingData",
    "UserStats",
]
