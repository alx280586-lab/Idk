"""Rich-powered Grok-inspired console interface."""
from __future__ import annotations

from datetime import datetime

from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ai_system.config import SystemConfig
from ai_system.core.memory import MemoryTrace
from ai_system.interfaces.runtime import RuntimeContext, create_runtime

console = Console()


class GrokConsole:
    """Interactive session manager with stylised Grok visuals."""

    def __init__(self, config: SystemConfig | None = None) -> None:
        runtime: RuntimeContext = create_runtime(config)
        self.config = runtime.config
        self.knowledge = runtime.knowledge
        self.memory = runtime.memory
        self.reasoner = runtime.reasoner

    def _header(self) -> Panel:
        title = "[magenta bold]GROK-SCRIPT ORBITAL[/]"
        subtitle = (
            "[white]Scripting intelligence with rebellious wit."
            + "\n"
            + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        )
        return Panel(Align.center(subtitle), title=title, border_style="magenta", box=box.ROUNDED)

    def _history_panel(self) -> Panel:
        table = Table(show_header=False, box=box.SIMPLE_HEAVY)
        table.add_column("Context")
        table.add_column("Score", justify="right")
        for trace in reversed(self.memory.recall()[-5:]):
            table.add_row(trace.context, f"{trace.score:.2f}")
        if not table.rows:
            table.add_row("No missions yet", "-")
        return Panel(table, title="Recent Missions", border_style="cyan")

    def _knowledge_panel(self) -> Panel:
        docs = list((self.config.data_root / "knowledge").glob("*.md"))[-5:]
        body = "\n".join(doc.name for doc in docs) if docs else "Bootstrapping..."
        return Panel(body, title="Knowledge Cache", border_style="green")

    def launch(self) -> None:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
        )
        layout["body"].split_row(
            Layout(name="history", ratio=1),
            Layout(name="main", ratio=2),
            Layout(name="knowledge", ratio=1),
        )

        with Live(layout, console=console, screen=True, refresh_per_second=4):
            layout["header"].update(self._header())
            layout["history"].update(self._history_panel())
            layout["knowledge"].update(self._knowledge_panel())

            while True:
                mission = Prompt.ask("[bold cyan]Input a mission goal[/]", default="Author a witty automation script")
                context = Prompt.ask("[bold cyan]Add keywords (space separated)[/]", default="automation humor resilience")
                thought = self.reasoner.brainstorm(mission, {"keywords": context})
                response = f"Mission: {mission}\nPlan: {thought.conclusion}\nNotes:\n- " + "\n- ".join(thought.considerations)
                console.print(Panel(response, title="Grok Response", border_style="magenta"))
                self.memory.record(MemoryTrace(mission, response, thought.confidence, ["grok"]))
                layout["history"].update(self._history_panel())
                layout["knowledge"].update(self._knowledge_panel())
                if Prompt.ask("[bold yellow]Log mission to knowledge base?[/]", choices=["y", "n"], default="y") == "y":
                    stored_path = self.knowledge.store(
                        f"grok_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        response,
                    )
                    console.print(f"[green]Stored at {stored_path}")
                if Prompt.ask("[bold red]Another mission?[/]", choices=["y", "n"], default="y") == "n":
                    break


def run() -> None:
    GrokConsole().launch()


if __name__ == "__main__":
    run()

