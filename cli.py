#!/usr/bin/env python3
"""
Command-line interface for the Fantasy Football Trade Finder recite functionality.

This script provides a CLI to "recite" various information from the trade finder app.
"""

import argparse
import json
import sys
from typing import Optional, List
from datetime import datetime

try:
    from .recite import recite_service
    from .models import LeagueConfig, Player, FantasyProPlayer
    from .cache import cache_manager
except ImportError:
    # Handle direct execution
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from recite import recite_service
    from models import LeagueConfig, Player, FantasyProPlayer  
    from cache import cache_manager


def format_output(data: dict, format_type: str = "json") -> str:
    """Format output data for display"""
    if format_type.lower() == "json":
        return json.dumps(data, indent=2, default=str)
    elif format_type.lower() == "summary":
        return format_summary(data)
    else:
        return str(data)


def format_summary(data: dict) -> str:
    """Format data as a human-readable summary"""
    lines = []
    
    def add_section(title: str, content: dict, indent: int = 0):
        prefix = "  " * indent
        lines.append(f"{prefix}{title}:")
        
        for key, value in content.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}  {key.replace('_', ' ').title()}:")
                add_section("", value, indent + 2)
            elif isinstance(value, list):
                lines.append(f"{prefix}  {key.replace('_', ' ').title()}: {len(value)} items")
                if key in ["top_players", "top_vor_players", "top_trades"] and value:
                    for i, item in enumerate(value[:3]):  # Show top 3
                        if isinstance(item, dict):
                            if "name" in item:
                                lines.append(f"{prefix}    {i+1}. {item.get('name', 'Unknown')}")
                        else:
                            lines.append(f"{prefix}    {i+1}. {item}")
            else:
                lines.append(f"{prefix}  {key.replace('_', ' ').title()}: {value}")
    
    if "app_info" in data:
        add_section("Application Information", data["app_info"])
        lines.append("")
    
    if "league_config" in data:
        add_section("League Configuration", data["league_config"])
        lines.append("")
    
    if "player_info" in data:
        add_section("Player Information", data["player_info"])
        lines.append("")
    
    if "vor_analysis" in data:
        add_section("VOR Analysis", data["vor_analysis"])
        lines.append("")
    
    if "trade_summary" in data:
        add_section("Trade Summary", data["trade_summary"])
        lines.append("")
        
    if "cache_status" in data:
        add_section("Cache Status", data["cache_status"])
        lines.append("")
    
    # Handle single-level data
    if not any(key in data for key in ["app_info", "league_config", "player_info", "vor_analysis", "trade_summary", "cache_status"]):
        add_section("Information", data)
    
    return "\n".join(lines)


def create_sample_data():
    """Create sample data for demonstration"""
    # Sample players
    sample_players = [
        Player(
            id="1", name="Josh Allen", position="QB", team="BUF",
            vor=15.2, ecr_rank=1, ros_points=285.5
        ),
        Player(
            id="2", name="Christian McCaffrey", position="RB", team="SF", 
            vor=12.8, ecr_rank=2, ros_points=245.3
        ),
        Player(
            id="3", name="Cooper Kupp", position="WR", team="LAR",
            vor=10.5, ecr_rank=8, ros_points=210.7
        )
    ]
    
    return sample_players


def main():
    parser = argparse.ArgumentParser(
        description="Recite information from Fantasy Football Trade Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s app                    # Show basic app information
  %(prog)s config                 # Show league configuration 
  %(prog)s cache                  # Show cache status
  %(prog)s full                   # Show comprehensive summary
  %(prog)s --format summary app   # Show app info in readable format
        """
    )
    
    parser.add_argument(
        "command",
        choices=["app", "config", "players", "vor", "trades", "cache", "full"],
        help="What information to recite"
    )
    
    parser.add_argument(
        "--format", 
        choices=["json", "summary"],
        default="json",
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of items to show (default: 20)"
    )
    
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use sample data for demonstration"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "app":
            data = recite_service.recite_app_info()
            
        elif args.command == "config":
            config = LeagueConfig()  # Use default config
            data = recite_service.recite_league_config(config)
            
        elif args.command == "players":
            if args.sample:
                players = create_sample_data()
                data = recite_service.recite_player_info(players, args.limit)
            else:
                print("Error: No player data source specified. Use --sample for demonstration.")
                return 1
                
        elif args.command == "vor":
            try:
                fp_players = cache_manager.get_all_fantasypros_players()
                if not fp_players and args.sample:
                    print("No cached FantasyPros data found. Use --sample not implemented for VOR.")
                    return 1
                data = recite_service.recite_vor_analysis(fp_players)
            except Exception as e:
                print(f"Error accessing cached data: {e}")
                return 1
                
        elif args.command == "trades":
            print("Error: Trade analysis requires roster data. Use 'full' command with sample data.")
            return 1
            
        elif args.command == "cache":
            data = recite_service.recite_cache_status()
            
        elif args.command == "full":
            config = LeagueConfig() if args.sample else None
            players = create_sample_data() if args.sample else None
            fp_players = None
            try:
                fp_players = cache_manager.get_all_fantasypros_players()
            except:
                pass
                
            data = recite_service.recite_full_summary(
                config=config,
                players=players, 
                fp_players=fp_players
            )
        
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
        # Output the data
        output = format_output(data, args.format)
        print(output)
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())