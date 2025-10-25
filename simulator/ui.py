"""Console user interface for the country simulator."""
from __future__ import annotations

from typing import Dict

from .world import World, Country


class GameUI:
    def __init__(self, world: World, player_country: str) -> None:
        self.world = world
        self.player_country = player_country

    def main_loop(self) -> None:
        while True:
            country = self.world.countries[self.player_country]
            print("\n==== COUNTRY SIMULATOR ====")
            print(f"Year: {self.world.year} | Global tension: {self.world.tension:.2f}")
            print(f"Playing as: {self.player_country}")
            print(self.world.map.render(focus_country=self.player_country))
            print("1) View country summary")
            print("2) Adjust policies")
            print("3) Engage in diplomacy")
            print("4) Manage military")
            print("5) Toggle automation")
            print("6) Save game")
            print("7) Advance to next year")
            print("0) Quit")
            choice = input("Select an option: ")
            if choice == "1":
                self._show_summary(country)
            elif choice == "2":
                self._adjust_policies(country)
            elif choice == "3":
                self._diplomacy_menu(country)
            elif choice == "4":
                self._military_menu(country)
            elif choice == "5":
                self._toggle_automation(country)
            elif choice == "6":
                from .save_load import save_game

                filename = input("Enter save filename: ") or "savegame.json"
                save_game(self.world, self.player_country, filename)
                print(f"Game saved to {filename}")
            elif choice == "7":
                self._advance_turn()
            elif choice == "0":
                print("Exiting game.")
                break
            else:
                print("Invalid choice. Try again.")

    def _show_summary(self, country: Country) -> None:
        summary = country.summary()
        for section, data in summary.items():
            print(f"\n-- {section} --")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"{key}: {value}")
            else:
                print(data)
        if country.history:
            print("\nRecent events:")
            for entry in country.history[-5:]:
                print(f" - {entry}")

    def _adjust_policies(self, country: Country) -> None:
        print("\nAdjust Policies")
        print(f"Current tax rate: {country.economy.tax_rate:.2f}")
        new_tax = input("Enter new tax rate (0.05 - 0.75, blank to skip): ")
        if new_tax:
            try:
                country.economy.adjust_tax_rate(float(new_tax))
                print("Tax rate updated.")
            except ValueError:
                print("Invalid tax rate.")
        print("Budget allocations:")
        for sector, allocation in country.economy.budget_allocation.items():
            print(f" - {sector}: {allocation:.2f}")
        sector = input("Sector to adjust (blank to exit): ")
        if sector:
            try:
                allocation = float(input("New allocation share (e.g., 0.25): "))
                country.economy.set_budget_allocation(sector, allocation)
                print("Budget updated and normalized.")
            except ValueError as exc:
                print(f"Error: {exc}")

    def _diplomacy_menu(self, country: Country) -> None:
        print("\nDiplomacy")
        for partner, score in country.diplomacy.relations.items():
            print(f" - {partner}: {score:.1f}")
        target = input("Choose a country to influence (blank to exit): ")
        if target and target in self.world.countries and target != self.player_country:
            action = input("Improve relations (i) or worsen (w)? ")
            delta = 5 if action.lower().startswith("i") else -5
            country.diplomacy.adjust_relation(target, delta)
            print(f"Relations with {target} adjusted by {delta} points.")
        else:
            print("No changes made.")

    def _military_menu(self, country: Country) -> None:
        print("\nMilitary")
        print(f"Doctrine: {country.military.doctrine}")
        print(f"Total Power: {country.military.total_power():.0f}")
        if country.military.conflicts:
            for opponent, status in country.military.conflicts.items():
                print(f"Conflict with {opponent}: {status}")
        opponent = input("Launch offensive against which country? (blank to cancel): ")
        if opponent and opponent in self.world.countries:
            outcome = country.military.deploy(self.world.countries[opponent].military.total_power(), self.world.rng)
            print(f"Battle outcome: {outcome}")
            country.record_event(f"Offensive against {opponent}: {outcome}")
        else:
            print("No offensive launched.")

    def _toggle_automation(self, country: Country) -> None:
        print("\nAutomation Settings")
        for system, enabled in country.automation.items():
            print(f" - {system}: {'ON' if enabled else 'OFF'}")
        system = input("Toggle which system? (economy/military/diplomacy): ")
        if system in country.automation:
            country.automation[system] = not country.automation[system]
            print(f"Automation for {system} is now {'ON' if country.automation[system] else 'OFF'}.")
        else:
            print("Unknown system.")

    def _advance_turn(self) -> None:
        from .ai import ai_take_turn
        from .save_load import autosave

        ai_events: Dict[str, Dict[str, str]] = {}
        for name in self.world.countries:
            if name != self.player_country:
                ai_events[name] = ai_take_turn(self.world, name)
        world_events = self.world.update(self.player_country)
        autosave(self.world, self.player_country)
        print("\n--- Year Advanced ---")
        for name, events in ai_events.items():
            for category, description in events.items():
                print(f"{name}: {category} - {description}")
        for name, events in world_events.items():
            if events:
                print(f"{name} events:")
                for event in events:
                    print(f" * {event}")
        print("Autosave complete.")
