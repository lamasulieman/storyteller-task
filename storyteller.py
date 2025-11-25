from __future__ import annotations

from pathlib import Path

import click

from story_builder.story_builder import build_story_from_files, save_story


MATCH_EVENTS_PATH = Path("data/match_events.json")
CELTIC_SQUAD_PATH = Path("data/celtic-squad.json")
KILMARNOCK_SQUAD_PATH = Path("data/kilmarnock-squad.json")


@click.group()
def cli() -> None:
    """Story builder CLI."""
    pass


@cli.command()
@click.option(
    "--n",
    "top_n",
    default=7,
    show_default=True,
    help="Number of highlight pages to include.",
)
@click.option(
    "--out",
    "out_filename",
    default="story.json",
    show_default=True,
    help="Output JSON filename inside the out/ folder.",
)
def build(top_n: int, out_filename: str) -> None:
    """
    Build a story pack from the default match and squad files.
    """
    story = build_story_from_files(
        match_events_path=MATCH_EVENTS_PATH,
        celtic_squad_path=CELTIC_SQUAD_PATH,
        kilmarnock_squad_path=KILMARNOCK_SQUAD_PATH,
        top_n=top_n,
    )
    out_path = save_story(story, filename=out_filename)
    click.echo(f"Story written to {out_path}")


if __name__ == "__main__":
    cli()
