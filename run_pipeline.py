"""
run_pipeline.py runs the CityScope data pipeline in order.
It cleans the Census demographic data, loads the spatial
city boundaries, and then runs the city analysis.
"""

import subprocess
import sys

# Run the Census data cleaning stage.
subprocess.run([sys.executable, "census_clean.py"], check=True)

# Run the spatial data cleaning stage.
subprocess.run([sys.executable, "spatial_clean.py"], check=True)

# Run the city analysis stage.
subprocess.run([sys.executable, "query_cities.py"], check=True)