import sys
import os

def init_notebook():
    root_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
    sys.path.append(root_dir)

