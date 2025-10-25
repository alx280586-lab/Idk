"""Country simulator package."""
from .game import main as run_game
from .world import generate_world

__all__ = ["run_game", "generate_world"]
