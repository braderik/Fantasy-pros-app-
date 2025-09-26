from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime

class ScoringBonus(BaseModel):
    """Scoring bonuses for achievements"""
    rec_100: int = 0
    rush_100: int = 0
    rec_200: int = 0
    pass_300: int = 0

class Scoring(BaseModel):
    """League scoring configuration"""
    format: str = Field(default="PPR", description="PPR, Half, or Standard")
    pass_td: int = Field(default=4, description="Points for passing touchdowns")
    bonus: ScoringBonus = Field(default_factory=ScoringBonus)

class RosterSlots(BaseModel):
    """League roster slot configuration"""
    QB: int = 1
    RB: int = 2
    WR: int = 2
    TE: int = 1
    FLEX: int = 1
    SUPERFLEX: int = 0
    BENCH: int = 6

class LeagueConfig(BaseModel):
    """League configuration"""
    platform: Optional[str] = None
    league_id: Optional[str] = None
    scoring: Scoring = Field(default_factory=Scoring)
    roster_slots: RosterSlots = Field(default_factory=RosterSlots)
    te_premium: bool = False

class Player(BaseModel):
    """Fantasy football player"""
    id: str = Field(..., description="Platform-specific player ID")
    name: str
    position: str
    team: str
    player_key: Optional[str] = None
    fp_slug: Optional[str] = Field(None, description="FantasyPros player slug")
    
    # FantasyPros data
    ecr_rank: Optional[int] = None
    ros_points: Optional[float] = None
    vor: Optional[float] = None
    
    # Additional metadata
    injury_status: Optional[str] = None
    bye_week: Optional[int] = None

class Team(BaseModel):
    """Fantasy team"""
    id: str
    name: str
    owner: Optional[str] = None

class Roster(BaseModel):
    """Team roster"""
    team_id: str
    players: List[Player]

class TradePlayer(BaseModel):
    """Player in a trade proposal"""
    player: str
    pos: str
    vor: float

class TradeIdea(BaseModel):
    """Trade proposal between teams"""
    send: List[TradePlayer]
    receive: List[TradePlayer]
    score_me: float
    score_them: float
    notes: str

class TradeRequest(BaseModel):
    """Request for trade ideas"""
    my_team_id: str
    max_players_per_side: int = 2
    consider_2_for_1: bool = True

class TradeResponse(BaseModel):
    """Response containing trade ideas"""
    ideas: List[TradeIdea]

class FantasyProPlayer(BaseModel):
    """FantasyPros player data"""
    player_name: str
    position: str
    team: str
    fp_id: Optional[str] = None
    fp_slug: Optional[str] = None
    ecr_rank: int
    ros_points: float
    last_updated: datetime

class PlayerMapping(BaseModel):
    """Mapping between platform player ID and FantasyPros slug"""
    platform: str
    platform_player_id: str
    fp_slug: str
    player_name: str
    position: str
    team: str
    manual_override: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class CacheEntry(BaseModel):
    """Generic cache entry"""
    key: str
    value: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)