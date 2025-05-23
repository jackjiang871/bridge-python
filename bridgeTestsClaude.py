"""
Bridge Game Validation Test Suite

This module provides comprehensive testing for the Bridge game simulator
against parsed PBN (Portable Bridge Notation) files to ensure accuracy
of game logic, scoring, and contract resolution.

Usage:
    python test_bridge_games.py [--verbose] [--filter=PATTERN] [--fail-fast]

Environment Variables:
    BRIDGE_TEST_DATA_DIR: Directory containing parsed PBN files (default: 'parsed-games')
    BRIDGE_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
"""

import os
import json
import logging
import argparse
from typing import List, Dict, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from collections import defaultdict
import sys
from pathlib import Path

# Import the Bridge simulator
try:
    from bridgeClaudev2 import Bridge
except ImportError:
    print("Error: Could not import Bridge class from bridgeClean module")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEATS = ['N', 'E', 'S', 'W']
DENOMS = ['C', 'D', 'H', 'S', 'NT']
BIDS = [f"{level}{denom}" for level in range(1, 8) for denom in DENOMS]
VALID_AUCTION_ACTIONS = set(['Pass', 'X', 'XX'] + BIDS)
TARGET_TAGS = {'Vulnerable', 'Dealer', 'Deal', 'Declarer', 'Contract', 'Result', 'Score', 'Auction', 'Play'}

@dataclass
class GameResult:
    """Represents the outcome of a single game validation."""
    file_name: str
    game_index: int
    expected_declarer: str
    actual_declarer: str
    expected_contract: str
    actual_contract: str
    expected_result: Optional[int]
    actual_result: Optional[int]
    expected_score: Optional[str]
    actual_score: Optional[str]
    errors: List[str]
    
    @property
    def is_valid(self) -> bool:
        """Returns True if all validations passed."""
        return len(self.errors) == 0
    
    @property
    def has_play_data(self) -> bool:
        """Returns True if this game included play data."""
        return self.expected_result is not None

class ValidationStats:
    """Tracks validation statistics across all games."""
    
    def __init__(self):
        self.total_games = 0
        self.games_with_play = 0
        self.declarer_matches = 0
        self.contract_matches = 0
        self.result_matches = 0
        self.score_matches = 0
        self.error_counts = defaultdict(int)
        self.failed_games = []
    
    def add_result(self, result: GameResult):
        """Add a game result to the statistics."""
        self.total_games += 1
        
        if result.has_play_data:
            self.games_with_play += 1
            
        if result.expected_declarer == result.actual_declarer:
            self.declarer_matches += 1
        else:
            self.error_counts['declarer_mismatch'] += 1
            
        if result.expected_contract == result.actual_contract:
            self.contract_matches += 1
        else:
            self.error_counts['contract_mismatch'] += 1
            
        if result.has_play_data:
            if result.expected_result == result.actual_result:
                self.result_matches += 1
            else:
                self.error_counts['result_mismatch'] += 1
                
            if result.expected_score == result.actual_score:
                self.score_matches += 1
            else:
                self.error_counts['score_mismatch'] += 1
        
        if not result.is_valid:
            self.failed_games.append(result)
    
    def print_summary(self):
        """Print a comprehensive summary of validation results."""
        print("\n" + "="*60)
        print("BRIDGE GAME VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Total games processed: {self.total_games}")
        print(f"Games with play data: {self.games_with_play}")
        print()
        
        # Auction validation
        declarer_pct = (self.declarer_matches / self.total_games) * 100 if self.total_games > 0 else 0
        contract_pct = (self.contract_matches / self.total_games) * 100 if self.total_games > 0 else 0
        
        print("AUCTION VALIDATION:")
        print(f"  Declarer matches: {self.declarer_matches}/{self.total_games} ({declarer_pct:.1f}%)")
        print(f"  Contract matches: {self.contract_matches}/{self.total_games} ({contract_pct:.1f}%)")
        
        # Play validation
        if self.games_with_play > 0:
            result_pct = (self.result_matches / self.games_with_play) * 100
            score_pct = (self.score_matches / self.games_with_play) * 100
            
            print("\nPLAY VALIDATION:")
            print(f"  Result matches: {self.result_matches}/{self.games_with_play} ({result_pct:.1f}%)")
            print(f"  Score matches: {self.score_matches}/{self.games_with_play} ({score_pct:.1f}%)")
        
        # Error summary
        if self.error_counts:
            print("\nERROR BREAKDOWN:")
            for error_type, count in sorted(self.error_counts.items()):
                print(f"  {error_type}: {count}")
        
        # Overall success rate
        total_validations = self.total_games * 2  # declarer + contract
        if self.games_with_play > 0:
            total_validations += self.games_with_play * 2  # result + score
            
        successful_validations = self.declarer_matches + self.contract_matches + self.result_matches + self.score_matches
        success_rate = (successful_validations / total_validations) * 100 if total_validations > 0 else 0
        
        print(f"\nOVERALL SUCCESS RATE: {success_rate:.1f}%")
        
        if self.failed_games:
            print(f"\nFAILED GAMES: {len(self.failed_games)}")

