"""Jinja2 environment factory."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def get_env() -> Environment:
    return Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)
