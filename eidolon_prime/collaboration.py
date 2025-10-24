"""Human collaboration layer via command-line interface."""
from __future__ import annotations

from .kernel import Kernel, KernelStatus


class CollaborationLayer:
    """Provides a simple CLI for interacting with the engine."""

    def __init__(self, kernel: Kernel) -> None:
        self._kernel = kernel

    def run_cli(self) -> None:
        print("Eidolon Prime interactive console. Type 'help' for options, 'exit' to quit.")
        while True:
            try:
                prompt = input(">>> ")
            except (EOFError, KeyboardInterrupt):
                print("\nShutting down. Goodbye!")
                break
            stripped = prompt.strip()
            command = stripped.split(" ", 1)[0].lower()
            if command == "exit":
                print("Session closed by user.")
                break
            if command == "help":
                print(self._help_message())
                continue
            if not self._kernel.permits_command(command):
                print(f"Command '{command}' is not permitted by the firewall policy.")
                continue
            if command == "status":
                self._render_status(self._kernel.status())
                continue
            if command == "train":
                payload = stripped[len(command) :].strip()
                if not payload:
                    print("Provide information with 'train <topic>: <details>'.")
                    continue
                try:
                    receipt = self._kernel.train(payload)
                except ValueError as exc:
                    print(f"Training aborted: {exc}")
                    continue
                self.render_response(prompt, receipt.render())
                continue
            if command in {"talk", "chat"}:
                message = stripped[len(command) :].strip()
                if not message:
                    print("Share a message with 'talk <your thought>'.")
                    continue
                result = self._kernel.chat(message)
                self.render_response(prompt, result.render())
                continue
            response = self._kernel.process_request(prompt)
            self.render_response(prompt, response.render())

    def render_response(self, prompt: str, content: str) -> None:
        print(f"\n=== Response to: {prompt} ===")
        print(content)
        print("=== End response ===\n")

    def _render_status(self, status: KernelStatus) -> None:
        print("\n--- Kernel Status ---")
        print("Resources:")
        for key, value in status.resources.items():
            print(f"  {key}: {value}")
        print(f"Personality: {status.personality}")
        print("Memory entries:")
        if not status.memory_stats:
            print("  (empty)")
        else:
            for topic, count in status.memory_stats.items():
                print(f"  {topic}: {count}")
        print("----------------------\n")

    def _help_message(self) -> str:
        return (
            "Available commands:\n"
            "  help   - show this message\n"
            "  status - display kernel resource and memory summary\n"
            "  plan   - request agents to devise a plan\n"
            "  reflect- trigger reflection cycle\n"
            "  log    - ask for a narrative explanation\n"
            "  train  - feed new knowledge into the training ground\n"
            "  talk   - chat with Eidolon Prime about anything on your mind\n"
            "  exit   - quit the session"
        )
