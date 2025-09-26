#!/usr/bin/env python3
"""
Test suite for the recite functionality.

This module contains comprehensive tests for all recite service methods
and CLI functionality.
"""

import unittest
import json
from datetime import datetime
from typing import List

# Import modules to test
try:
    from recite import recite_service, ReciteService
    from models import (
        LeagueConfig, Player, FantasyProPlayer, TradeIdea, TradePlayer,
        RosterSlots, Scoring, ScoringBonus
    )
    from cli import format_output, format_summary, create_sample_data
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all modules are properly set up")
    exit(1)


class TestReciteService(unittest.TestCase):
    """Test cases for ReciteService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = ReciteService()
        
        # Sample data
        self.sample_config = LeagueConfig(
            platform="ESPN",
            league_id="12345",
            te_premium=True
        )
        
        self.sample_players = [
            Player(
                id="1", name="Josh Allen", position="QB", team="BUF",
                vor=15.2, ecr_rank=1, ros_points=285.5, bye_week=7
            ),
            Player(
                id="2", name="Christian McCaffrey", position="RB", team="SF",
                vor=12.8, ecr_rank=2, ros_points=245.3, injury_status="Healthy"
            ),
            Player(
                id="3", name="Cooper Kupp", position="WR", team="LAR",
                vor=10.5, ecr_rank=8, ros_points=210.7
            )
        ]
        
        self.sample_fp_players = [
            FantasyProPlayer(
                player_name="Josh Allen", position="QB", team="BUF",
                ecr_rank=1, ros_points=285.5, last_updated=datetime.now()
            ),
            FantasyProPlayer(
                player_name="Lamar Jackson", position="QB", team="BAL", 
                ecr_rank=3, ros_points=275.2, last_updated=datetime.now()
            )
        ]
        
        self.sample_trade_ideas = [
            TradeIdea(
                send=[TradePlayer(player="Josh Allen", pos="QB", vor=15.2)],
                receive=[TradePlayer(player="Lamar Jackson", pos="QB", vor=14.1)],
                score_me=2.5, score_them=1.8,
                notes="Slight upgrade at QB position"
            )
        ]
    
    def test_recite_app_info(self):
        """Test basic app information recital"""
        result = self.service.recite_app_info()
        
        self.assertIn("app_name", result)
        self.assertIn("version", result)
        self.assertIn("description", result)
        self.assertIn("features", result)
        self.assertIn("supported_platforms", result)
        self.assertIn("timestamp", result)
        
        self.assertEqual(result["app_name"], "Fantasy Football Trade Finder")
        self.assertEqual(result["version"], "1.0.0")
        self.assertIsInstance(result["features"], list)
        self.assertTrue(len(result["features"]) > 0)
    
    def test_recite_league_config_default(self):
        """Test league configuration recital with default config"""
        result = self.service.recite_league_config()
        
        self.assertIn("league_configuration", result)
        self.assertIn("total_starting_positions", result)
        self.assertIn("total_roster_size", result)
        
        config = result["league_configuration"]
        self.assertEqual(config["platform"], "Not specified")
        self.assertEqual(config["scoring"]["format"], "PPR")
        self.assertEqual(config["roster_slots"]["QB"], 1)
    
    def test_recite_league_config_custom(self):
        """Test league configuration recital with custom config"""
        result = self.service.recite_league_config(self.sample_config)
        
        config = result["league_configuration"]
        self.assertEqual(config["platform"], "ESPN")
        self.assertEqual(config["league_id"], "12345")
        self.assertEqual(config["te_premium"], True)
    
    def test_recite_player_info_empty(self):
        """Test player information recital with empty list"""
        result = self.service.recite_player_info([])
        
        self.assertIn("message", result)
        self.assertEqual(result["total_players"], 0)
    
    def test_recite_player_info_with_players(self):
        """Test player information recital with sample players"""
        result = self.service.recite_player_info(self.sample_players)
        
        self.assertIn("total_players", result)
        self.assertIn("players_shown", result)
        self.assertIn("position_breakdown", result)
        self.assertIn("top_players", result)
        
        self.assertEqual(result["total_players"], 3)
        self.assertEqual(result["players_shown"], 3)
        
        # Check position breakdown
        breakdown = result["position_breakdown"]
        self.assertEqual(breakdown["QB"], 1)
        self.assertEqual(breakdown["RB"], 1) 
        self.assertEqual(breakdown["WR"], 1)
        
        # Check player details
        top_players = result["top_players"]
        self.assertEqual(len(top_players), 3)
        self.assertEqual(top_players[0]["name"], "Josh Allen")  # Highest VOR
    
    def test_recite_vor_analysis_empty(self):
        """Test VOR analysis with empty player list"""
        result = self.service.recite_vor_analysis([])
        
        self.assertIn("message", result)
    
    def test_recite_vor_analysis_with_players(self):
        """Test VOR analysis with sample players"""
        result = self.service.recite_vor_analysis(self.sample_fp_players)
        
        self.assertIn("analysis_parameters", result)
        self.assertIn("replacement_baselines", result)
        self.assertIn("total_players_analyzed", result) 
        self.assertIn("top_vor_players", result)
        
        self.assertEqual(result["total_players_analyzed"], 2)
        
        # Check analysis parameters
        params = result["analysis_parameters"]
        self.assertEqual(params["num_teams"], 12)
        self.assertIn("roster_configuration", params)
    
    def test_recite_trade_summary_empty(self):
        """Test trade summary with empty list"""
        result = self.service.recite_trade_summary([])
        
        self.assertIn("message", result)
        self.assertEqual(result["total_trades"], 0)
    
    def test_recite_trade_summary_with_trades(self):
        """Test trade summary with sample trades"""
        result = self.service.recite_trade_summary(self.sample_trade_ideas)
        
        self.assertIn("total_trade_ideas", result)
        self.assertIn("trades_shown", result)
        self.assertIn("top_trades", result)
        self.assertIn("average_my_improvement", result)
        
        self.assertEqual(result["total_trade_ideas"], 1)
        self.assertEqual(result["trades_shown"], 1)
        
        trade = result["top_trades"][0]
        self.assertIn("send_players", trade)
        self.assertIn("receive_players", trade)
        self.assertIn("my_improvement", trade)
        self.assertIn("their_improvement", trade)
        self.assertIn("trade_type", trade)
        self.assertEqual(trade["trade_type"], "1-for-1")
    
    def test_recite_cache_status(self):
        """Test cache status recital"""
        result = self.service.recite_cache_status()
        
        self.assertIn("cache_status", result)
        
        cache_status = result["cache_status"]
        self.assertIn("status", cache_status)
        self.assertIn("fantasypros_players_cached", cache_status)
        self.assertIn("database_path", cache_status)
    
    def test_recite_full_summary(self):
        """Test comprehensive full summary"""
        result = self.service.recite_full_summary(
            config=self.sample_config,
            players=self.sample_players,
            fp_players=self.sample_fp_players,
            trade_ideas=self.sample_trade_ideas
        )
        
        # Should contain all sections
        self.assertIn("app_info", result)
        self.assertIn("league_config", result)
        self.assertIn("cache_status", result)
        self.assertIn("player_info", result)
        self.assertIn("vor_analysis", result)
        self.assertIn("trade_summary", result)


class TestCLIFunctions(unittest.TestCase):
    """Test cases for CLI utility functions"""
    
    def test_format_output_json(self):
        """Test JSON formatting"""
        data = {"key": "value", "number": 42}
        result = format_output(data, "json")
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed["key"], "value")
        self.assertEqual(parsed["number"], 42)
    
    def test_format_output_summary(self):
        """Test summary formatting"""
        data = {"app_name": "Test App", "version": "1.0"}
        result = format_output(data, "summary")
        
        self.assertIn("Test App", result)
        self.assertIn("1.0", result)
    
    def test_create_sample_data(self):
        """Test sample data creation"""
        players = create_sample_data()
        
        self.assertIsInstance(players, list)
        self.assertTrue(len(players) > 0)
        
        # Check first player
        player = players[0]
        self.assertEqual(player.name, "Josh Allen")
        self.assertEqual(player.position, "QB")
        self.assertIsNotNone(player.vor)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""
    
    def test_full_workflow(self):
        """Test complete workflow from config to trade analysis"""
        service = ReciteService()
        
        # Create test data
        config = LeagueConfig(platform="Test", league_id="999")
        players = create_sample_data()
        
        # Test each component
        app_info = service.recite_app_info()
        self.assertIn("app_name", app_info)
        
        config_info = service.recite_league_config(config)
        self.assertEqual(config_info["league_configuration"]["platform"], "Test")
        
        player_info = service.recite_player_info(players)
        self.assertEqual(player_info["total_players"], len(players))
        
        # Test full summary
        full_summary = service.recite_full_summary(config=config, players=players)
        self.assertIn("app_info", full_summary)
        self.assertIn("league_config", full_summary)
        self.assertIn("player_info", full_summary)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        service = ReciteService()
        
        # Test with None values
        result = service.recite_player_info(None)
        self.assertEqual(result["total_players"], 0)
        
        # Test with invalid data types
        result = service.recite_player_info([])
        self.assertIn("message", result)


def run_tests():
    """Run all tests and provide summary"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestReciteService))
    suite.addTest(unittest.makeSuite(TestCLIFunctions))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)