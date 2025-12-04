import os

# Jupyter path migration: use platformdirs standard (future-proof for jupyter_core v6)
os.environ.setdefault("JUPYTER_PLATFORM_DIRS", "1")

PANTHEON_DIR = os.path.realpath(
    os.path.expanduser(os.environ.get("CONFIG_DIR", "~/.pantheon"))
)
CONFIG_FILE = os.path.join(PANTHEON_DIR, "config.yaml")
CLI_HISTORY_FILE = os.path.join(PANTHEON_DIR, "cli_history")
