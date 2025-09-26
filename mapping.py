import re
from typing import Dict, List, Optional, Tuple
try:
    from .models import Player, PlayerMapping, FantasyProPlayer
    from .cache import cache_manager
    from services.fantasypros import fantasypros_service
except ImportError:
    from models import Player, PlayerMapping, FantasyProPlayer
    from cache import cache_manager
    try:
        from services.fantasypros import fantasypros_service
    except ImportError:
        # Service not available, will be handled in the code
        fantasypros_service = None

class PlayerMappingService:
    """Service for mapping league player IDs to FantasyPros slugs"""
    
    def __init__(self):
        self.name_cache: Dict[str, str] = {}
        self.team_mappings = self._build_team_mappings()
    
    def _build_team_mappings(self) -> Dict[str, List[str]]:
        """Build team name variations for better matching"""
        return {
            "ARI": ["ARI", "ARIZONA", "CARDINALS"],
            "ATL": ["ATL", "ATLANTA", "FALCONS"],
            "BAL": ["BAL", "BALTIMORE", "RAVENS"],
            "BUF": ["BUF", "BUFFALO", "BILLS"],
            "CAR": ["CAR", "CAROLINA", "PANTHERS"],
            "CHI": ["CHI", "CHICAGO", "BEARS"],
            "CIN": ["CIN", "CINCINNATI", "BENGALS"],
            "CLE": ["CLE", "CLEVELAND", "BROWNS"],
            "DAL": ["DAL", "DALLAS", "COWBOYS"],
            "DEN": ["DEN", "DENVER", "BRONCOS"],
            "DET": ["DET", "DETROIT", "LIONS"],
            "GB": ["GB", "GNB", "GREEN BAY", "PACKERS"],
            "HOU": ["HOU", "HOUSTON", "TEXANS"],
            "IND": ["IND", "INDIANAPOLIS", "COLTS"],
            "JAX": ["JAX", "JAC", "JACKSONVILLE", "JAGUARS"],
            "KC": ["KC", "KAN", "KANSAS CITY", "CHIEFS"],
            "LV": ["LV", "LAS", "LAS VEGAS", "RAIDERS"],
            "LAC": ["LAC", "LOS ANGELES", "CHARGERS"],
            "LAR": ["LAR", "LOS ANGELES", "RAMS"],
            "MIA": ["MIA", "MIAMI", "DOLPHINS"],
            "MIN": ["MIN", "MINNESOTA", "VIKINGS"],
            "NE": ["NE", "NEW ENGLAND", "PATRIOTS"],
            "NO": ["NO", "NEW ORLEANS", "SAINTS"],
            "NYG": ["NYG", "NEW YORK", "GIANTS"],
            "NYJ": ["NYJ", "NEW YORK", "JETS"],
            "PHI": ["PHI", "PHILADELPHIA", "EAGLES"],
            "PIT": ["PIT", "PITTSBURGH", "STEELERS"],
            "SEA": ["SEA", "SEATTLE", "SEAHAWKS"],
            "SF": ["SF", "SAN FRANCISCO", "49ERS"],
            "TB": ["TB", "TAMPA BAY", "BUCCANEERS"],
            "TEN": ["TEN", "TENNESSEE", "TITANS"],
            "WAS": ["WAS", "WASHINGTON", "COMMANDERS"]
        }
    
    def normalize_name(self, name: str) -> str:
        """Normalize player name for matching"""
        if not name:
            return ""
        
        # Cache normalized names
        if name in self.name_cache:
            return self.name_cache[name]
        
        # Remove common suffixes and prefixes
        normalized = name.strip().upper()
        
        # Remove Jr., Sr., III, etc.
        normalized = re.sub(r'\s+(JR\.?|SR\.?|III|IV|V)(\s|$)', '', normalized)
        
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Handle common name variations
        replacements = {
            'CHRISTOPHER': 'CHRIS',
            'BENJAMIN': 'BEN',
            'MATTHEW': 'MATT',
            'ANTHONY': 'TONY',
            'ALEXANDER': 'ALEX',
            'NICHOLAS': 'NICK',
            'JONATHAN': 'JON',
            'MICHAEL': 'MIKE',
            'WILLIAM': 'WILL',
            'ROBERT': 'ROB',
            'KENNETH': 'KEN'
        }
        
        for full, short in replacements.items():
            if normalized.startswith(full + ' '):
                normalized = normalized.replace(full + ' ', short + ' ', 1)
                break
        
        self.name_cache[name] = normalized
        return normalized
    
    def normalize_team(self, team: str) -> str:
        """Normalize team abbreviation"""
        if not team:
            return ""
        
        team_upper = team.upper()
        
        # Find matching team
        for standard_abbr, variations in self.team_mappings.items():
            if team_upper in variations:
                return standard_abbr
        
        return team_upper
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (0-1)"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Check if one is a substring of the other (handle nicknames)
        if norm1 in norm2 or norm2 in norm1:
            return 0.9
        
        # Split into words and check overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Jaccard similarity
        return len(intersection) / len(union) if union else 0.0
    
    def find_best_match(self, league_player: Player, 
                       fp_players: List[FantasyProPlayer]) -> Optional[FantasyProPlayer]:
        """Find the best FantasyPros match for a league player"""
        best_match = None
        best_score = 0.0
        
        league_team = self.normalize_team(league_player.team)
        
        for fp_player in fp_players:
            # Position must match exactly
            if league_player.position != fp_player.position:
                continue
            
            # Calculate name similarity
            name_score = self.calculate_name_similarity(league_player.name, fp_player.player_name)
            
            # Team match bonus
            fp_team = self.normalize_team(fp_player.team)
            team_bonus = 0.1 if league_team == fp_team else 0.0
            
            total_score = name_score + team_bonus
            
            if total_score > best_score and total_score >= 0.7:  # Minimum threshold
                best_score = total_score
                best_match = fp_player
        
        return best_match
    
    async def map_players(self, platform: str, players: List[Player]) -> Dict[str, Optional[str]]:
        """Map league players to FantasyPros slugs"""
        mappings = {}
        
        # Get existing mappings from cache
        for player in players:
            existing = cache_manager.get_player_mapping(platform, player.id)
            if existing:
                mappings[player.id] = existing.fp_slug
            else:
                mappings[player.id] = None
        
        # Get unmapped players
        unmapped_ids = [pid for pid, slug in mappings.items() if slug is None]
        unmapped_players = [p for p in players if p.id in unmapped_ids]
        
        if not unmapped_players:
            return mappings
        
        # Get all FantasyPros players for matching
        try:
            fp_players = cache_manager.get_all_fantasypros_players()
            if not fp_players:
                # Fetch from API if cache is empty
                fp_players = await fantasypros_service.get_ros_values()
        except Exception as e:
            print(f"Error fetching FantasyPros players: {e}")
            return mappings
        
        # Attempt automatic mapping
        for player in unmapped_players:
            best_match = self.find_best_match(player, fp_players)
            
            if best_match:
                # Save mapping
                mapping = PlayerMapping(
                    platform=platform,
                    platform_player_id=player.id,
                    fp_slug=best_match.fp_slug or "",
                    player_name=player.name,
                    position=player.position,
                    team=player.team,
                    manual_override=False
                )
                cache_manager.save_player_mapping(mapping)
                mappings[player.id] = mapping.fp_slug
        
        return mappings
    
    def save_manual_mapping(self, platform: str, platform_player_id: str,
                          fp_slug: str, player_name: str, position: str, team: str):
        """Save a manual player mapping override"""
        mapping = PlayerMapping(
            platform=platform,
            platform_player_id=platform_player_id,
            fp_slug=fp_slug,
            player_name=player_name,
            position=position,
            team=team,
            manual_override=True
        )
        cache_manager.save_player_mapping(mapping)
    
    def get_mapping_misses(self, platform: str, players: List[Player]) -> List[Player]:
        """Get list of players that don't have FantasyPros mappings"""
        unmapped = []
        
        for player in players:
            mapping = cache_manager.get_player_mapping(platform, player.id)
            if not mapping:
                unmapped.append(player)
        
        return unmapped

# Global mapping service instance
mapping_service = PlayerMappingService()