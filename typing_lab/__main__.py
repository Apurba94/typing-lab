"""Start the app: python -m typing_lab [data.db] [--port 8027]"""
import sys

from .fieldkit import main_cli
from .web import create_app

sys.exit(main_cli(create_app, "typing.db", 8027, sys.argv))
