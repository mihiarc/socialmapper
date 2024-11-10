import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file (if using)
load_dotenv()

# Census API key
API_KEY = os.getenv('CENSUS_API_KEY')  # Ensure 'CENSUS_API_KEY' is set in your environment

if not API_KEY:
    raise ValueError("Census API key not found. Please set the 'CENSUS_API_KEY' environment variable.")

# Define the API endpoint
year = 2021  # ACS 5-Year Estimates year
dataset = 'acs/acs5'
base_url = f'https://api.census.gov/data/{year}/{dataset}'

# Define the variables to retrieve
variables = ['B01003_001E', 'NAME']  # Total population and Block Group name

# Define the geography: all Block Groups in NC
# Block Group identifiers require specifying state, county, and tract
# 'for=block group:*' specifies all block groups
# 'in=state:37 county:* tract:*' limits to all NC block groups across all tracts
params = {
    'get': ','.join(variables),
    'for': 'block group:*',
    'in': 'state:37 county:* tract:*',
    'key': API_KEY
}

# Make the API request
response = requests.get(base_url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Rename columns for clarity
    df.rename(columns={
        'B01003_001E': 'Population',
        'NAME': 'Block_Group_Name',
        'state': 'State_FIPS',
        'county': 'County_FIPS',
        'tract': 'Tract_Code',
        'block group': 'Block_Group_Number'
    }, inplace=True)
    
    # Convert Population to numeric, handle missing or non-numeric data
    df['Population'] = pd.to_numeric(df['Population'], errors='coerce')
    
    # Optionally, create a unique identifier for each Block Group
    df['Block_Group_ID'] = df['State_FIPS'] + df['County_FIPS'] + df['Tract_Code'] + df['Block_Group_Number']
    
    # Display the first few rows
    print(df.head())
    
    # Save to CSV
    df.to_csv('nc_block_groups_population.csv', index=False)
    print("Data saved to 'nc_block_groups_population.csv'")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
