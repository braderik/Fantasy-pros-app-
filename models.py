from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Union
from datetime import datetime


class ScoringBonus(BaseModel):
    """Scoring bonuses for achievements"""
    rec_100: int = Field(default=0, ge=0, description="Points for 100+ receiving yards")
    rush_100: int = Field(default=0, ge=0, description="Points for 100+ rushing yards")
    rec_200: int = Field(default=0, ge=0, description="Points for 200+ receiving yards") 
    pass_300: int = Field(default=0, ge=0, description="Points for 300+ passing yards")


class Scoring(BaseModel):
    """League scoring configuration"""
    format: str = Field(default="PPR", description="PPR, Half, or Standard")
    pass_td: int = Field(default=4, ge=0, le=10, description="Points for passing touchdowns")
    bonus: ScoringBonus = Field(default_factory=ScoringBonus)
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        allowed_formats = ["PPR", "HALF", "STANDARD", "0.5PPR", "HALF_PPR"]
        if v.upper() not in allowed_formats:
            raise ValueError(f"Scoring format must be one of {allowed_formats}")
        return v.upper()


class RosterSlots(BaseModel):
    """League roster slot configuration"""
    QB: int = Field(default=1, ge=0, le=4, description="Starting QB slots")
    RB: int = Field(default=2, ge=0, le=6, description="Starting RB slots")
    WR: int = Field(default=2, ge=0, le=6, description="Starting WR slots")
    TE: int = Field(default=1, ge=0, le=4, description="Starting TE slots")
    FLEX: int = Field(default=1, ge=0, le=4, description="FLEX slots")
    SUPERFLEX: int = Field(default=0, ge=0, le=2, description="SuperFlex slots")
    BENCH: int = Field(default=6, ge=0, le=15, description="Bench slots")
    
    @field_validator('QB', 'RB', 'WR', 'TE', 'FLEX', 'SUPERFLEX', 'BENCH')
    @classmethod
    def validate_roster_slots(cls, v):
        if v < 0:
            raise ValueError("Roster slots cannot be negative")
        return v

class LeagueConfig(BaseModel):
    """League configuration"""
    platform: Optional[str] = None
    league_id: Optional[str] = None
    scoring: Scoring = Field(default_factory=Scoring)
    roster_slots: RosterSlots = Field(default_factory=RosterSlots)
    te_premium: bool = False

class Player(BaseModel):
    """Fantasy football player"""
    id: str = Field(..., description="Platform-specific player ID", min_length=1)
    name: str = Field(..., min_length=1, description="Player full name")
    position: str = Field(..., description="Player position")
    team: str = Field(..., min_length=1, max_length=5, description="NFL team abbreviation")
    player_key: Optional[str] = None
    fp_slug: Optional[str] = Field(None, description="FantasyPros player slug")
    
    # FantasyPros data
    ecr_rank: Optional[int] = Field(None, ge=1, description="Expert consensus ranking")
    ros_points: Optional[float] = Field(None, ge=0.0, description="Rest of season projected points")
    vor: Optional[float] = Field(None, description="Value over replacement")
    
    # Additional metadata
    injury_status: Optional[str] = None
    bye_week: Optional[int] = Field(None, ge=1, le=18, description="Bye week number")
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, v):
        allowed_positions = ["QB", "RB", "WR", "TE", "K", "DST", "DEF"]
        if v.upper() not in allowed_positions:
            raise ValueError(f"Position must be one of {allowed_positions}")
        return v.upper()
    
    @field_validator('injury_status')
    @classmethod
    def validate_injury_status(cls, v):
        if v is None:
            return v
        allowed_statuses = ["HEALTHY", "QUESTIONABLE", "DOUBTFUL", "OUT", "IR", "PUP", "PROBABLE"]
        if v.upper() not in allowed_statuses:
            raise ValueError(f"Injury status must be one of {allowed_statuses}")
        return v.upper()


class Team(BaseModel):
    """Fantasy team"""
    id: str = Field(..., min_length=1, description="Unique team identifier")
    name: str = Field(..., min_length=1, description="Team name")
    owner: Optional[str] = None


class Roster(BaseModel):
    """Team roster"""
    team_id: str = Field(..., min_length=1, description="Team identifier")
    players: List[Player] = Field(..., description="List of players on roster")
    
    @field_validator('players')
    @classmethod
    def validate_roster_size(cls, v):
        if len(v) > 25:  # Reasonable maximum roster size
            raise ValueError("Roster cannot exceed 25 players")
        return v

