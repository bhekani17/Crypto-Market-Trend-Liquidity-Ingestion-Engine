import requests
import pandas as pd

def fetch_country_metadata() -> pd.DataFrame:
    """Fetches geographic metadata from REST Countries API."""
    url = "https://restcountries.com/v3.1/all?fields=name,cca3,region,subregion,population,area"
    response = requests.get(url)
    response.raise_for_status()
    
    countries = []
    for item in response.json():
        countries.append({
            "country_code": item.get("cca3"),
            "country_name": item.get("name", {}).get("common"),
            "region": item.get("region"),
            "subregion": item.get("subregion"),
            "population": item.get("population"),
            "area_sq_km": item.get("area")
        })
    return pd.DataFrame(countries)

def fetch_world_bank_indicators(country_code: str) -> list:
    """Fetches GDP (Current USD) for a specific country from World Bank API."""
    # Indicator NY.GDP.MKTP.CD is GDP in current US$
    url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
    params = {"format": "json", "date": "2018:2023"}
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
        
    data = response.json()
    if len(data) < 2 or not data[1]:
        return []
        
    records = []
    for entry in data[1]:
        if entry.get("value") is not None:
            records.append({
                "country_code": country_code,
                "year": int(entry.get("date")),
                "gdp_usd": float(entry.get("value"))
            })
    return records