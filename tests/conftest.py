"""Put code/ on sys.path so the dossier's modules import as top-level names,
exactly as they do when run as scripts (each does sys.path.insert(0, code/))."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(os.path.dirname(HERE), "code")
if CODE not in sys.path:
    sys.path.insert(0, CODE)
