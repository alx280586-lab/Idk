"""Phase 3 conversation fine-tuning stub."""
from __future__ import annotations

from nfce.conversational_module.generator import generate_response


def main():
    demo = generate_response("Hello", ["This is NFCE."])
    print(demo)


if __name__ == "__main__":
    main()
