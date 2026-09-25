"""
ui_demo.py is an interactive python shell to demonstrate successful 
querying of CityScope proccessed data
"""

import pyarrow.parquet as pq

crime = pq.read_table("data/processed/crime_city")
weather = pq.read_table("data/processed/weather_monthly")

print(crime.column_names)
print(weather.column_names)