class TradePlayer(BaseModel):
    """Player in a trade proposal"""
    player: str = Field(..., min_length=1, description="Player name")
    pos: str = Field(..., description="Player position")
    vor: float = Field(..., description="Value over replacement")
    
    @field_validator('pos')
    @classmethod
    def validate_position(cls, v):
        allowed_positions = ["QB", "RB", "WR", "TE", "K", "DST", "DEF"]
        if v.upper() not in allowed_positions:
            raise ValueError(f"Position must be one of {allowed_positions}")
        return v.upper()


class TradeIdea(BaseModel):
    """Trade proposal between teams"""
    send: List[TradePlayer] = Field(..., min_items=1, max_items=5, description="Players to send")
    receive: List[TradePlayer] = Field(..., min_items=1, max_items=5, description="Players to receive")
    score_me: float = Field(..., description="VOR improvement for my team")
    score_them: float = Field(..., description="VOR improvement for their team")
    notes: str = Field(..., description="Trade analysis notes")
    
    @field_validator('send', 'receive')
    @classmethod
    def validate_trade_balance(cls, v):
        if len(v) > 5:
            raise ValueError("Cannot trade more than 5 players per side")
        return v


class TradeRequest(BaseModel):
    """Request for trade ideas"""
    my_team_id: str = Field(..., min_length=1, description="Requesting team ID")
    max_players_per_side: int = Field(default=2, ge=1, le=5, description="Maximum players per side")
    consider_2_for_1: bool = Field(default=True, description="Whether to consider uneven trades")


class TradeResponse(BaseModel):
    """Response containing trade ideas"""
    ideas: List[TradeIdea] = Field(..., description="List of trade proposals")
    
    @field_validator('ideas')
    @classmethod
    def validate_ideas_limit(cls, v):
        if len(v) > 100:
            raise ValueError("Too many trade ideas returned, maximum is 100")
        return v

class FantasyProPlayer(BaseModel):
    """FantasyPros player data"""
    player_name: str = Field(..., min_length=1, description="Player full name")
    position: str = Field(..., description="Player position")
    team: str = Field(..., min_length=1, max_length=5, description="NFL team abbreviation")
    fp_id: Optional[str] = None
    fp_slug: Optional[str] = None
    ecr_rank: int = Field(..., ge=1, description="Expert consensus ranking")
    ros_points: float = Field(..., ge=0.0, description="Rest of season projected points")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    @field_validator('position')
    @classmethod
    def validate_fp_position(cls, v):
        allowed_positions = ["QB", "RB", "WR", "TE", "K", "DST", "DEF"]
        if v.upper() not in allowed_positions:
            raise ValueError(f"Position must be one of {allowed_positions}")
        return v.upper()


class PlayerMapping(BaseModel):
    """Mapping between platform player ID and FantasyPros slug"""
    platform: str = Field(..., min_length=1, description="League platform name")
    platform_player_id: str = Field(..., min_length=1, description="Platform-specific player ID")
    fp_slug: str = Field(..., min_length=1, description="FantasyPros player slug")
    player_name: str = Field(..., min_length=1, description="Player full name")
    position: str = Field(..., description="Player position")
    team: str = Field(..., min_length=1, max_length=5, description="NFL team abbreviation")
    manual_override: bool = Field(default=False, description="Whether mapping was manually created")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        allowed_platforms = ["YAHOO", "ESPN", "NFL", "SLEEPER", "CBS"]
        if v.upper() not in allowed_platforms:
            raise ValueError(f"Platform must be one of {allowed_platforms}")
        return v.upper()
    
    @field_validator('position')
    @classmethod
    def validate_mapping_position(cls, v):
        allowed_positions = ["QB", "RB", "WR", "TE", "K", "DST", "DEF"]
        if v.upper() not in allowed_positions:
            raise ValueError(f"Position must be one of {allowed_positions}")
        return v.upper()


class CacheEntry(BaseModel):
    """Generic cache entry"""
    key: str = Field(..., min_length=1, description="Cache key")
    value: str = Field(..., description="Cached value as JSON string")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    @field_validator('expires_at')
    @classmethod
    def validate_expiration(cls, v, info):
        if hasattr(info, 'data') and 'created_at' in info.data and v <= info.data['created_at']:
            raise ValueError("Expiration time must be after creation time")
        return v