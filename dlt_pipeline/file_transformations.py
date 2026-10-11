import pandas as pd
import requests
import numpy as np
import os
import glob
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from zipfile import ZipFile
from io import BytesIO
from datetime import date
from pathlib import Path

eia_page = r'https://www.eia.gov/electricity/data/eia861/'
migration_page = r'https://www.maine.gov/mpuc/regulated-utilities/electricity/choosing-supplier/migration-statistics'

project_root = Path(__file__).parent.parent

raw_data_dir = Path(project_root, 'raw_data')
raw_data_dir.mkdir(exist_ok=True)
process_dir = Path(project_root, 'prepared_data')
process_dir.mkdir(exist_ok=True)

def _get_eia_861_paths(start_year=2012, end_year=date.today().year):
    resp = requests.get(eia_page)
    soup = BeautifulSoup(resp.content, 'html.parser')
    file_tags = soup.find('table').contents[3].find_all('a', {'class': 'ico zip'})
    urls = [urljoin(eia_page, obj.get('href')) for obj in file_tags
            if start_year <= int(obj.get('title')) <= end_year]
    return urls

def download_eia_861(end_year=None):
    target_regex = re.compile(r'Sales_Ult_Cust_\d{4}\.xls')

    files = _get_eia_861_paths(end_year=end_year)

    for file in files:
        file = requests.get(file)
        zip_data = BytesIO(file.content)

        try:
            with ZipFile(zip_data, 'r') as zip_ref:
                files = zip_ref.namelist()
                files_to_extract = [file for file in files if target_regex.search(file)]
                for file_to_extract in files_to_extract:
                    zip_ref.extract(file_to_extract, raw_data_dir)
                    print(f'Extracted {file_to_extract}')
        except Exception as e:
            print(f'Error with ZIP for {file}: {e}')


def process_and_merge_861():
    files = glob.glob(os.path.join(raw_data_dir, 'Sales_*.xls*'))
    col_range = 'A:R'
    skiprows = 2
    tiers = ['RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL']
    measures = ['REVENUE', 'SALES_MWH', 'CUSTOMERS']

    # Set up column names
    tier_cols = [f'{tier}_{measure}' for tier in tiers for measure in measures]
    all_columns = ['YEAR', 'UTILITY_NUMBER', 'UTILITY_NAME', 'PART', 'SERVICE_TYPE', 'DATA_TYPE', 'STATE', 'OWNERSHIP', 'BA_CODE'] + tier_cols

    dfs = []

    for file in files:
        print(f'Reading in {file}')

        if '2019' in file:
            col_range = 'A:S'
        else:
            col_range = 'A:R'

        df = pd.read_excel(file, skiprows=skiprows, usecols=col_range)

        # BA_CODE does not exist in 2012 file, add this
        # Drop last column incorrectly indexed from A:K
        if '2012' in file:
            df.insert(loc=8, column='BA_CODE', value=np.nan)
            df = df.drop(df.columns[-1], axis=1)

        if '2019' in file:
            df = df.drop('Short Form', axis=1)

        df.columns = all_columns

        dfs.append(df)

    df_merged = pd.concat(dfs, axis=0).reset_index(drop=True)

    # Remove erroneous footer rows
    df_merged = df_merged[df_merged['YEAR'].apply(lambda x: isinstance(x, int))]

    dfs = []

    for tier in tiers:
        ref_list = tiers.copy()
        ref_list.remove(tier)

        exclusion = '|'.join(ref_list)
        exclude_regex = f'^(?!{exclusion})'

        df = df_merged.filter(regex=exclude_regex).assign(CUSTOMER_TYPE=tier)
        df.columns = [col.replace(f'{tier}_', '') for col in df.columns]
        dfs.append(df)

    pivot_df = pd.concat(dfs, axis=0).reset_index(drop=True)

    # Correct value to thousands of dollars
    pivot_df['REVENUE'] = pivot_df['REVENUE'] * 1000
    pivot_df['SALES_MWH'] = pivot_df['SALES_MWH'] * 1000
    pivot_df.rename(columns={'SALES_MWH': 'SALES_KWH'}, inplace=True)

    numeric_columns = ['REVENUE', 'SALES_KWH', 'CUSTOMERS']
    pivot_df[numeric_columns] = pivot_df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    print(f'Merged dataframe of {pivot_df.shape}')

    return pivot_df

