"""
Recite service for displaying fantasy football application information.

This module provides functionality to "recite" or display various aspects
of the fantasy football trade finder application, including league configurations,
player data, VOR calculations, trade recommendations, and system status.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
try:
    from .models import (
        LeagueConfig, Player, Team, Roster, TradeIdea, FantasyProPlayer,
        RosterSlots, Scoring, ScoringBonus
    )
    from .cache import cache_manager
    from .vor import vor_calculator
    from .trade import trade_analyzer
    from .mapping import mapping_service
except ImportError:
    # Handle direct execution or testing
    from models import (
        LeagueConfig, Player, Team, Roster, TradeIdea, FantasyProPlayer,
        RosterSlots, Scoring, ScoringBonus
    )
    from cache import cache_manager
    from vor import vor_calculator
    from trade import trade_analyzer
    from mapping import mapping_service


class ReciteService:
    """Service for reciting/displaying fantasy football application information"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.app_name = "Fantasy Football Trade Finder"
    
    def recite_app_info(self) -> Dict[str, Any]:
        """Recite basic application information"""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "description": "A comprehensive fantasy football trade analysis and recommendation system",
            "features": [
                "Value Over Replacement (VOR) calculations",
                "Trade proposal generation and analysis",
                "Player mapping to FantasyPros data",
                "League configuration support",
                "Caching system for performance"
            ],
            "supported_platforms": ["ESPN", "Yahoo", "Sleeper", "Generic"],
            "timestamp": datetime.now().isoformat()
        }
    
    def recite_league_config(self, config: Optional[LeagueConfig] = None) -> Dict[str, Any]:
        """Recite league configuration details"""
        if config is None:
            # Create default configuration for demonstration
            config = LeagueConfig()
        
        config_dict = {
            "platform": config.platform or "Not specified",
            "league_id": config.league_id or "Not specified", 
            "scoring": {
                "format": config.scoring.format,
                "pass_td": config.scoring.pass_td,
                "bonuses": {
                    "100_yard_receiving": config.scoring.bonus.rec_100,
                    "100_yard_rushing": config.scoring.bonus.rush_100,
                    "200_yard_receiving": config.scoring.bonus.rec_200,
                    "300_yard_passing": config.scoring.bonus.pass_300
                }
            },
            "roster_slots": {
                "QB": config.roster_slots.QB,
                "RB": config.roster_slots.RB,
                "WR": config.roster_slots.WR,
                "TE": config.roster_slots.TE,
                "FLEX": config.roster_slots.FLEX,
                "SUPERFLEX": config.roster_slots.SUPERFLEX,
                "BENCH": config.roster_slots.BENCH
            },
            "te_premium": config.te_premium
        }
        
        return {
            "league_configuration": config_dict,
            "total_starting_positions": (
                config.roster_slots.QB + config.roster_slots.RB + 
                config.roster_slots.WR + config.roster_slots.TE + 
                config.roster_slots.FLEX + config.roster_slots.SUPERFLEX
            ),
            "total_roster_size": (
                config.roster_slots.QB + config.roster_slots.RB + 
                config.roster_slots.WR + config.roster_slots.TE + 
                config.roster_slots.FLEX + config.roster_slots.SUPERFLEX +
                config.roster_slots.BENCH
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    def recite_player_info(self, players: List[Player], limit: int = 20) -> Dict[str, Any]:
        """Recite player information and statistics"""
        if not players:
            return {
                "message": "No players provided",
                "total_players": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Group players by position
        position_groups = {}
        for player in players:
            pos = player.position
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(player)
        
        # Sort players by VOR if available, otherwise by name
        sorted_players = sorted(
            players[:limit], 
            key=lambda p: p.vor if p.vor is not None else 0, 
            reverse=True
        )
        
        player_list = []
        for player in sorted_players:
            player_info = {
                "name": player.name,
                "position": player.position,
                "team": player.team,
                "vor": player.vor,
                "ecr_rank": player.ecr_rank,
                "ros_points": player.ros_points,
                "injury_status": player.injury_status,
                "bye_week": player.bye_week
            }
            player_list.append(player_info)
        
        return {
            "total_players": len(players),
            "players_shown": len(sorted_players),
            "position_breakdown": {pos: len(players) for pos, players in position_groups.items()},
            "top_players": player_list,
            "timestamp": datetime.now().isoformat()
        }
    
    def recite_vor_analysis(self, players: List[FantasyProPlayer], 
                           roster_slots: Optional[RosterSlots] = None,
                           num_teams: int = 12) -> Dict[str, Any]:
        """Recite VOR (Value Over Replacement) analysis"""
        if not players:
            return {
                "message": "No FantasyPros players provided for VOR analysis",
                "timestamp": datetime.now().isoformat()
            }
        
        if roster_slots is None:
            roster_slots = RosterSlots()
        
        # Calculate replacement baselines
        baselines = vor_calculator.calculate_replacement_baselines(
            players, roster_slots, num_teams
        )
        
        # Calculate VOR for each player
        vor_players = []
        for player in players[:50]:  # Limit to top 50 for display
            baseline = baselines.get(player.position, 0)
            vor = player.ros_points - baseline
            vor_players.append({
                "name": player.player_name,
                "position": player.position,
                "team": player.team,
                "ecr_rank": player.ecr_rank,
                "ros_points": player.ros_points,
                "vor": round(vor, 2),
                "baseline": round(baseline, 2)
            })
        
        # Sort by VOR
        vor_players.sort(key=lambda p: p["vor"], reverse=True)
        
        return {
            "analysis_parameters": {
                "num_teams": num_teams,
                "roster_configuration": {
                    "QB": roster_slots.QB,
                    "RB": roster_slots.RB,
                    "WR": roster_slots.WR,
                    "TE": roster_slots.TE,
                    "FLEX": roster_slots.FLEX,
                    "SUPERFLEX": roster_slots.SUPERFLEX
                }
            },
            "replacement_baselines": {pos: round(baseline, 2) for pos, baseline in baselines.items()},
            "total_players_analyzed": len(players),
            "top_vor_players": vor_players,
            "timestamp": datetime.now().isoformat()
        }
    
    def recite_trade_summary(self, trade_ideas: List[TradeIdea], limit: int = 10) -> Dict[str, Any]:
        """Recite summary of trade recommendations"""
        if not trade_ideas:
            return {
                "message": "No trade ideas provided",
                "total_trades": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        trade_summaries = []
        for trade in trade_ideas[:limit]:
            trade_summary = {
                "send_players": [
                    {"name": tp.player, "position": tp.pos, "vor": tp.vor}
                    for tp in trade.send
                ],
                "receive_players": [
                    {"name": tp.player, "position": tp.pos, "vor": tp.vor}
                    for tp in trade.receive
                ],
                "my_improvement": round(trade.score_me, 2),
                "their_improvement": round(trade.score_them, 2),
                "combined_benefit": round(trade.score_me + trade.score_them, 2),
                "notes": trade.notes,
                "trade_type": f"{len(trade.send)}-for-{len(trade.receive)}"
            }
            trade_summaries.append(trade_summary)
        
        return {
            "total_trade_ideas": len(trade_ideas),
            "trades_shown": len(trade_summaries),
            "top_trades": trade_summaries,
            "average_my_improvement": round(
                sum(t.score_me for t in trade_ideas[:limit]) / min(len(trade_ideas), limit), 2
            ) if trade_ideas else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def recite_cache_status(self) -> Dict[str, Any]:
        """Recite cache system status and statistics"""
        try:
            # Get cache statistics
            fp_players = cache_manager.get_all_fantasypros_players()
            
            cache_info = {
                "fantasypros_players_cached": len(fp_players),
                "cache_last_updated": fp_players[0].last_updated.isoformat() if fp_players else "Never",
                "database_path": cache_manager.db_path,
                "status": "Active"
            }
            
            # Get position breakdown of cached players
            if fp_players:
                position_counts = {}
                for player in fp_players:
                    pos = player.position
                    position_counts[pos] = position_counts.get(pos, 0) + 1
                cache_info["position_breakdown"] = position_counts
            
            return {
                "cache_status": cache_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "cache_status": {
                    "status": "Error",
                    "error": str(e),
                    "fantasypros_players_cached": 0
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def recite_full_summary(self, 
                           config: Optional[LeagueConfig] = None,
                           players: Optional[List[Player]] = None,
                           fp_players: Optional[List[FantasyProPlayer]] = None,
                           trade_ideas: Optional[List[TradeIdea]] = None) -> Dict[str, Any]:
        """Recite comprehensive summary of the entire application state"""
        summary = {
            "app_info": self.recite_app_info(),
            "league_config": self.recite_league_config(config),
            "cache_status": self.recite_cache_status()
        }
        
        if players:
            summary["player_info"] = self.recite_player_info(players)
        
        if fp_players:
            roster_slots = config.roster_slots if config else None
            summary["vor_analysis"] = self.recite_vor_analysis(fp_players, roster_slots)
        
        if trade_ideas:
            summary["trade_summary"] = self.recite_trade_summary(trade_ideas)
        
        return summary


# Global recite service instance
recite_service = ReciteService()