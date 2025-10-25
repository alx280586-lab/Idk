"""World generation and global simulation utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import random

from .economy import Economy, RESOURCE_TYPES
from .politics import PoliticalSystem
from .military import Military
from .diplomacy import Diplomacy
from .society import Society


TERRAINS = ["plains", "forest", "mountain", "desert", "tundra", "coast"]
CLIMATES = ["temperate", "arid", "tropical", "polar", "continental"]


@dataclass
class Tile:
    x: int
    y: int
    terrain: str
    climate: str
    resource: str
    owner: str | None


@dataclass
class Country:
    name: str
    economy: Economy
    politics: PoliticalSystem
    military: Military
    diplomacy: Diplomacy
    society: Society
    automation: Dict[str, bool] = field(
        default_factory=lambda: {
            "economy": False,
            "military": False,
            "diplomacy": False,
        }
    )
    history: List[str] = field(default_factory=list)

    def record_event(self, event: str) -> None:
        self.history.append(event)
        if len(self.history) > 50:
            self.history.pop(0)

    def summary(self) -> Dict[str, Dict[str, float]]:
        return {
            "Economy": self.economy.summary(),
            "Politics": self.politics.summary(),
            "Society": self.society.summary(),
            "Military": {
                "Total Power": round(self.military.total_power(), 2),
                "Doctrine": self.military.doctrine,
            },
            "Diplomacy": self.diplomacy.summary(),
        }


@dataclass
class WorldMap:
    width: int
    height: int
    tiles: List[List[Tile]]

    def render(self, focus_country: str | None = None) -> str:
        rows: List[str] = []
        for y in range(self.height):
            row_chars: List[str] = []
            for x in range(self.width):
                tile = self.tiles[y][x]
                if tile.owner is None:
                    char = "~" if tile.terrain == "coast" else "."
                else:
                    char = tile.owner[0].upper()
                    if focus_country and tile.owner == focus_country:
                        char = char.lower()
                row_chars.append(char)
            rows.append("".join(row_chars))
        return "\n".join(rows)


@dataclass
class World:
    map: WorldMap
    countries: Dict[str, Country]
    year: int
    tension: float
    rng: random.Random
    seed: int

    def update(self, player_country: str) -> Dict[str, List[str]]:
        """Advance the world by one year."""
        self.year += 1
        events: Dict[str, List[str]] = {name: [] for name in self.countries}

        for name, country in self.countries.items():
            econ_growth_mod = 0.01 if country.politics.stability > 0.5 else -0.01
            econ_growth_mod += (0.5 - country.society.unrest) * 0.02
            country.economy.update(econ_growth_mod, self.rng)

            policy_effects = {
                "welfare": country.economy.budget_allocation.get("welfare", 0),
                "civil_rights": country.politics.civil_rights,
                "austerity": float(
                    country.economy.budget_allocation.get("infrastructure", 0) < 0.15
                ),
                "education": country.economy.budget_allocation.get("education", 0),
                "healthcare": country.economy.budget_allocation.get("healthcare", 0),
                "repression": 1 - country.politics.civil_rights,
            }
            social_events = country.society.update(econ_growth_mod, policy_effects, self.rng)
            if social_events:
                events[name].extend(social_events.values())

            political_events = country.politics.update(country.society.unrest, self.rng)
            if political_events:
                events[name].extend(political_events.values())

            budget_military = country.economy.budget_allocation.get("military", 0)
            military_events = country.military.update(budget_military, country.society.unrest, self.rng)
            if military_events:
                events[name].extend(military_events.values())

            diplomacy_events = country.diplomacy.update(self.tension, self.rng)
            events[name].extend(diplomacy_events)

            if name != player_country and country.automation.get("economy"):
                self._automate_economy(country)
            if country.automation.get("diplomacy"):
                self._automate_diplomacy(country)
            if country.automation.get("military"):
                self._automate_military(country)

            for event in events[name]:
                country.record_event(f"Year {self.year}: {event}")

        self._update_world_tension()
        return events

    def _update_world_tension(self) -> None:
        average_stability = sum(c.politics.stability for c in self.countries.values()) / len(self.countries)
        unrest_pressure = sum(c.society.unrest for c in self.countries.values()) / len(self.countries)
        military_pressure = sum(c.military.total_power() for c in self.countries.values())
        self.tension = max(min(1 - average_stability + unrest_pressure + military_pressure / 1e9, 1.0), 0.0)

    def _automate_economy(self, country: Country) -> None:
        if country.economy.reserves < 0:
            country.economy.adjust_tax_rate(country.economy.tax_rate + 0.01)
        elif country.economy.unemployment > 0.15:
            country.economy.set_budget_allocation("infrastructure", country.economy.budget_allocation["infrastructure"] + 0.05)

    def _automate_diplomacy(self, country: Country) -> None:
        for partner, score in list(country.diplomacy.relations.items()):
            if score < -50:
                country.diplomacy.adjust_relation(partner, 5)
            elif score > 70:
                country.diplomacy.adjust_relation(partner, -3)

    def _automate_military(self, country: Country) -> None:
        doctrine = country.military.doctrine
        if doctrine == "Defensive":
            country.economy.set_budget_allocation("military", min(country.economy.budget_allocation["military"] + 0.02, 0.4))
        elif doctrine == "Guerrilla":
            country.economy.set_budget_allocation("military", min(country.economy.budget_allocation["military"] + 0.01, 0.3))


def generate_world(seed: int, num_countries: int = 6, width: int = 24, height: int = 12) -> World:
    rng = random.Random(seed)
    tiles: List[List[Tile]] = []
    countries: Dict[str, Country] = {}

    country_names = [
        "Arcland",
        "Borealis",
        "Cyrene",
        "Demeris",
        "Elysia",
        "Farsia",
        "Galedor",
        "Helion",
        "Ionara",
        "Jandor",
    ]
    rng.shuffle(country_names)
    selected_names = country_names[:num_countries]

    for y in range(height):
        row: List[Tile] = []
        for x in range(width):
            terrain = rng.choices(TERRAINS, weights=[4, 3, 2, 1, 1, 2])[0]
            climate = rng.choice(CLIMATES)
            resource = rng.choice(RESOURCE_TYPES)
            owner = None
            row.append(Tile(x=x, y=y, terrain=terrain, climate=climate, resource=resource, owner=owner))
        tiles.append(row)

    world_map = WorldMap(width=width, height=height, tiles=tiles)

    for name in selected_names:
        economy = Economy.random(rng)
        politics = PoliticalSystem.random(rng)
        military = Military.random(rng)
        diplomacy = Diplomacy.random(rng)
        society = Society.random(rng)
        countries[name] = Country(
            name=name,
            economy=economy,
            politics=politics,
            military=military,
            diplomacy=diplomacy,
            society=society,
        )

    _assign_territories(world_map, list(countries.keys()), rng)
    _initialize_relations(countries, rng)
    return World(
        map=world_map,
        countries=countries,
        year=rng.randint(1980, 2025),
        tension=rng.uniform(0, 1),
        rng=rng,
        seed=seed,
    )


def _assign_territories(world_map: WorldMap, country_names: List[str], rng: random.Random) -> None:
    shuffled = [(rng.randint(0, world_map.width - 1), rng.randint(0, world_map.height - 1), name) for name in country_names]
    for x, y, name in shuffled:
        world_map.tiles[y][x].owner = name

    frontier: List[Tuple[int, int, str]] = [(x, y, name) for x, y, name in shuffled]
    while frontier:
        x, y, name = frontier.pop(0)
        for nx, ny in _neighbors(x, y, world_map.width, world_map.height):
            tile = world_map.tiles[ny][nx]
            if tile.owner is None and rng.random() < 0.6:
                tile.owner = name
                frontier.append((nx, ny, name))


def _neighbors(x: int, y: int, width: int, height: int) -> List[Tuple[int, int]]:
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    result: List[Tuple[int, int]] = []
    for dx, dy in offsets:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            result.append((nx, ny))
    return result


def _initialize_relations(countries: Dict[str, Country], rng: random.Random) -> None:
    names = list(countries.keys())
    for i, name in enumerate(names):
        for partner in names[i + 1 :]:
            relation = rng.uniform(-30, 40)
            countries[name].diplomacy.relations[partner] = relation
            countries[partner].diplomacy.relations[name] = relation

            if relation > 30:
                countries[name].diplomacy.alliances.append(partner)
                countries[partner].diplomacy.alliances.append(name)
            elif relation < -40:
                countries[name].diplomacy.embargoes.append(partner)
                countries[partner].diplomacy.embargoes.append(name)
