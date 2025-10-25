"""Save and load functionality for the simulator."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Tuple

from .world import World
from .economy import Economy, TradeRelation
from .politics import PoliticalSystem
from .military import Military, ForceGroup
from .diplomacy import Diplomacy, DiplomacyProfile
from .society import Society
from .world import WorldMap, Tile


SAVE_DIR = Path("saves")
SAVE_DIR.mkdir(exist_ok=True)


def save_game(world: World, player_country: str, filename: str) -> None:
    path = SAVE_DIR / filename
    data = {
        "player_country": player_country,
        "world": _world_to_dict(world),
    }
    path.write_text(json.dumps(data, indent=2))


def autosave(world: World, player_country: str) -> None:
    save_game(world, player_country, "autosave.json")


def load_game(filename: str) -> Tuple[World, str]:
    path = SAVE_DIR / filename
    data = json.loads(path.read_text())
    world = _world_from_dict(data["world"])
    return world, data["player_country"]


def _world_to_dict(world: World) -> dict:
    return {
        "year": world.year,
        "tension": world.tension,
        "seed": world.seed,
        "map": {
            "width": world.map.width,
            "height": world.map.height,
            "tiles": [
                [
                    {
                        "terrain": tile.terrain,
                        "climate": tile.climate,
                        "resource": tile.resource,
                        "owner": tile.owner,
                    }
                    for tile in row
                ]
                for row in world.map.tiles
            ],
        },
        "countries": {
            name: {
                "economy": _economy_to_dict(country.economy),
                "politics": _politics_to_dict(country.politics),
                "military": {
                    "army": country.military.army.__dict__,
                    "navy": country.military.navy.__dict__,
                    "air_force": country.military.air_force.__dict__,
                    "logistics": country.military.logistics,
                    "doctrine": country.military.doctrine,
                    "conflicts": country.military.conflicts,
                },
                "diplomacy": {
                    "profile": country.diplomacy.profile.__dict__,
                    "relations": country.diplomacy.relations,
                    "alliances": country.diplomacy.alliances,
                    "embargoes": country.diplomacy.embargoes,
                },
                "society": _society_to_dict(country.society),
                "automation": country.automation,
                "history": country.history,
            }
            for name, country in world.countries.items()
        },
}


def _world_from_dict(data: dict) -> World:
    rng = random.Random()
    rng.seed(data.get("seed", 0))

    tiles = []
    for y, row in enumerate(data["map"]["tiles"]):
        tile_row = []
        for x, tile in enumerate(row):
            tile_row.append(
                Tile(
                    x=x,
                    y=y,
                    terrain=tile["terrain"],
                    climate=tile["climate"],
                    resource=tile["resource"],
                    owner=tile["owner"],
                )
            )
        tiles.append(tile_row)

    world_map = WorldMap(width=data["map"]["width"], height=data["map"]["height"], tiles=tiles)

    countries = {}
    for name, payload in data["countries"].items():
        economy = _economy_from_dict(payload["economy"])
        politics = PoliticalSystem(**payload["politics"])
        military = Military(
            army=ForceGroup(**payload["military"]["army"]),
            navy=ForceGroup(**payload["military"]["navy"]),
            air_force=ForceGroup(**payload["military"]["air_force"]),
            logistics=payload["military"]["logistics"],
            doctrine=payload["military"]["doctrine"],
            conflicts=payload["military"]["conflicts"],
        )
        diplomacy = Diplomacy(
            profile=DiplomacyProfile(**payload["diplomacy"]["profile"]),
            relations=payload["diplomacy"]["relations"],
            alliances=payload["diplomacy"]["alliances"],
            embargoes=payload["diplomacy"]["embargoes"],
        )
        society = Society(**payload["society"])
        from .world import Country as CountryModel

        countries[name] = CountryModel(
            name=name,
            economy=economy,
            politics=politics,
            military=military,
            diplomacy=diplomacy,
            society=society,
            automation=payload.get("automation", {}),
            history=payload.get("history", []),
        )

    from .world import World

    return World(
        map=world_map,
        countries=countries,
        year=data["year"],
        tension=data["tension"],
        rng=rng,
        seed=data.get("seed", 0),
    )


def _economy_to_dict(economy: Economy) -> dict:
    return {
        "gdp": economy.gdp,
        "debt": economy.debt,
        "tax_rate": economy.tax_rate,
        "inflation": economy.inflation,
        "unemployment": economy.unemployment,
        "reserves": economy.reserves,
        "resources": economy.resources,
        "budget_allocation": economy.budget_allocation,
        "trade_relations": {
            partner: {
                "partner": rel.partner,
                "balance": rel.balance,
                "tariffs": rel.tariffs,
            }
            for partner, rel in economy.trade_relations.items()
        },
    }


def _economy_from_dict(data: dict) -> Economy:
    trade_relations = {
        partner: TradeRelation(**rel_dict)
        for partner, rel_dict in data.get("trade_relations", {}).items()
    }
    return Economy(
        gdp=data["gdp"],
        debt=data["debt"],
        tax_rate=data["tax_rate"],
        inflation=data["inflation"],
        unemployment=data["unemployment"],
        reserves=data["reserves"],
        resources=data.get("resources", {}),
        budget_allocation=data.get("budget_allocation", {}),
        trade_relations=trade_relations,
    )


def _politics_to_dict(politics: PoliticalSystem) -> dict:
    return {
        "government_type": politics.government_type,
        "approval_rating": politics.approval_rating,
        "stability": politics.stability,
        "corruption": politics.corruption,
        "civil_rights": politics.civil_rights,
        "election_cycle": politics.election_cycle,
        "next_election": politics.next_election,
        "opposition_strength": politics.opposition_strength,
    }


def _society_to_dict(society: Society) -> dict:
    return {
        "population": society.population,
        "happiness": society.happiness,
        "unrest": society.unrest,
        "literacy": society.literacy,
        "healthcare": society.healthcare,
        "inequality": society.inequality,
        "median_age": society.median_age,
        "religion": society.religion,
    }
