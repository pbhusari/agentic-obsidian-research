from __future__ import annotations

import json
from pathlib import Path


def init_vault(vault_path: str) -> None:
    root = Path(vault_path)
    for sub in ["papers", "concepts", "threats", "synthesis", "synthesis/errors"]:
        (root / sub).mkdir(parents=True, exist_ok=True)

    obsidian_dir = root / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)

    # Graph color groups by node type
    graph_config = {
        "colorGroups": [
            {"query": 'tag:#vantage/paper', "color": {"a": 1, "rgb": 14400668}},
            {"query": 'tag:#vantage/concept', "color": {"a": 1, "rgb": 5787475}},
            {"query": 'tag:#vantage/threat', "color": {"a": 1, "rgb": 14701138}},
            {"query": 'tag:#vantage/dashboard', "color": {"a": 1, "rgb": 10040166}},
        ]
    }
    (obsidian_dir / "graph.json").write_text(json.dumps(graph_config, indent=2))

    # Minimal app config
    app_config = {"legacyEditor": False, "livePreview": True}
    (obsidian_dir / "app.json").write_text(json.dumps(app_config, indent=2))
