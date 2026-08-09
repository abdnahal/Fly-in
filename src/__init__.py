"""Fly-in package.

Set pygame's banner-suppression flag before any submodule imports pygame,
so the program's stdout stays limited to the simulation output. This runs
when the package is loaded, which is before ``__main__`` executes.
"""
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
