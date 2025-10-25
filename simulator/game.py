"""Entry point for running the country simulator."""
from __future__ import annotations

import argparse
import random

from .world import generate_world
from .ui import GameUI
from .save_load import load_game


def new_game(seed: int | None, countries: int) -> None:
    if seed is None:
        seed = random.randint(0, 9_999_999)
        print(f"Generated seed: {seed}")
    world = generate_world(seed, num_countries=countries)
    player_country = choose_player_country(world)
    ui = GameUI(world, player_country)
    ui.main_loop()


def choose_player_country(world) -> str:
    print("Available countries:")
    for name, country in world.countries.items():
        print(f" - {name}: GDP {country.economy.gdp/1_000_000_000:.1f}B, Government {country.politics.government_type}")
    while True:
        choice = input("Select your country: ")
        if choice in world.countries:
            return choice
        print("Invalid country. Try again.")


def load_saved_game(filename: str) -> None:
    world, player_country = load_game(filename)
    print(f"Loaded {filename}. Resuming as {player_country} in year {world.year}.")
    ui = GameUI(world, player_country)
    ui.main_loop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Replayable country simulator.")
    parser.add_argument("--seed", type=int, help="Seed for world generation", default=None)
    parser.add_argument("--countries", type=int, help="Number of AI countries", default=6)
    parser.add_argument("--load", type=str, help="Load game from file", default=None)
    args = parser.parse_args()

    if args.load:
        load_saved_game(args.load)
    else:
        new_game(args.seed, args.countries)


if __name__ == "__main__":
    main()
