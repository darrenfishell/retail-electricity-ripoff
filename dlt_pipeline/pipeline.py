import dlt
import dlt_pipeline.file_transformations as ft
import pandas as pd
import os

@dlt.resource(
    primary_key=[
        'year',
        'utility_number',
        'utility_name',
        'state',
        'customer_type',
        'service_type',
        'part'
    ]
)
def eia_df(end_year=2025):
    ft.download_eia_861(end_year=end_year)
    df = ft.process_and_merge_861()
    yield df

@dlt.resource
def customers_df():
    customer_df, _ = ft.process_customer_migration_files()
    yield customer_df

@dlt.resource
def load_df():
    _, load_df = ft.process_customer_migration_files()
    yield load_df

@dlt.resource
def standard_offer_df():
    df = pd.read_csv('prepared_data/standard_offer.csv')
    df['start_date'] = pd.to_datetime(df['start_date'], format='mixed')
    yield df

db_path = os.path.abspath('data/retail_electricity.duckdb')

pipeline = dlt.pipeline(
    pipeline_name='retail_electricity_pipeline',
    destination=dlt.destinations.duckdb(db_path),
    dataset_name='stage'
)

@dlt.source
def all_data():
    yield eia_df()
    yield customers_df()
    yield load_df()
    yield standard_offer_df()

def main():
    # Run pipeline using the generator
    load_info = pipeline.run(
        all_data(),
        write_disposition='replace'
    )
    print(load_info)

if __name__ == '__main__':
    main()