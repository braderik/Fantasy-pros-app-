import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from .models import PlayerMapping, CacheEntry, FantasyProPlayer

class CacheManager:
    """SQLite-based cache manager for player mappings and API responses"""
    
    def __init__(self, db_path: str = "trade_finder.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    platform_player_id TEXT NOT NULL,
                    fp_slug TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    team TEXT NOT NULL,
                    manual_override BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, platform_player_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fantasypros_players (
                    fp_slug TEXT PRIMARY KEY,
                    player_name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    team TEXT NOT NULL,
                    fp_id TEXT,
                    ecr_rank INTEGER NOT NULL,
                    ros_points REAL NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context management"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def set_cache(self, key: str, value: Any, ttl_hours: int = 24):
        """Store a value in cache with TTL"""
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_entries (key, value, expires_at)
                VALUES (?, ?, ?)
            """, (key, value_str, expires_at))
            conn.commit()
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache if not expired"""
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT value, expires_at FROM cache_entries 
                WHERE key = ? AND expires_at > CURRENT_TIMESTAMP
            """, (key,)).fetchone()
            
            if row:
                try:
                    return json.loads(row['value'])
                except json.JSONDecodeError:
                    return row['value']
            return None
    
    def clear_expired_cache(self):
        """Remove expired cache entries"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM cache_entries WHERE expires_at <= CURRENT_TIMESTAMP")
            conn.commit()
    
    def save_player_mapping(self, mapping: PlayerMapping):
        """Save a player mapping"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO player_mappings 
                (platform, platform_player_id, fp_slug, player_name, position, team, manual_override)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                mapping.platform, mapping.platform_player_id, mapping.fp_slug,
                mapping.player_name, mapping.position, mapping.team, mapping.manual_override
            ))
            conn.commit()
    
    def get_player_mapping(self, platform: str, platform_player_id: str) -> Optional[PlayerMapping]:
        """Get player mapping by platform and player ID"""
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM player_mappings 
                WHERE platform = ? AND platform_player_id = ?
            """, (platform, platform_player_id)).fetchone()
            
            if row:
                return PlayerMapping(
                    platform=row['platform'],
                    platform_player_id=row['platform_player_id'],
                    fp_slug=row['fp_slug'],
                    player_name=row['player_name'],
                    position=row['position'],
                    team=row['team'],
                    manual_override=row['manual_override'],
                    created_at=row['created_at']
                )
            return None
    
    def get_unmapped_players(self, platform: str, player_ids: List[str]) -> List[str]:
        """Get list of player IDs that don't have mappings"""
        if not player_ids:
            return []
            
        placeholders = ','.join(['?' for _ in player_ids])
        with self.get_connection() as conn:
            mapped_ids = conn.execute(f"""
                SELECT platform_player_id FROM player_mappings 
                WHERE platform = ? AND platform_player_id IN ({placeholders})
            """, [platform] + player_ids).fetchall()
            
            mapped_set = {row['platform_player_id'] for row in mapped_ids}
            return [pid for pid in player_ids if pid not in mapped_set]
    
    def save_fantasypros_players(self, players: List[FantasyProPlayer]):
        """Save FantasyPros player data"""
        with self.get_connection() as conn:
            for player in players:
                conn.execute("""
                    INSERT OR REPLACE INTO fantasypros_players 
                    (fp_slug, player_name, position, team, fp_id, ecr_rank, ros_points, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player.fp_slug, player.player_name, player.position, player.team,
                    player.fp_id, player.ecr_rank, player.ros_points, player.last_updated
                ))
            conn.commit()
    
    def get_fantasypros_player(self, fp_slug: str) -> Optional[FantasyProPlayer]:
        """Get FantasyPros player data by slug"""
        with self.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM fantasypros_players WHERE fp_slug = ?
            """, (fp_slug,)).fetchone()
            
            if row:
                return FantasyProPlayer(
                    player_name=row['player_name'],
                    position=row['position'],
                    team=row['team'],
                    fp_id=row['fp_id'],
                    fp_slug=row['fp_slug'],
                    ecr_rank=row['ecr_rank'],
                    ros_points=row['ros_points'],
                    last_updated=row['last_updated']
                )
            return None
    
    def get_all_fantasypros_players(self) -> List[FantasyProPlayer]:
        """Get all FantasyPros player data"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM fantasypros_players ORDER BY ecr_rank").fetchall()
            
            return [
                FantasyProPlayer(
                    player_name=row['player_name'],
                    position=row['position'],
                    team=row['team'],
                    fp_id=row['fp_id'],
                    fp_slug=row['fp_slug'],
                    ecr_rank=row['ecr_rank'],
                    ros_points=row['ros_points'],
                    last_updated=row['last_updated']
                ) for row in rows
            ]

# Global cache instance
cache_manager = CacheManager()