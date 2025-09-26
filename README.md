# Fantasy Football Trade Finder

A comprehensive fantasy football trade analysis and recommendation system that helps fantasy managers find fair and beneficial trades using Value Over Replacement (VOR) calculations and FantasyPros data.

## Features

- **Value Over Replacement (VOR) calculations** - Calculate player values relative to replacement level
- **Trade proposal generation and analysis** - Generate and analyze fair trade proposals between teams
- **Player mapping to FantasyPros data** - Map league players to FantasyPros rankings and projections
- **League configuration support** - Support for different league formats and settings
- **Caching system for performance** - SQLite-based caching for API responses and player mappings
- **Recite functionality** - Display and summarize application information and analysis

## Supported Platforms

- ESPN
- Yahoo Fantasy
- Sleeper
- Generic CSV/JSON imports

## Recite Functionality

The application includes a comprehensive "recite" feature that allows you to display various information about your fantasy football setup and analysis.

### CLI Usage

```bash
# Show basic application information
python cli.py app

# Show league configuration
python cli.py config

# Show cache status
python cli.py cache

# Show comprehensive summary with sample data
python cli.py full --sample

# Use human-readable format instead of JSON
python cli.py app --format summary
```

### Available Recite Commands

- `app` - Display basic application information
- `config` - Show league configuration (scoring, roster slots, etc.)
- `players` - Display player information and statistics (requires data)
- `vor` - Show VOR analysis and replacement baselines (requires cached data)
- `trades` - Display trade recommendations (requires roster data)
- `cache` - Show cache system status and statistics
- `full` - Comprehensive summary of all available information

### Python API Usage

```python
from recite import recite_service
from models import LeagueConfig, Player

# Get basic app info
app_info = recite_service.recite_app_info()

# Show league configuration
config = LeagueConfig(platform="ESPN", league_id="12345")
config_info = recite_service.recite_league_config(config)

# Display player information
players = [...]  # Your player list
player_info = recite_service.recite_player_info(players)

# Get full summary
full_summary = recite_service.recite_full_summary(
    config=config,
    players=players
)
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install pydantic
   ```
3. Run the application or tests

## Testing

Run the comprehensive test suite:

```bash
python test_recite.py
```

## Core Components

- `models.py` - Pydantic models for data structures
- `vor.py` - Value Over Replacement calculator
- `trade.py` - Trade analysis and generation
- `mapping.py` - Player mapping to FantasyPros data
- `cache.py` - SQLite caching system
- `recite.py` - Information display and summary functionality
- `cli.py` - Command-line interface

## Example Output

### Application Information
```json
{
  "app_name": "Fantasy Football Trade Finder",
  "version": "1.0.0",
  "description": "A comprehensive fantasy football trade analysis and recommendation system",
  "features": [
    "Value Over Replacement (VOR) calculations",
    "Trade proposal generation and analysis",
    "Player mapping to FantasyPros data",
    "League configuration support",
    "Caching system for performance"
  ],
  "supported_platforms": ["ESPN", "Yahoo", "Sleeper", "Generic"]
}
```

### League Configuration Summary
```
League Configuration:
  Platform: ESPN  
  League Id: 12345
  Scoring:
    Format: PPR
    Pass Td: 4
  Roster Slots:
    QB: 1, RB: 2, WR: 2, TE: 1, FLEX: 1, BENCH: 6
  Total Starting Positions: 7
  Total Roster Size: 13
```

## Contributing

This is a fantasy football analysis tool designed to help managers make better trade decisions through data-driven analysis.