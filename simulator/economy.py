"""Economic simulation module for the country simulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
import random


RESOURCE_TYPES = [
    "oil",
    "gas",
    "iron",
    "grain",
    "rare_metals",
    "water",
]


def _random_resources(rng: random.Random) -> Dict[str, int]:
    return {resource: rng.randint(0, 5) for resource in RESOURCE_TYPES}


@dataclass
class TradeRelation:
    """Represents a bilateral trade relationship."""

    partner: str
    balance: float = 0.0
    tariffs: float = 0.05


@dataclass
class Economy:
    """Models macro-economic indicators for a country."""

    gdp: float
    debt: float
    tax_rate: float
    inflation: float
    unemployment: float
    reserves: float
    resources: Dict[str, int] = field(default_factory=dict)
    budget_allocation: Dict[str, float] = field(
        default_factory=lambda: {
            "military": 0.2,
            "infrastructure": 0.2,
            "welfare": 0.3,
            "education": 0.2,
            "healthcare": 0.1,
        }
    )
    trade_relations: Dict[str, TradeRelation] = field(default_factory=dict)

    def __post_init__(self) -> None:
        total = sum(self.budget_allocation.values())
        if abs(total - 1.0) > 1e-6:
            self.budget_allocation = {
                k: v / total for k, v in self.budget_allocation.items()
            }
        if not self.resources:
            self.resources = _random_resources(random.Random())

    def update(self, growth_modifier: float, rng: random.Random) -> None:
        """Advance the economy by one turn.

        growth_modifier is influenced by policies, stability, and global context.
        """

        base_growth = rng.uniform(-0.02, 0.05)
        resource_bonus = sum(self.resources.values()) * 0.001
        trade_balance = sum(rel.balance for rel in self.trade_relations.values())
        trade_modifier = trade_balance / max(self.gdp, 1e-6)
        growth = base_growth + resource_bonus + trade_modifier + growth_modifier

        self.gdp *= 1 + growth
        self.gdp = max(self.gdp, 1_000_000)

        budget_surplus = self.gdp * self.tax_rate - self._budget_expense()
        self.reserves += budget_surplus
        self.debt = max(self.debt + self._interest_rate() * self.debt - budget_surplus, 0)

        inflation_shock = rng.uniform(-0.01, 0.02) + growth_modifier * 0.5
        self.inflation = max(min(self.inflation + inflation_shock, 0.25), -0.05)

        unemployment_shift = rng.uniform(-0.02, 0.02) - growth * 0.5
        self.unemployment = max(min(self.unemployment + unemployment_shift, 0.25), 0.01)

    def _budget_expense(self) -> float:
        return sum(allocation * self.gdp for allocation in self.budget_allocation.values())

    def _interest_rate(self) -> float:
        debt_ratio = self.debt / max(self.gdp, 1)
        return 0.02 + debt_ratio * 0.03 + max(self.inflation, 0)

    def adjust_tax_rate(self, new_rate: float) -> None:
        self.tax_rate = max(min(new_rate, 0.75), 0.05)

    def set_budget_allocation(self, sector: str, allocation: float) -> None:
        if sector not in self.budget_allocation:
            raise ValueError(f"Unknown budget sector: {sector}")
        self.budget_allocation[sector] = max(allocation, 0)
        total = sum(self.budget_allocation.values())
        if total == 0:
            raise ValueError("Budget allocations must sum to a positive value")
        self.budget_allocation = {
            k: v / total for k, v in self.budget_allocation.items()
        }

    def add_trade_relation(self, partner: str, balance: float, tariffs: float) -> None:
        self.trade_relations[partner] = TradeRelation(partner, balance, tariffs)

    def summary(self) -> Dict[str, float]:
        return {
            "GDP": round(self.gdp, 2),
            "Debt": round(self.debt, 2),
            "Tax Rate": round(self.tax_rate, 2),
            "Inflation": round(self.inflation, 3),
            "Unemployment": round(self.unemployment, 3),
            "Reserves": round(self.reserves, 2),
        }

    @classmethod
    def random(cls, rng: random.Random) -> "Economy":
        gdp = rng.uniform(50, 800) * 1_000_000_000
        debt = gdp * rng.uniform(0.1, 1.2)
        tax_rate = rng.uniform(0.1, 0.5)
        inflation = rng.uniform(0.0, 0.07)
        unemployment = rng.uniform(0.03, 0.2)
        reserves = gdp * rng.uniform(0.05, 0.5)
        resources = _random_resources(rng)
        return cls(
            gdp=gdp,
            debt=debt,
            tax_rate=tax_rate,
            inflation=inflation,
            unemployment=unemployment,
            reserves=reserves,
            resources=resources,
        )