def get_migration_file_url():
    html_content = requests.get(migration_page).content
    soup = BeautifulSoup(html_content, 'html.parser')
    rel_url = soup.find('a', attrs={'data-entity-type': 'file'}).get('href')
    url = urljoin(migration_page, rel_url)
    return url

def process_customer_migration_files():

    file_url = get_migration_file_url()
    outputs = {}

    resp = requests.get(file_url)
    filepath = os.path.join(raw_data_dir, 'customer_migration_statistics.xls')
    with open(filepath, 'wb') as file:
        file.write(resp.content)

    cust_cols = ['DATE', 'CEP_CUSTOMERS', 'TOTAL_CUSTOMERS']
    load_cols = ['DATE', 'CEP_LOAD_MWH', 'TOTAL_CLASS_LOAD_MWH']

    # Select and transform source data
    col_range = 'A:AK'

    sheet_to_file_map = {
        'Customers': {
            'filename': 'customers_migrated.csv',
            'cols': cust_cols,
            'skiprows': 3
        },
        'Load': {
            'filename': 'load_migrated.csv',
            'cols': load_cols,
            'skiprows': 4
        }
    }

    for sheet, deets in sheet_to_file_map.items():

        excel_bytes = BytesIO(resp.content)
        df = pd.read_excel(excel_bytes, sheet_name=sheet, skiprows=deets.get('skiprows'), usecols=col_range)
        df = df[~df.iloc[:, 1].isna()]

        exclude_regex = f'^(?!%)'
        df = df.filter(regex=exclude_regex)

        district_dict = {
            'BANGOR HYDRO DISTRICT': {
                'SMALL': slice(1, 3),
                'MEDIUM': slice(3, 5)
            },
            'CENTRAL MAINE POWER CO.': {
                'SMALL': slice(9, 11),
                'MEDIUM': slice(11, 13)
            },
            'MAINE PUBLIC SERVICE': {
                'SMALL': slice(17, 19),
                'MEDIUM': slice(19, 21)
            }
        }

        dfs = []

        # Transform each utility partition, adding ref column
        for utility, v in district_dict.items():
            for customer_class, col_slice in v.items():
                df_slice = df.iloc[:, np.r_[0, col_slice]]
                df_slice.columns = deets.get('cols')
                df_slice = df_slice.assign(UTILITY=utility).assign(CUSTOMER_CLASS=customer_class)
                dfs.append(df_slice)

        migration_df = pd.concat(dfs, axis=0)

        outputs[sheet.lower()] = migration_df

    return outputs['customers'], outputs['load']

def get_standard_offer(end_year=2023):
    '''
    Scraping only valid through 2023. Other years follow a much more complex
    table structure.
    :return:
    '''

    url = r'https://www.maine.gov/mpuc/regulated-utilities/electricity/delivery-rates'
    html_content = requests.get(url).content
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')

    def custom_selector(tag):
        if tag.name == "table":
            first_p = tag.find('p')
            if first_p and re.search(r'RESIDENTIAL ELECTRICITY RATES IN MAINE',
                                     first_p.get_text(),
                                     re.IGNORECASE):
                return True
        return False

    target_tables = soup.find_all(custom_selector)

    collector = []

    for table in target_tables:
        find = table.select_one('th:-soup-contains("As of")')
        try:
            match = re.search(r'As of (.*)', find.text)
            start_date = match.group(1).replace('*', '')
        except AttributeError as e:
            continue

        th_elements = table.find_all('th')
        for th in th_elements:
            if re.search(r'(Supply Rate|Standard Offer)', th.get_text(), re.IGNORECASE):
                std_offer_index = th_elements.index(th)

        pattern = re.compile(r'^Central Maine Power|^Emera Maine|^Versant Power', re.IGNORECASE)

        # Find rows where any <td> matches the pattern
        rows = [
            tr for tr in table.find_all('tr')
            if any(re.search(pattern, td.get_text()) for td in tr.find_all('td'))
        ]

        # Print the matching rows
        for row in rows:
            td_elements = row.select('td')
            collector.append({
                'start_date': start_date,
                'utility': td_elements[0].text.strip(),
                'std_offer_rate': re.match(r'\d+.\d{1}', td_elements[std_offer_index].text.strip()).group()
            })

    std_df = pd.DataFrame(collector)

    std_df['start_date'] = pd.to_datetime(std_df['start_date'])
    std_df['std_offer_rate'] = pd.to_numeric(std_df['std_offer_rate'])/100

    return std_df[std_df['start_date'].dt.year <= end_year]