from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserPublic(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    login: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class CommunityOut(BaseModel):
    id: int
    name: str
    description: str | None
    min_transactions: int = 0


class CommunityOverviewOut(BaseModel):
    id: int
    name: str
    description: str | None
    min_transactions: int
    is_member: bool
    transactions_needed: int


class CommunitiesOverviewResponse(BaseModel):
    total_tx_count: int
    communities: list[CommunityOverviewOut]


class CashbackOut(BaseModel):
    id: int
    amount: float
    place: int
    created_at: str | None


class PostOut(BaseModel):
    id: int
    id_sender: int
    id_community: int
    title: str | None
    text: str | None
    rating: int
    created_at: str | None
