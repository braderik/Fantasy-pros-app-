from typing import List, Dict, Tuple, Optional, Set
from itertools import combinations
from .models import Player, Roster, TradeIdea, TradePlayer, RosterSlots, Scoring
from .vor import vor_calculator

class TradeAnalyzer:
    """Analyzes and generates fair fantasy football trade proposals"""
    
    def __init__(self):
        self.min_improvement_threshold = 1.0  # Minimum VOR improvement for both sides
        self.max_trade_size = 3  # Maximum players per side
    
    def generate_trade_ideas(self,
                           my_roster: Roster,
                           all_rosters: List[Roster],
                           vor_values: Dict[str, float],
                           roster_slots: RosterSlots,
                           max_players_per_side: int = 2,
                           consider_2_for_1: bool = True) -> List[TradeIdea]:
        """
        Generate trade ideas between my team and all other teams
        
        Args:
            my_roster: My team's roster
            all_rosters: All league rosters
            vor_values: VOR values for all players
            roster_slots: League roster configuration
            max_players_per_side: Maximum players per side of trade
            consider_2_for_1: Whether to consider 2-for-1 trades
        """
        trade_ideas = []
        
        # Get other team rosters (exclude mine)
        other_rosters = [r for r in all_rosters if r.team_id != my_roster.team_id]
        
        for other_roster in other_rosters:
            # Generate trades between my team and this team
            team_trades = self._generate_team_trades(
                my_roster, other_roster, vor_values, roster_slots,
                max_players_per_side, consider_2_for_1
            )
            trade_ideas.extend(team_trades)
        
        # Sort by combined benefit (both teams improve)
        trade_ideas.sort(key=lambda t: t.score_me + t.score_them, reverse=True)
        
        # Return top trades
        return trade_ideas[:50]  # Limit to top 50 trades
    
    def _generate_team_trades(self,
                            my_roster: Roster,
                            their_roster: Roster,
                            vor_values: Dict[str, float],
                            roster_slots: RosterSlots,
                            max_players_per_side: int,
                            consider_2_for_1: bool) -> List[TradeIdea]:
        """Generate all possible trades between two specific teams"""
        trades = []
        
        # Get non-bench players for both teams (more likely to be tradeable)
        my_players = [p for p in my_roster.players if vor_values.get(p.id, 0) > 0]
        their_players = [p for p in their_roster.players if vor_values.get(p.id, 0) > 0]
        
        # Generate 1-for-1 trades
        for my_player in my_players:
            for their_player in their_players:
                trade = self._evaluate_trade(
                    [my_player], [their_player], 
                    my_roster, their_roster, vor_values, roster_slots
                )
                if trade:
                    trades.append(trade)
        
        if consider_2_for_1 and max_players_per_side >= 2:
            # Generate 2-for-1 trades (I give 2, get 1)
            for my_combo in combinations(my_players, 2):
                for their_player in their_players:
                    trade = self._evaluate_trade(
                        list(my_combo), [their_player],
                        my_roster, their_roster, vor_values, roster_slots
                    )
                    if trade:
                        trades.append(trade)
            
            # Generate 1-for-2 trades (I give 1, get 2)
            for my_player in my_players:
                for their_combo in combinations(their_players, 2):
                    trade = self._evaluate_trade(
                        [my_player], list(their_combo),
                        my_roster, their_roster, vor_values, roster_slots
                    )
                    if trade:
                        trades.append(trade)
        
        if max_players_per_side >= 2:
            # Generate 2-for-2 trades
            for my_combo in combinations(my_players, 2):
                for their_combo in combinations(their_players, 2):
                    trade = self._evaluate_trade(
                        list(my_combo), list(their_combo),
                        my_roster, their_roster, vor_values, roster_slots
                    )
                    if trade:
                        trades.append(trade)
        
        return trades
    
    def _evaluate_trade(self,
                       my_players: List[Player],
                       their_players: List[Player],
                       my_roster: Roster,
                       their_roster: Roster,
                       vor_values: Dict[str, float],
                       roster_slots: RosterSlots) -> Optional[TradeIdea]:
        """Evaluate a specific trade proposal"""
        
        # Calculate current lineup VOR for both teams
        my_current_vor = vor_calculator.calculate_lineup_vor(
            my_roster.players, vor_values, roster_slots
        )
        their_current_vor = vor_calculator.calculate_lineup_vor(
            their_roster.players, vor_values, roster_slots
        )
        
        # Create post-trade rosters
        my_post_trade = [p for p in my_roster.players if p.id not in [mp.id for mp in my_players]]
        my_post_trade.extend(their_players)
        
        their_post_trade = [p for p in their_roster.players if p.id not in [tp.id for tp in their_players]]
        their_post_trade.extend(my_players)
        
        # Calculate post-trade VOR
        my_new_vor = vor_calculator.calculate_lineup_vor(
            my_post_trade, vor_values, roster_slots
        )
        their_new_vor = vor_calculator.calculate_lineup_vor(
            their_post_trade, vor_values, roster_slots
        )
        
        # Calculate improvements
        my_improvement = my_new_vor - my_current_vor
        their_improvement = their_new_vor - their_current_vor
        
        # Only suggest if both teams improve by minimum threshold
        if (my_improvement >= self.min_improvement_threshold and 
            their_improvement >= self.min_improvement_threshold):
            
            # Create trade idea
            send_players = [
                TradePlayer(
                    player=p.name,
                    pos=p.position,
                    vor=vor_values.get(p.id, 0.0)
                ) for p in my_players
            ]
            
            receive_players = [
                TradePlayer(
                    player=p.name,
                    pos=p.position,
                    vor=vor_values.get(p.id, 0.0)
                ) for p in their_players
            ]
            
            # Generate trade notes
            notes = self._generate_trade_notes(
                my_players, their_players, my_improvement, their_improvement
            )
            
            return TradeIdea(
                send=send_players,
                receive=receive_players,
                score_me=round(my_improvement, 1),
                score_them=round(their_improvement, 1),
                notes=notes
            )
        
        return None
    
    def _generate_trade_notes(self,
                            my_players: List[Player],
                            their_players: List[Player],
                            my_improvement: float,
                            their_improvement: float) -> str:
        """Generate explanatory notes for a trade"""
        notes = []
        
        # Analyze position needs
        my_positions = [p.position for p in my_players]
        their_positions = [p.position for p in their_players]
        
        if len(set(my_positions)) == 1 and len(set(their_positions)) == 1:
            if my_positions[0] != their_positions[0]:
                notes.append(f"You get {their_positions[0]} help, they get {my_positions[0]} depth")
        
        # Analyze trade balance
        if abs(my_improvement - their_improvement) < 1.0:
            notes.append("Balanced trade benefits both teams equally")
        elif my_improvement > their_improvement:
            notes.append("Slight advantage to you")
        else:
            notes.append("Slight advantage to them")
        
        # Check for bye week considerations
        my_teams = set(p.team for p in my_players if p.team)
        their_teams = set(p.team for p in their_players if p.team)
        
        if my_teams.intersection(their_teams):
            notes.append("Watch for bye week conflicts")
        
        # Default note if none generated
        if not notes:
            notes.append(f"Mutual benefit: +{my_improvement:.1f} for you, +{their_improvement:.1f} for them")
        
        return "; ".join(notes)
    
    def validate_trade_roster_limits(self,
                                   roster: List[Player],
                                   roster_slots: RosterSlots) -> bool:
        """Validate that a roster meets league requirements"""
        position_counts = {}
        
        for player in roster:
            pos = player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Check minimum requirements
        required_positions = {
            "QB": roster_slots.QB,
            "RB": roster_slots.RB,
            "WR": roster_slots.WR,
            "TE": roster_slots.TE
        }
        
        for pos, required in required_positions.items():
            if position_counts.get(pos, 0) < required:
                return False
        
        return True
    
    def get_position_scarcity_bonus(self, 
                                  position: str,
                                  vor_values: Dict[str, float],
                                  all_players: List[Player]) -> float:
        """Calculate scarcity bonus for positions with fewer elite options"""
        position_players = [p for p in all_players if p.position == position]
        
        if not position_players:
            return 0.0
        
        # Get VOR values for this position
        position_vors = [vor_values.get(p.id, 0.0) for p in position_players]
        position_vors = [v for v in position_vors if v > 0]
        
        if len(position_vors) < 10:  # Scarce position
            return 0.5
        elif len(position_vors) < 20:
            return 0.2
        
        return 0.0

# Global trade analyzer instance
trade_analyzer = TradeAnalyzer()