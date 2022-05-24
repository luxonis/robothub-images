import os
from pathlib import Path

_IS_INTERACTIVE = "DISPLAY" in os.environ or os.name == "nt"
IS_INTERACTIVE = False if "APP_DISABLE_INTERACTIVE" in os.environ else _IS_INTERACTIVE
CONFIG_FILE = os.environ.get("APP_CONFIG_FILE", "config.json" if IS_INTERACTIVE else "/config.json")
BROKER_SOCKET = os.environ.get("BROKER_SOCKET", "/socket/broker.sock")
STORAGE_DIR = os.environ.get("APP_STORAGE_DIR", os.getcwd() if IS_INTERACTIVE else "/storage")
PUBLIC_DIR = os.environ.get("APP_PUBLIC_DIR", str(Path(STORAGE_DIR).joinpath("public")))
