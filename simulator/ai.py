"""AI behaviour for non-player countries."""
from __future__ import annotations

from typing import Dict
import random

from .world import World, Country


def ai_take_turn(world: World, country_name: str) -> Dict[str, str]:
    country = world.countries[country_name]
    rng = world.rng
    events: Dict[str, str] = {}

    if not country.automation.get("economy"):
        if country.economy.unemployment > 0.15 and rng.random() < 0.5:
            try:
                country.economy.set_budget_allocation("infrastructure", country.economy.budget_allocation["infrastructure"] + 0.03)
                events["economy"] = "Infrastructure spending increased to tackle unemployment."
            except ValueError:
                pass
        if country.economy.inflation > 0.1 and rng.random() < 0.4:
            country.economy.adjust_tax_rate(country.economy.tax_rate + 0.01)
            events["economy"] = "Tax rate raised to combat inflation."

    if country.politics.stability < 0.3 and rng.random() < 0.5:
        country.politics.reform(civil_rights_delta=0.05, corruption_delta=-0.03)
        events["politics"] = "Government enacts reforms to restore stability."

    for partner, relation in list(country.diplomacy.relations.items()):
        if relation < -40 and rng.random() < country.diplomacy.profile.aggression:
            country.military.conflicts[partner] = "Skirmishes"
            events["military"] = f"Border clashes reported with {partner}."
        elif relation > 50 and rng.random() < country.diplomacy.profile.openness:
            country.diplomacy.alliances.append(partner)
            events["diplomacy"] = f"Alliance strengthened with {partner}."

    if world.tension > 0.7 and rng.random() < country.diplomacy.profile.espionage:
        target = rng.choice([n for n in world.countries if n != country_name])
        country.diplomacy.adjust_relation(target, -5)
        events["espionage"] = f"Espionage incident strains relations with {target}."

    return events
