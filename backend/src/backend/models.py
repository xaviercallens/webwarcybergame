from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class PlayerBase(SQLModel):
    username: str = Field(index=True, unique=True)
    xp: int = Field(default=0)
    rank: str = Field(default="SCRIPT_KIDDIE")
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    win_streak: int = Field(default=0)
    best_streak: int = Field(default=0)

class Player(PlayerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PlayerCreate(SQLModel):
    username: str
    password: str

class PlayerPublic(PlayerBase):
    id: int
    created_at: datetime

class Token(SQLModel):
    access_token: str
    token_type: str
    player: PlayerPublic