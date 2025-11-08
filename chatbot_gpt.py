"""Beginner-friendly GPT-style chatbot script using PyTorch and Hugging Face Transformers.

This single-file program walks you through building, understanding, and testing a
miniature GPT-style chatbot model. The focus is on clarity and step-by-step
explanations so you can explore the entire pipeline and later fine-tune the model
with your own dialogue data.

The script covers the following topics:
1. Building a configurable GPT-like transformer model completely from scratch.
2. Loading a tokenizer and preparing USER/BOT chat text for the model.
3. Constructing a super small example dataset and batching helper.
4. Demonstrating a lightweight training loop so you can see how optimization works.
5. Sampling text from the model with random decoding to simulate chatbot replies.

You can run this file as-is on a CPU-only laptop. The model defaults to a tiny
configuration so it fits in memory easily, yet the code structure matches what you
would use for larger models too.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import GPT2Tokenizer


# ----------------------------------------------------------------------------
# Device helper --------------------------------------------------------------
# ----------------------------------------------------------------------------

def get_device() -> torch.device:
    """Pick CPU by default but use CUDA if available.

    Keeping this logic in one place avoids sprinkling device handling throughout
    the rest of the script and makes it clear how to move tensors/models between
    CPU and GPU.
    """

    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ----------------------------------------------------------------------------
# HOW TO TRAIN THIS MODEL
# 1. Gather a small dataset of USER/BOT conversations (plain text or JSON).
# 2. Tokenize it using GPT2Tokenizer or SentencePiece.
# 3. Use the provided train_step() loop to fine-tune for a few epochs.
# 4. Save weights with torch.save(model.state_dict(), "chatbot.pth")
# 5. Load weights later with model.load_state_dict(torch.load("chatbot.pth"))
#
# For faster training:
# - Reduce hidden_size or num_layers to make the model smaller.
# - Train with a small batch size (like 1 or 2).
# - Use 4-bit quantization or QLoRA if you have a GPU.
# ----------------------------------------------------------------------------


@dataclass
class GPTConfig:
    """Tiny configuration object describing the core model dimensions.

    Keeping the config separate from the model class makes it easy to experiment
    with different model sizes. For laptops or limited hardware you can shrink the
    numbers; for larger hardware you can scale them up while keeping the code
    identical.
    """

    vocab_size: int
    max_seq_len: int = 128
    hidden_size: int = 256
    num_layers: int = 4
    num_heads: int = 4
    dropout: float = 0.1


class MultiHeadSelfAttention(nn.Module):
    """Basic multi-head self-attention block used in GPT models."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        assert (
            config.hidden_size % config.num_heads == 0
        ), "hidden_size must be divisible by num_heads"
        self.num_heads = config.num_heads
        self.head_dim = config.hidden_size // config.num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(config.hidden_size, config.hidden_size * 3)
        self.out_proj = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, hidden_size = x.size()

        # Project the input into queries, keys, and values.
        qkv = self.qkv(x)  # shape: (batch, seq_len, hidden_size * 3)
        q, k, v = qkv.chunk(3, dim=-1)

        # Split the last dimension into (num_heads, head_dim) for multi-head attention.
        def reshape_heads(t: torch.Tensor) -> torch.Tensor:
            return t.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        q = reshape_heads(q)
        k = reshape_heads(k)
        v = reshape_heads(v)

        # Compute scaled dot-product attention scores.
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale

        # Mask out future tokens to preserve the autoregressive property.
        mask = torch.triu(
            torch.ones(seq_len, seq_len, device=x.device, dtype=torch.bool),
            diagonal=1,
        )
        attn_scores = attn_scores.masked_fill(mask, float("-inf"))

        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        context = torch.matmul(attn_weights, v)  # shape: (batch, num_heads, seq_len, head_dim)
        context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, hidden_size)

        return self.out_proj(context)


