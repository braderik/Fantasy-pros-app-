from typing import Dict, List, Optional, Tuple
import math
from .models import Player, FantasyProPlayer, RosterSlots, Scoring
from .cache import cache_manager


class VORCalculator:
    """Value Over Replacement calculator for fantasy football players"""
    
    # Constants for VOR calculations
    DEFAULT_BUFFER_PERCENTAGE = 0.1  # Additional percentage for replacement level
    TE_PREMIUM_BONUS_MULTIPLIER = 0.1  # TE premium rough estimate multiplier
    INJURY_PENALTIES = {
        "OUT": 1.0,  # 100% penalty (no value if out)
        "DOUBTFUL": 0.7,  # 70% penalty  
        "QUESTIONABLE": 0.15,  # 15% penalty
        "PROBABLE": 0.05   # 5% penalty
    }
    
    def __init__(self):
        self.position_order = ["QB", "RB", "WR", "TE", "K", "DST"]
        self.flex_positions = ["RB", "WR", "TE"]
    
    def calculate_replacement_baselines(self, 
                                     fp_players: List[FantasyProPlayer],
                                     roster_slots: RosterSlots,
                                     num_teams: int = 12,
                                     buffer_percentage: float = None) -> Dict[str, float]:
        """
        Calculate replacement level baselines for each position
        
        Args:
            fp_players: List of FantasyPros players with projections
            roster_slots: League roster configuration
            num_teams: Number of teams in league
            buffer_percentage: Additional percentage of players to consider beyond starters
            
        Returns:
            Dictionary mapping position to replacement baseline points
        """
        if buffer_percentage is None:
            buffer_percentage = self.DEFAULT_BUFFER_PERCENTAGE
            
        baselines = {}
        
        # Group players by position for efficient processing
        players_by_pos = self._group_players_by_position(fp_players)
        
        # Calculate baselines for each position
        for position in self.position_order:
            baselines[position] = self._calculate_position_baseline(
                position, players_by_pos.get(position, []), 
                roster_slots, num_teams, buffer_percentage
            )
        
        return baselines
    
    def _group_players_by_position(self, fp_players: List[FantasyProPlayer]) -> Dict[str, List[FantasyProPlayer]]:
        """Group and sort players by position for efficient processing"""
        players_by_pos = {}
        for player in fp_players:
            pos = player.position
            if pos not in players_by_pos:
                players_by_pos[pos] = []
            players_by_pos[pos].append(player)
        
        # Sort each position by projected points (descending)
        for pos in players_by_pos:
            players_by_pos[pos].sort(key=lambda p: p.ros_points, reverse=True)
        
        return players_by_pos
    
    def _calculate_position_baseline(self, position: str, position_players: List[FantasyProPlayer],
                                   roster_slots: RosterSlots, num_teams: int, 
                                   buffer_percentage: float) -> float:
        """Calculate baseline for a specific position"""
        if not position_players:
            return 0.0
        
        # Get roster requirement for this position
        base_starters = getattr(roster_slots, position, 0)
        
        # Add FLEX consideration for RB/WR/TE
        flex_starters = 0
        if position in self.flex_positions:
            flex_starters = roster_slots.FLEX // len(self.flex_positions)  # Distribute FLEX evenly
        
        total_starters = (base_starters + flex_starters) * num_teams
        
        # Add buffer for replacement level
        replacement_rank = int(total_starters * (1 + buffer_percentage))
        
        # Get replacement level points
        if replacement_rank < len(position_players):
            return position_players[replacement_rank].ros_points
        elif position_players:
            # If we don't have enough players, use the last available
            return position_players[-1].ros_points
        else:
            return 0.0
    
    def calculate_vor(self, 
                     players: List[Player],
                     fp_players: List[FantasyProPlayer],
                     roster_slots: RosterSlots,
                     scoring: Scoring,
                     te_premium: bool = False,
                     num_teams: int = 12) -> Dict[str, float]:
        """
        Calculate VOR for all players
        
        Returns:
            Dictionary mapping player_id to VOR value
        """
        # Get replacement baselines
        baselines = self.calculate_replacement_baselines(fp_players, roster_slots, num_teams)
        
        # Create lookup for FantasyPros data
        fp_lookup = {}
        for fp_player in fp_players:
            if fp_player.fp_slug:
                fp_lookup[fp_player.fp_slug] = fp_player
        
        vor_values = {}
        
        for player in players:
            vor = 0.0
            
            if player.fp_slug and player.fp_slug in fp_lookup:
                fp_player = fp_lookup[player.fp_slug]
                
                # Get baseline for this position
                baseline = baselines.get(player.position, 0.0)
                
                # Calculate raw VOR
                raw_vor = fp_player.ros_points - baseline
                
                # Apply TE premium if applicable
                if te_premium and player.position == "TE":
                    # Assume TE premium adds bonus based on projected points
                    # This is a rough estimate - would need actual reception projections
                    te_bonus = fp_player.ros_points * self.TE_PREMIUM_BONUS_MULTIPLIER
                    raw_vor += te_bonus
                
                vor = raw_vor
            
            vor_values[player.id] = max(vor, 0.0)  # VOR can't be negative
        
        return vor_values
    
    def get_positional_rankings(self, 
                               players: List[Player],
                               vor_values: Dict[str, float]) -> Dict[str, List[Player]]:
        """Get players ranked by VOR within each position"""
        rankings = {}
        
        # Group by position
        by_position = {}
        for player in players:
            pos = player.position
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)
        
        # Sort each position by VOR
        for pos, pos_players in by_position.items():
            sorted_players = sorted(pos_players, 
                                  key=lambda p: vor_values.get(p.id, 0.0), 
                                  reverse=True)
            rankings[pos] = sorted_players
        
        return rankings
    
    def calculate_lineup_vor(self, 
                           lineup_players: List[Player],
                           vor_values: Dict[str, float],
                           roster_slots: RosterSlots) -> float:
        """
        Calculate total VOR for an optimal lineup from given players
        
        This finds the best possible starting lineup and calculates total VOR
        """
        # Group players by position with their VOR
        position_players = {}
        for player in lineup_players:
            pos = player.position
            vor = vor_values.get(player.id, 0.0)
            
            if pos not in position_players:
                position_players[pos] = []
            position_players[pos].append((player, vor))
        
        # Sort each position by VOR
        for pos in position_players:
            position_players[pos].sort(key=lambda x: x[1], reverse=True)
        
        total_vor = 0.0
        used_players = set()
        
        # Fill required positions first
        for pos in ["QB", "RB", "WR", "TE", "K", "DST"]:
            required = getattr(roster_slots, pos, 0)
            available = position_players.get(pos, [])
            
            for i in range(min(required, len(available))):
                player, vor = available[i]
                if player.id not in used_players:
                    total_vor += vor
                    used_players.add(player.id)
        
        # Fill FLEX positions with remaining best players
        flex_candidates = []
        for pos in self.flex_positions:
            available = position_players.get(pos, [])
            for player, vor in available:
                if player.id not in used_players:
                    flex_candidates.append((player, vor))
        
        # Sort FLEX candidates by VOR and take the best
        flex_candidates.sort(key=lambda x: x[1], reverse=True)
        
        for i in range(min(roster_slots.FLEX, len(flex_candidates))):
            player, vor = flex_candidates[i]
            total_vor += vor
            used_players.add(player.id)
        
        return total_vor
    
    def apply_injury_penalty(self, vor: float, injury_status: Optional[str]) -> float:
        """
        Apply penalty for injury status
        
        Args:
            vor: Original VOR value
            injury_status: Player's injury status (OUT, DOUBTFUL, QUESTIONABLE, PROBABLE)
            
        Returns:
            VOR value adjusted for injury status
        """
        if not injury_status:
            return vor
        
        status = injury_status.upper()
        if status in self.INJURY_PENALTIES:
            penalty_factor = self.INJURY_PENALTIES[status]
            return vor * (1 - penalty_factor)
        
        return vor

# Global VOR calculator instance
vor_calculator = VORCalculator()