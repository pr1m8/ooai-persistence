"""Sphinx configuration for ooai-persistence."""

from __future__ import annotations

import os

project = "ooai-persistence"
author = "William R. Astley"
copyright = "2026, William R. Astley"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
]

autodoc_typehints = "description"
html_theme = "furo"
html_title = "ooai-persistence"
html_baseurl = os.getenv(
    "READTHEDOCS_CANONICAL_URL",
    "https://pr1m8.github.io/ooai-persistence/",
)
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
