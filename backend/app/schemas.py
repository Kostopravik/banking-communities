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
    category_key: str | None = None


class CommunityOverviewOut(BaseModel):
    id: int
    name: str
    description: str | None
    min_transactions: int
    is_member: bool
    transactions_needed: int
    category_key: str | None = None
    category_operations_count: int = 0
    mcc_operations_required: int = 3


class CommunitiesOverviewResponse(BaseModel):
    total_operations: int
    communities: list[CommunityOverviewOut]


class CashbackOut(BaseModel):
    id: int
    amount: float
    place: int
    created_at: str | None
    category_key: str | None = None
    category_label: str | None = None


class CashbackOpportunityOut(BaseModel):
    """Кэшбэк, привязанный к MCC/категории; разблокируется при ≥3 операциях в категории в Neo4j."""

    id: int
    amount: float
    place_mcc: int
    category_key: str | None
    category_label: str | None
    operations_in_category: int
    operations_required: int
    eligible: bool
    accrued: bool
    hint: str


class BenefitOut(BaseModel):
    id: int
    title: str
    percent: int
    description: str | None
    community_id: int
    community_name: str
    is_active: bool
    operations_needed_to_join: int
    hint: str


class PostOut(BaseModel):
    id: int
    id_sender: int
    id_community: int
    title: str | None
    text: str | None
    rating: int
    created_at: str | None
    like_count: int = 0
    liked_by_me: bool = False


class PostCreate(BaseModel):
    id_community: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=225)
    text: str = Field(..., min_length=1, max_length=8000)


class CommentOut(BaseModel):
    id: int
    id_sender: int
    sender_name: str
    message: str
    created_at: str | None
    id_parent: int | None = None
    reply_to_name: str | None = None


class CommentCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    parent_id: int | None = Field(None, ge=1)
