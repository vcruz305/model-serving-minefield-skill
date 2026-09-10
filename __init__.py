"""Hermes plugin entry point for Model Serving Minefield."""

try:
    # Normal Hermes plugin loading: this directory is imported as a package.
    from .minefield_companion import register
except ImportError:
    # Standalone loaders/test discovery may import repo-root __init__.py directly.
    from minefield_companion import register

__all__ = ["register"]
