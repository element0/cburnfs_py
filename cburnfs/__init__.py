"""Using Jupyter Notebook to write and export the python code, relative module imports will not work. Modifying the python path is a workaround."""

import os
import sys

sys.path.append(os.path.dirname(__file__))

from CBurnFS import CBurnFS
