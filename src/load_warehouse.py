import duckdb
from src.transform import fetch_country_metadata, fetch_world_bank_indicators

def build_warehouse():
    conn = duckdb.connect("data/world_warehouse.db")
    
    print("Extracting country metadata...")
    df_countries = fetch_country_metadata()
    
    # Create Dimension Table: dim_country
    conn.execute("DROP TABLE IF EXISTS dim_country;")
    conn.execute("""
        CREATE TABLE dim_country (
            country_code VARCHAR PRIMARY KEY,
            country_name VARCHAR,
            region VARCHAR,
            subregion VARCHAR,
            population BIGINT,
            area_sq_km DOUBLE
        );
    """)
    conn.register("stg_countries", df_countries)
    conn.execute("INSERT INTO dim_country SELECT * FROM stg_countries;")
    
    print("Extracting economic indicators for target countries...")
    all_indicators = []
    # Loop through a subset of country codes for demo efficiency
    sample_codes = df_countries['country_code'].dropna().head(20).tolist()
    
    for code in sample_codes:
        indicators = fetch_world_bank_indicators(code)
        all_indicators.extend(indicators)
        
    df_indicators = pd.DataFrame(all_indicators)
    
    # Create Fact Table: fact_economic_indicators
    conn.execute("DROP TABLE IF EXISTS fact_economic_indicators;")
    conn.execute("""
        CREATE TABLE fact_economic_indicators (
            country_code VARCHAR,
            year INT,
            gdp_usd DOUBLE,
            FOREIGN KEY (country_code) REFERENCES dim_country(country_code)
        );
    """)
    
    if not df_indicators.empty:
        conn.register("stg_indicators", df_indicators)
        conn.execute("INSERT INTO fact_economic_indicators SELECT * FROM stg_indicators;")
        
    print("Star Schema warehouse successfully built and populated!")
    
    # Run a test analytical query joining dimension and fact tables
    result = conn.execute("""
        D:
        SELECT 
            c.region,
            f.year,
            SUM(f.gdp_usd) AS total_regional_gdp
        FROM fact_economic_indicators f
        JOIN dim_country c ON f.country_code = c.country_code
        GROUP BY c.region, f.year
        ORDER BY f.year DESC, total_regional_gdp DESC;
    """).fetchdf()
    
    print(result.head())
    conn.close()

if __name__ == "__main__":
    build_warehouse()