import os
import sys
import unittest

def import_src():
    project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src/gravity_lab')
    sys.path.insert(0, project_dir)

import_src()

if __name__ == "__main__":
    pass