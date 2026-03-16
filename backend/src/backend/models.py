from typing import Optional
from datetime import datetime
import enum
from sqlmodel import Field, SQLModel

class NodeClass(str, enum.Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"

class EpochPhase(str, enum.Enum):
    PLANNING = "PLANNING"
    SIM = "SIM"
    TRANSITION = "TRANSITION"

class ActionType(str, enum.Enum):
    SCAN = "SCAN"
    BREACH = "BREACH"
    DEFEND = "DEFEND"
    TREATY = "TREATY"

class SentinelStatus(str, enum.Enum):
    IDLE = "IDLE"
    DEPLOYED = "DEPLOYED"

class NotificationType(str, enum.Enum):
    COMBAT = "COMBAT"
    DIPLOMACY = "DIPLOMACY"
    EPOCH = "EPOCH"
    SYSTEM = "SYSTEM"

class Faction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    color: str
    compute_reserves: int = Field(default=1000)
    global_influence_pct: float = Field(default=0.0)

class Node(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    lat: float
    lng: float
    faction_id: Optional[int] = Field(default=None, foreign_key="faction.id")
    defense_level: int = Field(default=100)
    compute_output: int = Field(default=10)
    node_class: NodeClass = Field(default=NodeClass.TIER_1)

class Epoch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    number: int = Field(unique=True, index=True)
    phase: EpochPhase = Field(default=EpochPhase.PLANNING)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

class EpochAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    epoch_id: int = Field(foreign_key="epoch.id")
    player_id: int = Field(foreign_key="player.id")
    action_type: ActionType
    target_node_id: int = Field(foreign_key="node.id")
    cu_committed: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PlayerBase(SQLModel):
    username: str = Field(index=True, unique=True)
    xp: int = Field(default=0)
    rank: str = Field(default="SCRIPT_KIDDIE")
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    win_streak: int = Field(default=0)
    best_streak: int = Field(default=0)
    faction_id: Optional[int] = Field(default=None, foreign_key="faction.id")

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

class Accord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    faction_a_id: int = Field(foreign_key="faction.id")
    faction_b_id: int = Field(foreign_key="faction.id")
    type: str = Field(default="CEASEFIRE") # CEASEFIRE, ALLIANCE, TRADE
    status: str = Field(default="ACTIVE") # ACTIVE, BROKEN
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NewsItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    epoch_id: int = Field(foreign_key="epoch.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Sentinel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    name: str
    status: SentinelStatus = Field(default=SentinelStatus.IDLE)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SentinelPolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sentinel_id: int = Field(foreign_key="sentinel.id")
    persistence_weight: float = Field(default=0.5)
    stealth_weight: float = Field(default=0.5)
    efficiency_weight: float = Field(default=0.5)
    aggression_weight: float = Field(default=0.5)

class SentinelLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sentinel_id: int = Field(foreign_key="sentinel.id")
    epoch_id: int = Field(foreign_key="epoch.id")
    description: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    message: str = Field(index=True)
    type: NotificationType = Field(default=NotificationType.SYSTEM)
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)