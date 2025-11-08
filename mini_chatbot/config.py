"""Configuration helpers for the mini reasoning chatbot model."""

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Tuple


def _validate_heads(hidden_size: int, num_heads: int) -> None:
    if hidden_size % num_heads != 0:
        raise ValueError(
            "hidden_size must be divisible by num_heads so each head has the same dimension"
        )


@dataclass
class ChatbotConfig:
    """Stores all hyperparameters needed to build the GPT-style chatbot."""

    vocab_size: int
    max_seq_len: int = 256
    hidden_size: int = 512
    num_layers: int = 8
    num_heads: int = 8
    ff_multiplier: float = 4.0
    dropout: float = 0.1
    attention_dropout: float = 0.1
    layer_norm_epsilon: float = 1e-5
    rotary_base: float = 10_000.0
    device: str = "cpu"

    def __post_init__(self) -> None:
        _validate_heads(self.hidden_size, self.num_heads)
        if self.max_seq_len < 8:
            raise ValueError("max_seq_len is unrealistically small; use at least 8 tokens.")
        if self.vocab_size <= 0:
            raise ValueError("vocab_size must be positive.")

    def summary_rows(self) -> Iterable[Tuple[str, str]]:
        """Return key/value pairs for pretty printing."""

        info: Dict[str, str] = {
            "vocab_size": str(self.vocab_size),
            "max_seq_len": str(self.max_seq_len),
            "hidden_size": str(self.hidden_size),
            "num_layers": str(self.num_layers),
            "num_heads": str(self.num_heads),
            "ff_multiplier": f"{self.ff_multiplier:.1f}",
            "dropout": f"{self.dropout:.2f}",
            "attention_dropout": f"{self.attention_dropout:.2f}",
            "device": self.device,
        }
        for key, value in info.items():
            yield key, value

    def asdict(self) -> Dict[str, object]:
        """Return a dictionary representation handy for logging."""

        return asdict(self)
