from pathlib import Path

import typer

from fnc.inference.hf_bridge import export_gpt2_static_bundle

app = typer.Typer(add_completion=False)


@app.command()
def export(
    model: str = typer.Argument(..., help="Hugging Face model identifier (e.g. 'gpt2')."),
    output: Path = typer.Option(Path("gpt2_static.pt"), help="Path to the output bundle."),
    dtype: str = typer.Option("float16", help="Torch dtype to load the checkpoint with."),
) -> None:
    """Export a GPT-2 style checkpoint into an FNC static bundle."""

    path = export_gpt2_static_bundle(model, output, dtype=dtype)
    typer.echo(f"Bundle saved to {path}")


if __name__ == "__main__":  # pragma: no cover
    app()