class FeedForward(nn.Module):
    """Simple feed-forward block used inside the transformer."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        inner_dim = config.hidden_size * 4
        self.net = nn.Sequential(
            nn.Linear(config.hidden_size, inner_dim),
            nn.GELU(),
            nn.Linear(inner_dim, config.hidden_size),
            nn.Dropout(config.dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TransformerBlock(nn.Module):
    """Single GPT-style transformer block."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(config.hidden_size)
        self.ln2 = nn.LayerNorm(config.hidden_size)
        self.attn = MultiHeadSelfAttention(config)
        self.ff = FeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Add & Norm pattern used in transformers.
        x = x + self.attn(self.ln1(x))
        x = x + self.ff(self.ln2(x))
        return x


class MiniGPT(nn.Module):
    """A small GPT-style language model."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.hidden_size)
        self.position_embedding = nn.Embedding(config.max_seq_len, config.hidden_size)
        self.dropout = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList([TransformerBlock(config) for _ in range(config.num_layers)])
        self.final_ln = nn.LayerNorm(config.hidden_size)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len = input_ids.size()
        device = input_ids.device

        positions = torch.arange(seq_len, device=device).unsqueeze(0).expand(batch_size, seq_len)
        x = self.token_embedding(input_ids) + self.position_embedding(positions)
        x = self.dropout(x)

        for block in self.blocks:
            x = block(x)

        x = self.final_ln(x)
        logits = self.lm_head(x)
        return logits


def count_parameters(model: nn.Module) -> int:
    """Return the number of trainable parameters in the model."""

    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_tokenizer() -> GPT2Tokenizer:
    """Load the GPT2 tokenizer and add basic chat tokens if needed."""

    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

    # Ensure USER: and BOT: tokens are handled without splitting each character.
    special_tokens = {"additional_special_tokens": ["USER:", "BOT:"]}
    added = tokenizer.add_special_tokens(special_tokens)
    if added > 0:
        print(f"Added {added} special tokens to the tokenizer vocabulary.")
        print(
            "The configuration below will use the new vocabulary size so the"
            " embeddings line up with the tokenizer."
        )
    return tokenizer


def describe_config(config: GPTConfig) -> None:
    """Print the current configuration so users know what each value means."""

    print("Model configuration:")
    print(f"  Vocabulary size    : {config.vocab_size}")
    print(f"  Max sequence length: {config.max_seq_len}")
    print(f"  Hidden size        : {config.hidden_size}")
    print(f"  Number of layers   : {config.num_layers}")
    print(f"  Attention heads    : {config.num_heads}")
    print(f"  Dropout rate       : {config.dropout}")


def tokenize_chat_examples(tokenizer: GPT2Tokenizer) -> None:
    """Show how to tokenize USER/BOT text."""

    texts = ["USER: hello", "BOT: hi!"]
    encodings = tokenizer(texts, return_tensors="pt", padding=True)
    print("Tokenization example:")
    for text, tokens in zip(texts, encodings["input_ids"]):
        print(f"  Text: {text}")
        print(f"  Token IDs: {tokens.tolist()}")


def sample_dataset() -> List[Tuple[str, str]]:
    """Return a tiny list of sample dialogues.

    Replace this with your own conversation pairs. Keeping the structure as a
    list of ("USER:", "BOT:") strings makes it easy to plug into the rest of
    the script without additional preprocessing.
    """

    return [
        ("USER: hi", "BOT: hey!"),
        ("USER: what is 2+2?", "BOT: 4"),
        (
            "USER: tell me a joke",
            "BOT: why did the byte go to therapy? because it couldn’t process its feelings.",
        ),
    ]


def prepare_batch(
    tokenizer: GPT2Tokenizer,
    examples: List[Tuple[str, str]],
    max_length: int,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Tokenize USER and BOT texts and create input/target tensors.

    The returned `input_ids` are fed into the model, while `labels` are the
    expected next-token IDs the model should predict. Padding positions are set
    to -100 so PyTorch's cross-entropy loss ignores them automatically.
    """

    input_texts = [f"{user} {bot}" for user, bot in examples]
    encodings = tokenizer(
        input_texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )

    input_ids = encodings["input_ids"].to(device)
    attention_mask = encodings["attention_mask"].to(device)

    # For language modeling, targets are the same as input_ids but shifted by one position.
    labels = input_ids.clone()
    labels[attention_mask == 0] = -100  # Ignore padding positions in the loss.

    return input_ids, labels


