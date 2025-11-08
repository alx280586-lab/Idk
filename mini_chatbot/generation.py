"""Text generation helpers for sampling chatbot replies."""

from typing import Optional

import torch
import torch.nn.functional as F


def top_k_filter(logits: torch.Tensor, top_k: Optional[int]) -> torch.Tensor:
    """Keep only the top_k tokens with highest probability mass."""

    if top_k is None or top_k <= 0:
        return logits
    values, _ = torch.topk(logits, top_k)
    cutoff = values[..., -1, None]
    return torch.where(logits < cutoff, torch.full_like(logits, float("-inf")), logits)


def generate_reply(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 80,
    temperature: float = 0.8,
    top_k: Optional[int] = 50,
) -> str:
    """Sample a chatbot reply using nucleus-style top-k sampling."""

    device = next(model.parameters()).device
    model.eval()

    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        add_special_tokens=True,
    )
    input_ids = encoded["input_ids"].to(device)

    generated = input_ids
    with torch.no_grad():
        for _ in range(max_new_tokens):
            logits = model(generated)
            next_token_logits = logits[:, -1, :] / max(temperature, 1e-5)
            filtered = top_k_filter(next_token_logits, top_k)
            probs = F.softmax(filtered, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            generated = torch.cat([generated, next_token], dim=-1)
            if next_token.item() == tokenizer.eos_token_id:
                break

    decoded = tokenizer.decode(generated[0], skip_special_tokens=False)
    return decoded[len(prompt) :].strip()
