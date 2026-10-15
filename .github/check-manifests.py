"""Keep the two independently buildable image manifests in sync."""

from pathlib import Path

import yaml


def check_manifests(root: Path) -> None:
    anatase = yaml.safe_load((root / "anatase.yml").read_text())
    base = yaml.safe_load((root / "base.yml").read_text())
    expected_cards = [card for card in anatase["cards"] if card != "cards/de/kde"]
    if base["cards"] != expected_cards:
        raise ValueError("base cards must match Anatase in order, excluding cards/de/kde")
    for key in ("runtime", "flatpaks", "installer"):
        if key in base:
            raise ValueError(f"base must not declare {key}")

    # Only image identity, cards, and desktop-only outputs may differ.
    identity_keys = {"name", "cards", "runtime", "flatpaks", "installer", "labels"}
    if {k: v for k, v in base.items() if k not in identity_keys} != {
        k: v for k, v in anatase.items() if k not in identity_keys
    }:
        raise ValueError("base and Anatase must have identical shared build settings")
    identity_labels = {
        "org.opencontainers.image.title",
        "org.opencontainers.image.description",
    }
    if {k: v for k, v in base["labels"].items() if k not in identity_labels} != {
        k: v for k, v in anatase["labels"].items() if k not in identity_labels
    }:
        raise ValueError("base and Anatase must have identical shared OCI labels")


if __name__ == "__main__":
    check_manifests(Path(__file__).resolve().parent.parent)
    print("Base and Anatase manifests are consistent")
