"""Utilities for building a reasoning-oriented mini GPT chatbot.

This package splits the beginner tutorial into small modules so you can
inspect each part individually and gain a deeper understanding of the
architecture, data processing, and generation utilities.
"""

from .config import ChatbotConfig
from .datasets import SAMPLE_DIALOGUES, ReasoningChatDataset
from .generation import generate_reply
from .model import MiniReasoningGPT, build_model
from .tokenization import load_tokenizer, tokenize_chat_example
from .training import batch_iterator, run_dummy_training, train_step
from .utils import count_parameters, describe_model

__all__ = [
    "ChatbotConfig",
    "SAMPLE_DIALOGUES",
    "ReasoningChatDataset",
    "MiniReasoningGPT",
    "build_model",
    "load_tokenizer",
    "tokenize_chat_example",
    "generate_reply",
    "batch_iterator",
    "train_step",
    "run_dummy_training",
    "count_parameters",
    "describe_model",
]