class BridgeGameValidator:
    """Main class for validating Bridge games against PBN data."""
    
    def __init__(self, data_dir: str = 'parsed-games', verbose: bool = False):
        self.data_dir = Path(data_dir)
        self.verbose = verbose
        self.stats = ValidationStats()
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    def load_games_from_file(self, filepath: Path) -> List[Dict]:
        """Load and parse games from a single JSONL file."""
        games = []
        current_game = None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in {filepath}:{line_num}: {e}")
                        continue
                    
                    if obj.get('type') == 'game':
                        if current_game:
                            games.append(current_game)
                        current_game = {}
                    elif obj.get('type') == 'tag' and current_game is not None:
                        name = obj.get('name')
                        if name in TARGET_TAGS:
                            current_game[name] = obj
                
                if current_game:
                    games.append(current_game)
                    
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return []
        
        return games
    
    def create_auction_actions(self, game: Dict) -> List[Dict]:
        """Convert PBN auction tokens to Bridge simulator actions."""
        if 'Auction' not in game:
            return []
        
        actions = []
        auction_tokens = game['Auction']['tokens']
        seat_index = SEATS.index(game['Auction']['value'])
        
        for token in auction_tokens:
            if token in VALID_AUCTION_ACTIONS:
                actions.append({
                    'name': 'Auction',
                    'player': SEATS[seat_index],
                    'value': token
                })
                seat_index = (seat_index + 1) % len(SEATS)
        
        return actions
    
    def simulate_play(self, bridge: Bridge, game: Dict) -> bool:
        """Simulate the play phase of a bridge game."""
        if 'Play' not in game:
            return False
        
        play_tokens = game['Play']['tokens']
        seat_index = SEATS.index(game['Play']['value'])
        current_trick = []
        tricks_played = 0
        
        for token in play_tokens:
            if token == '*':  # End of play marker
                break
                
            play_action = {
                'name': 'Play',
                'player': SEATS[seat_index],
                'value': token
            }
            current_trick.append(play_action)
            seat_index = (seat_index + 1) % len(SEATS)
            
            if len(current_trick) == 4:
                # Play cards in correct turn order
                for _ in range(4):
                    next_player = bridge.tricks[-1].next_player()
                    for i, action in enumerate(current_trick):
                        if action['player'] == next_player:
                            bridge.simulate(current_trick.pop(i))
                            break
                
                tricks_played += 1
                current_trick = []
        
        return tricks_played == 13
    
    def validate_game(self, file_name: str, game_index: int, game: Dict) -> GameResult:
        """Validate a single bridge game."""
        errors = []
        
        # Required tags check
        required_tags = ['Vulnerable', 'Dealer', 'Deal', 'Auction']
        for tag in required_tags:
            if tag not in game:
                errors.append(f"Missing required tag: {tag}")
                
        if errors:
            return GameResult(
                file_name=file_name,
                game_index=game_index,
                expected_declarer="",
                actual_declarer="",
                expected_contract="",
                actual_contract="",
                expected_result=None,
                actual_result=None,
                expected_score=None,
                actual_score=None,
                errors=errors
            )
        
        # Create bridge simulation
        try:
            auction_actions = self.create_auction_actions(game)
            actions = [game['Vulnerable'], game['Dealer'], game['Deal']] + auction_actions
            bridge = Bridge(actions)
        except Exception as e:
            errors.append(f"Bridge simulation failed: {e}")
            return GameResult(
                file_name=file_name,
                game_index=game_index,
                expected_declarer="",
                actual_declarer="",
                expected_contract="",
                actual_contract="",
                expected_result=None,
                actual_result=None,
                expected_score=None,
                actual_score=None,
                errors=errors
            )
        
        # Validate auction results
        expected_declarer = game.get('Declarer', {}).get('value', '')
        actual_declarer = bridge.declarers[0] if bridge.declarers else ''
        if actual_declarer == None:
            actual_declarer = ''
        
        expected_contract = game.get('Contract', {}).get('value', '')
        contract_obj = bridge.contracts[0] if bridge.contracts else {}
        if contract_obj.get('denomination', '') == 'Pass':
            actual_contract = 'Pass'
        else:
            actual_contract = f"{contract_obj.get('level', '')}{contract_obj.get('denomination', '')}{contract_obj.get('risk', '')}"
        
        if expected_declarer != actual_declarer:
            errors.append(f"Declarer mismatch: expected {expected_declarer}, got {actual_declarer}")
        
        if expected_contract != actual_contract:
            errors.append(f"Contract mismatch: expected {expected_contract}, got {actual_contract}")
        
        # Validate play results if available
        expected_result = None
        actual_result = None
        expected_score = None
        actual_score = None
        
        if 'Play' in game:
            try:
                play_completed = self.simulate_play(bridge, game)
                if play_completed:
                    expected_result = int(game.get('Result', {}).get('value', 0))
                    actual_result = bridge.results[0] if bridge.results else 0
                    
                    expected_score = game.get('Score', {}).get('value', '')
                    actual_score = bridge.scores[0] if bridge.scores else ''
                    
                    if expected_result != actual_result:
                        errors.append(f"Result mismatch: expected {expected_result}, got {actual_result}")
                    
                    if expected_score != actual_score:
                        errors.append(f"Score mismatch: expected {expected_score}, got {actual_score}")
                else:
                    errors.append("Play simulation incomplete")
            except Exception as e:
                errors.append(f"Play simulation error: {e}")
        
        return GameResult(
            file_name=file_name,
            game_index=game_index,
            expected_declarer=expected_declarer,
            actual_declarer=actual_declarer,
            expected_contract=expected_contract,
            actual_contract=actual_contract,
            expected_result=expected_result,
            actual_result=actual_result,
            expected_score=expected_score,
            actual_score=actual_score,
            errors=errors
        )
    
    def run_validation(self, file_filter: Optional[str] = None, fail_fast: bool = False) -> ValidationStats:
        """Run validation on all PBN files in the data directory."""
        files = list(self.data_dir.glob('*.jsonl'))
        
        if file_filter:
            files = [f for f in files if file_filter in f.name]
        
        if not files:
            logger.warning(f"No JSONL files found in {self.data_dir}")
            return self.stats
        
        logger.info(f"Processing {len(files)} files...")
        
        for file_path in files:
            logger.info(f"Processing file: {file_path.name}")
            games = self.load_games_from_file(file_path)
            
            for game_index, game in enumerate(games):
                result = self.validate_game(file_path.name, game_index, game)
                self.stats.add_result(result)
                
                if self.verbose and not result.is_valid:
                    print(f"\nFAILED: {file_path.name} game {game_index}")
                    for error in result.errors:
                        print(f"  - {error}")
                
                if fail_fast and not result.is_valid:
                    logger.error(f"Stopping due to failure in {file_path.name} game {game_index}")
                    return self.stats
        
        return self.stats

def main():
    """Main entry point for the test suite."""
    parser = argparse.ArgumentParser(description='Validate Bridge game simulations against PBN data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--filter', help='Filter files by name pattern')
    parser.add_argument('--fail-fast', action='store_true', help='Stop on first failure')
    parser.add_argument('--data-dir', default='parsed-games', help='Directory containing PBN files')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        validator = BridgeGameValidator(data_dir=args.data_dir, verbose=args.verbose)
        stats = validator.run_validation(file_filter=args.filter, fail_fast=args.fail_fast)
        stats.print_summary()
        
        # Exit with error code if there were failures
        if stats.failed_games:
            sys.exit(1)
        else:
            print("\n✅ All validations passed!")
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()