def train_step(
    model: MiniGPT,
    tokenizer: GPT2Tokenizer,
    optimizer: torch.optim.Optimizer,
    examples: List[Tuple[str, str]],
    device: torch.device,
) -> float:
    """Perform a single dummy training step and return the loss.

    This function mirrors what a real training step would do: tokenize a batch,
    run the model forward, compute cross-entropy, and update the weights via
    backpropagation. We only run it on a toy dataset so the example finishes
    quickly on CPU.
    """

    model.train()
    input_ids, labels = prepare_batch(
        tokenizer, examples, model.config.max_seq_len, device
    )

    logits = model(input_ids)
    loss = F.cross_entropy(
        logits.view(-1, logits.size(-1)),
        labels.view(-1),
        ignore_index=-100,
    )

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()


def dummy_training_loop(
    model: MiniGPT, tokenizer: GPT2Tokenizer, device: torch.device
) -> None:
    """Demonstrate a short training loop without heavy computation.

    Use this as a blueprint for your own training routine: load your dataset,
    call `train_step` repeatedly, and monitor the loss. Here we only run two
    epochs over a three-example dataset to keep things snappy for beginners.
    """

    examples = sample_dataset()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

    for epoch in range(1, 3):  # Just two epochs for demonstration.
        loss = train_step(model, tokenizer, optimizer, examples, device)
        print(f"Epoch {epoch} done! Loss: {loss:.4f}")

    print("Training loop finished. Add more epochs/data for real training!")


@torch.no_grad()
def generate_reply(
    model: MiniGPT,
    tokenizer: GPT2Tokenizer,
    prompt: str,
    max_new_tokens: int = 40,
    temperature: float = 1.0,
    device: Optional[torch.device] = None,
) -> str:
    """Generate a reply from the model using random sampling.

    The sampling strategy here is intentionally simple: we draw the next token
    from the probability distribution produced by the model at each step. You
    can plug in more advanced methods such as top-k or nucleus sampling once
    you're comfortable with the basics.
    """

    model.eval()
    if device is None:
        device = next(model.parameters()).device

    input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"].to(device)
    generated = input_ids.clone()

    for _ in range(max_new_tokens):
        logits = model(generated)
        next_token_logits = logits[:, -1, :] / max(temperature, 1e-6)
        probs = F.softmax(next_token_logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        generated = torch.cat([generated, next_token], dim=1)

        # Stop if the tokenizer generates the end-of-text token.
        if next_token.item() == tokenizer.eos_token_id:
            break

    return tokenizer.decode(generated[0])


def main() -> None:
    print("\n=== Mini GPT-Style Chatbot Builder ===\n")

    device = get_device()
    print(f"Using device: {device}")

    tokenizer = build_tokenizer()

    # Create a configuration. Adjust hidden_size, num_layers, and num_heads to
    # scale the model up or down. Keeping hidden_size <= 512 and num_layers <= 12
    # helps stay well under 4 billion parameters.
    config = GPTConfig(
        vocab_size=len(tokenizer),
        max_seq_len=128,
        hidden_size=256,
        num_layers=4,
        num_heads=4,
    )

    describe_config(config)

    model = MiniGPT(config)
    model.to(device)
    print(model)

    total_params = count_parameters(model)
    print(f"Total parameters: {total_params:,}")
    print(
        "Tip: Increase hidden_size, num_layers, or num_heads gradually if you want"
        " a more capable model, but keep an eye on your hardware limits."
    )

    tokenize_chat_examples(tokenizer)

    print("Running dummy training loop (no heavy computation)...")
    dummy_training_loop(model, tokenizer, device)

    prompt = "USER: hello"
    reply = generate_reply(model, tokenizer, prompt, device=device)
    print("Sample generation:")
    print(reply)

    print("Model built! You can now train it with your data using the train_step() function.")


if __name__ == "__main__":
    main()
