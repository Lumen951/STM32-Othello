"""
Challenge Mode Manager for Othello PC

Manages challenge mode state and statistics:
- Cumulative score tracking
- Consecutive loss detection
- Win/Game Over conditions
- Challenge session management
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json
import os


@dataclass
class ChallengeStats:
    """Challenge mode statistics"""
    total_score: int = 0
    consecutive_losses: int = 0
    games_played: int = 0
    games_won: int = 0
    games_lost: int = 0
    games_drawn: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'total_score': self.total_score,
            'consecutive_losses': self.consecutive_losses,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'games_lost': self.games_lost,
            'games_drawn': self.games_drawn,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ChallengeStats':
        """Create from dictionary"""
        stats = cls()
        stats.total_score = data.get('total_score', 0)
        stats.consecutive_losses = data.get('consecutive_losses', 0)
        stats.games_played = data.get('games_played', 0)
        stats.games_won = data.get('games_won', 0)
        stats.games_lost = data.get('games_lost', 0)
        stats.games_drawn = data.get('games_drawn', 0)

        start_time_str = data.get('start_time')
        if start_time_str:
            stats.start_time = datetime.fromisoformat(start_time_str)

        end_time_str = data.get('end_time')
        if end_time_str:
            stats.end_time = datetime.fromisoformat(end_time_str)

        return stats


class ChallengeMode:
    """Challenge mode manager"""

    # Constants
    WIN_SCORE = 50  # Total score needed to win
    MAX_LOSSES = 2   # Maximum consecutive losses

    def __init__(self, data_dir: str = "OthelloPC/data"):
        """Initialize challenge mode manager"""
        self.data_dir = data_dir
        self.stats_file = os.path.join(data_dir, "challenge_stats.json")

        self.is_active = False
        self.current_stats = ChallengeStats()
        self.history = []  # List of past challenge sessions

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Load history
        self._load_history()

    def start_challenge(self):
        """Start new challenge session"""
        self.is_active = True
        self.current_stats = ChallengeStats()
        self.current_stats.start_time = datetime.now()

    def end_challenge(self):
        """End current challenge session"""
        if not self.is_active:
            return

        self.is_active = False
        self.current_stats.end_time = datetime.now()

        # Save to history
        self.history.append(self.current_stats.to_dict())
        self._save_history()

    def process_game_result(self, player_score: int, opponent_score: int) -> str:
        """
        Process game result and update challenge state

        Args:
            player_score: Player's score (black pieces)
            opponent_score: Opponent's score (white pieces)

        Returns:
            Result status: 'ongoing', 'win', or 'game_over'
        """
        if not self.is_active:
            return 'ongoing'

        self.current_stats.games_played += 1

        # Determine game result
        if player_score > opponent_score:
            # Player won
            self.current_stats.games_won += 1
            self.current_stats.consecutive_losses = 0
            self.current_stats.total_score += player_score
        elif player_score < opponent_score:
            # Player lost
            self.current_stats.games_lost += 1
            self.current_stats.consecutive_losses += 1
            # No score added for losses
        else:
            # Draw
            self.current_stats.games_drawn += 1
            self.current_stats.consecutive_losses = 0
            self.current_stats.total_score += player_score

        # Check win condition
        if self.current_stats.total_score >= self.WIN_SCORE:
            return 'win'

        # Check game over condition
        if self.current_stats.consecutive_losses >= self.MAX_LOSSES:
            return 'game_over'

        return 'ongoing'

    def update_from_protocol(self, games_won: int, games_lost: int,
                            total_score: int, game_result: int):
        """
        Update challenge stats from protocol data

        Args:
            games_won: Number of games won
            games_lost: Number of games lost
            total_score: Total cumulative score
            game_result: Game result (0=ongoing, 1=win, 2=game_over)
        """
        if not self.is_active:
            return

        self.current_stats.games_won = games_won
        self.current_stats.games_lost = games_lost
        self.current_stats.total_score = total_score
        self.current_stats.games_played = games_won + games_lost + self.current_stats.games_drawn

        # Update state based on game result
        if game_result == 1:  # Win
            self.end_challenge()
        elif game_result == 2:  # Game over
            self.end_challenge()

    def get_stats(self) -> ChallengeStats:
        """Get current challenge statistics"""
        return self.current_stats

    def is_win_condition_met(self) -> bool:
        """Check if win condition is met"""
        return self.current_stats.total_score >= self.WIN_SCORE

    def is_game_over_condition_met(self) -> bool:
        """Check if game over condition is met"""
        return self.current_stats.consecutive_losses >= self.MAX_LOSSES

    def get_progress_percentage(self) -> float:
        """Get progress towards win condition (0-100%)"""
        return min(100.0, (self.current_stats.total_score / self.WIN_SCORE) * 100)

    def get_duration(self) -> Optional[float]:
        """Get challenge duration in seconds"""
        if not self.current_stats.start_time:
            return None

        end_time = self.current_stats.end_time or datetime.now()
        duration = (end_time - self.current_stats.start_time).total_seconds()
        return duration

    def get_history(self) -> list:
        """Get challenge history"""
        return self.history.copy()

    def clear_history(self):
        """Clear challenge history"""
        self.history.clear()
        self._save_history()

    def _load_history(self):
        """Load challenge history from file"""
        if not os.path.exists(self.stats_file):
            return

        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = data.get('history', [])
        except Exception as e:
            print(f"Error loading challenge history: {e}")
            self.history = []

    def _save_history(self):
        """Save challenge history to file"""
        try:
            data = {
                'history': self.history,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving challenge history: {e}")
