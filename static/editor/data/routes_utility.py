import os
import sys

# Get the directory containing the 'data' directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the parent directory to the module search path
sys.path.append(parent_dir)

# Now you should be able to import from data.routes_utility
from data.routes_utility import *