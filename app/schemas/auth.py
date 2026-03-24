from typing import Optional, List
from pydantic import BaseModel, Field


# ---- Token / Auth ----

class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str                            # auth_subject (UID)
    email: Optional[str] = None
    roles: List[str] = []


class DevTokenRequest(BaseModel):
    """Request body for the dev token endpoint."""
    email: str = Field(..., example="dev@meddiag.com")
    role: str = Field("patient", example="patient")
    display_name: Optional[str] = Field(None, example="Dev User")


class DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Current user info ----

class UserOut(BaseModel):
    id: int
    email: Optional[str] = None
    display_name: Optional[str] = None
    auth_provider: Optional[str] = None
    is_active: bool = True
    roles: List[str] = []

    class Config:
        from_attributes = True
