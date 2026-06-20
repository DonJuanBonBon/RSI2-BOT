"""Make `import algo_core...` work when running pytest from inside the package dir."""
import os
import sys

# add the PARENT of algo_core/ to sys.path so `algo_core` is importable
HERE = os.path.dirname(os.path.abspath(__file__))
PKG_PARENT = os.path.abspath(os.path.join(HERE, "..", ".."))
if PKG_PARENT not in sys.path:
    sys.path.insert(0, PKG_PARENT)
