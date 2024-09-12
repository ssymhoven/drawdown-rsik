import pandas as pd
from source_engine.opus_source import OpusSource

from utility import calc_universe_rel_performance_vs_sector

opus = OpusSource()


mandate = {
    'D&R Aktien': '17154631',
    'D&R Aktien Nachhaltigkeit': '79939969',
    'D&R Aktien Strategie': '399443',
    'D&R Premium Select': '93708903'
}

futures = f"""
    SELECT
        accountsegments.name, 
        accountsegments.nav,
        accountsegments.account_id,
        reportings.report_date, 
        positions.name as position_name,
        positions.average_entry_quote,
        positions.volume,
        positions.position_type,
        positions.underlying_name,
        positions.price_per_point,
        positions.last_xrate_quantity,
        positions.total_exposure
    FROM
        reportings
            JOIN
        accountsegments ON (accountsegments.reporting_uuid = reportings.uuid)
            JOIN
        positions ON (reportings.uuid = positions.reporting_uuid)
    WHERE
            positions.account_segment_id = accountsegments.accountsegment_id
            AND reportings.newest = 1
            AND reportings.report = 'positions'
            AND positions.asset_class = 'FUTURE'
            AND positions.dr_class_level_1 = 'EQUITY'
            AND accountsegments.accountsegment_id in ({', '.join(mandate.values())})
            AND reportings.report_date = (SELECT
                                            MAX(report_date)
                                          FROM
                                            reportings)
"""

stocks = f"""
    SELECT
        accountsegment_id,
        account_id,
        accountsegments.name as Name, 
        reportings.report_date, 
        positions.name as 'Position Name',
        positions.isin as ISIN,
        positions.bloomberg_query as Query,
        positions.average_entry_quote as AEQ,
        positions.average_entry_xrate as AEX,
        positions.currency as Crncy,
        positions.last_quote,
        positions.volume as Volume,
        positions.gics_industry_sector as Sector,
        positions.dr_class_level_2 as 'Region'
    FROM
        reportings
            JOIN
        accountsegments ON (accountsegments.reporting_uuid = reportings.uuid)
            JOIN
        positions ON (reportings.uuid = positions.reporting_uuid)
    WHERE
            positions.account_segment_id = accountsegments.accountsegment_id
            AND reportings.newest = 1
            AND reportings.report = 'positions'
            AND positions.asset_class = 'STOCK'
            AND accountsegments.accountsegment_id in ({', '.join(mandate.values())})
            AND reportings.report_date = (SELECT
                                            MAX(report_date)
                                          FROM
                                            reportings)
"""

third_party = """
    SELECT
        accountsegments.name as Name, 
        accountsegments.account_id,
        reportings.report_date, 
        positions.bloomberg_query as Query,
        positions.name as 'Position Name',
        positions.average_entry_quote as AEQ,
        positions.volume as Volume,
        positions.last_xrate_quantity as AEX
    FROM
        reportings
            JOIN
        accountsegments ON (accountsegments.reporting_uuid = reportings.uuid)
            JOIN
        positions ON (reportings.uuid = positions.reporting_uuid)
    WHERE
            positions.account_segment_id = accountsegments.accountsegment_id
            AND reportings.newest = 1
            AND reportings.report = 'positions'
            AND positions.asset_class in ('FUND_CLASS', 'CERTIFICATE')
            AND (accountsegments.name LIKE "%VV-ESG%" OR accountsegments.name LIKE "%VV-Flex%" OR accountsegments.name LIKE "%Strategie - Select" OR accountsegments.name LIKE "%Premium Select%")
            AND reportings.report_date = (SELECT
                                            MAX(report_date)
                                          FROM
                                            reportings)
"""


def get_account_futures() -> pd.DataFrame:
    df = opus.read_sql(query=futures)
    df.set_index(['name', 'position_name'], inplace=True)
    return df


def get_positions() -> pd.DataFrame:
    df = opus.read_sql(query=stocks)
    df['AEQ'] = df['AEQ'] * df['AEX']

    positions = pd.merge(df, single_stocks[['bloomberg_query', 'isin', 'Last Price', '1D', '5D', '1MO', 'YTD', 'Δ 200D Mvag', 'Δ 52 Week High']],
                         left_on='ISIN', right_on='isin',
                         how='left')

    # Use DWH Last Quote if BBG Last Price not available
    for col in ['Last Price', 'AEQ', '1D', '5D', '1MO', 'YTD', 'Δ 200D Mvag', 'Δ 52 Week High']:
        positions[col] = pd.to_numeric(positions[col], errors='coerce').fillna(0)

    positions['Last Price'] = positions.apply(
        lambda row: row['last_quote'] if row['Last Price'] == 0 else row['Last Price'],
        axis=1
    )

    positions.set_index(['Name', 'Position Name'], inplace=True)
    positions['% since AEQ'] = pd.to_numeric(((positions['Last Price'] - positions['AEQ']) / positions['AEQ']) * 100, errors='coerce')
    return positions


def get_futures_data() -> pd.DataFrame:
    data = pd.read_excel('data.xlsx', sheet_name="Futures", header=0, skiprows=[1, 2], index_col=0)
    data.index = pd.to_datetime(data.index, errors='coerce')
    data = data.sort_index()

    return data


def get_universe_data(universe: str) -> pd.DataFrame:
    universe = pd.read_excel('data.xlsx', sheet_name=universe, header=0)
    universe.fillna(0, inplace=True)
    universe = universe.rename(
        columns={'name': 'Name', 'gics_sector_name': 'Sector', 'CURRENT_TRR_1D': '1D',
                 'CURRENT_TRR_5D': '5D', 'CURRENT_TRR_1MO': '1MO', 'CURRENT_TRR_YTD': 'YTD',
                 'CHG_PCT_MOV_AVG_200D': 'Δ 200D Mvag', 'CHG_PCT_HIGH_52WEEK': 'Δ 52 Week High'})
    universe = universe[universe['Sector'] != 0]
    return universe


def get_regions_data() -> pd.DataFrame:
    regions = pd.read_excel('data.xlsx', sheet_name="Regions", header=0, index_col=1)
    regions.fillna(0, inplace=True)
    regions.drop("Index", axis=1, inplace=True)
    regions = regions.rename(
        columns={'name': 'Name', 'CURRENT_TRR_1D': '1D',
                 'CURRENT_TRR_5D': '5D', 'CURRENT_TRR_1MO': '1MO', 'CURRENT_TRR_YTD': 'YTD',
                 'CHG_PCT_MOV_AVG_200D': 'Δ 200D Mvag', 'CHG_PCT_HIGH_52WEEK': 'Δ 52 Week High'})
    return regions


def get_third_party_products() -> pd.DataFrame:
    df = opus.read_sql(query=third_party)
    df['AEQ'] = df['AEQ'] * df['AEX']

    df = pd.merge(df, funds[['bloomberg_query', 'Last Price', '1D', '5D', '1MO', 'YTD', 'Δ 200D Mvag', 'Δ 52 Week High']],
                  left_on='Query', right_on='bloomberg_query',
                  how='left')

    df.set_index(['Name', 'Position Name'], inplace=True)
    df['% since AEQ'] = pd.to_numeric(((df['Last Price'] - df['AEQ']) / df['AEQ']) * 100,
                                      errors='coerce')

    return df


def get_stocks_data() -> pd.DataFrame:
    df = pd.read_excel('data.xlsx', sheet_name='Stocks', header=0)
    df.fillna(0, inplace=True)
    df = df.rename(columns={'CURRENT_TRR_1D': '1D', 'CURRENT_TRR_5D': '5D', 'CURRENT_TRR_1MO': '1MO', 'CURRENT_TRR_YTD': 'YTD',
                            'CHG_PCT_MOV_AVG_200D': 'Δ 200D Mvag', 'CHG_PCT_HIGH_52WEEK': 'Δ 52 Week High'})
    return df


def get_funds_data() -> pd.DataFrame:
    df = pd.read_excel('data.xlsx', sheet_name='Funds', header=0)
    df.fillna(0, inplace=True)
    df = df.rename(
        columns={'CURRENT_TRR_1D': '1D', 'CURRENT_TRR_5D': '5D', 'CURRENT_TRR_1MO': '1MO', 'CURRENT_TRR_YTD': 'YTD',
                 'CHG_PCT_MOV_AVG_200D': 'Δ 200D Mvag', 'CHG_PCT_HIGH_52WEEK': 'Δ 52 Week High'})
    return df


def get_us_sector_data() -> pd.DataFrame:
    df = pd.read_excel('data.xlsx', sheet_name='US Sector', header=0, index_col=0)
    df.drop('Query', inplace=True, axis=1)
    df.fillna(0, inplace=True)
    df = df.rename(columns={'CURRENT_TRR_1D': '1D', 'CURRENT_TRR_5D': '5D', 'CURRENT_TRR_1MO': '1MO', 'CURRENT_TRR_YTD': 'YTD',
                            'CHG_PCT_MOV_AVG_200D': 'Δ 200D Mvag', 'CHG_PCT_HIGH_52WEEK': 'Δ 52 Week High'})
    return df


def get_eu_sector_data() -> pd.DataFrame:
    df = pd.read_excel('data.xlsx', sheet_name='EU Sector', header=0)
    df.drop('Query', inplace=True, axis=1)
    df.fillna(0, inplace=True)
    df = df.rename(columns={'CURRENT_TRR_1D': '1D', 'CURRENT_TRR_5D': '5D', 'CURRENT_TRR_1MO': '1MO', 'CURRENT_TRR_YTD': 'YTD',
                            'CHG_PCT_MOV_AVG_200D': 'Δ 200D Mvag', 'CHG_PCT_HIGH_52WEEK': 'Δ 52 Week High'})

    def calculate_weighted_trrs(group):
        weight = group['CUR_MKT_CAP'] / group['CUR_MKT_CAP'].sum()
        d = {'1D': (group['1D'] * weight).sum(),
             '5D': (group['5D'] * weight).sum(),
             '1MO': (group['1MO'] * weight).sum(),
             'YTD': (group['YTD'] * weight).sum(),
             'Δ 200D Mvag': (group['Δ 200D Mvag'] * weight).sum(),
             'Δ 52 Week High': (group['Δ 52 Week High'] * weight).sum(),
             }
        return pd.Series(d)

    df = df.groupby('GICS').apply(calculate_weighted_trrs)
    return df


def calculate_quantiles(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    quantiles = {}
    for column in columns:
        quantiles[column] = {
            '5th Quantile': df[column].quantile(0.05),
            '95th Quantile': df[column].quantile(0.95)
        }
    df = pd.DataFrame(quantiles).transpose()
    df = df.apply(lambda x: round(x * 2) / 2)
    return df


def filter_positions(positions: pd.DataFrame, sector: str = None) -> (pd.DataFrame, pd.DataFrame):
    def get_quantiles(row):
        if sector:
            return us_quantiles if sector == 'US' else eu_quantiles
        else:
            return us_quantiles if row['Region'] == 'US' else eu_quantiles

    positives = []
    negatives = []

    for _, row in positions.iterrows():
        quantiles = get_quantiles(row)
        if sector:
            pos_condition = (
                    ((row['1D vs. Sector'] > quantiles.loc['1D vs. Sector', '95th Quantile']) |
                    (row['5D vs. Sector'] > quantiles.loc['5D vs. Sector', '95th Quantile']) |
                    (row['1MO vs. Sector'] > quantiles.loc['1MO vs. Sector', '95th Quantile']) |
                    (row['YTD vs. Sector'] > quantiles.loc['YTD vs. Sector', '95th Quantile'])) &
                    ((row['1D'] > quantiles.loc['1D', '95th Quantile']) |
                    (row['5D'] > quantiles.loc['5D', '95th Quantile']) |
                    (row['1MO'] > quantiles.loc['1MO', '95th Quantile']) |
                    (row['YTD'] > quantiles.loc['YTD', '95th Quantile']))
            )
            neg_condition = (
                    ((row['1D vs. Sector'] < quantiles.loc['1D vs. Sector', '5th Quantile']) |
                    (row['5D vs. Sector'] < quantiles.loc['5D vs. Sector', '5th Quantile']) |
                    (row['1MO vs. Sector'] < quantiles.loc['1MO vs. Sector', '5th Quantile']) |
                    (row['YTD vs. Sector'] < quantiles.loc['YTD vs. Sector', '5th Quantile'])) &
                    ((row['1D'] < quantiles.loc['1D', '5th Quantile']) |
                    (row['5D'] < quantiles.loc['5D', '5th Quantile']) |
                    (row['1MO'] < quantiles.loc['1MO', '5th Quantile']) |
                    (row['YTD'] < quantiles.loc['YTD', '5th Quantile']))
            )
        else:
            pos_condition = (
                    (row['1D vs. Sector'] > quantiles.loc['1D vs. Sector', '95th Quantile']) |
                    (row['5D vs. Sector'] > quantiles.loc['5D vs. Sector', '95th Quantile']) |
                    (row['1MO vs. Sector'] > quantiles.loc['1MO vs. Sector', '95th Quantile'])
            )
            neg_condition = (
                    ((row['1D vs. Sector'] < quantiles.loc['1D vs. Sector', '5th Quantile']) |
                    (row['5D vs. Sector'] < quantiles.loc['5D vs. Sector', '5th Quantile']) |
                    (row['1MO vs. Sector'] < quantiles.loc['1MO vs. Sector', '5th Quantile']) |
                    (row['YTD vs. Sector'] < quantiles.loc['YTD vs. Sector', '5th Quantile'])) |
                    (row['% since AEQ'] < -5) #| (row['Δ 200D Mvag'] < -10) | (row['Δ 52 Week High'] < -15)
            )

        if pos_condition:
            positives.append(row)
        if neg_condition:
            negatives.append(row)

    positive_positions = pd.DataFrame(positives)
    negative_positions = pd.DataFrame(negatives)

    return positive_positions, negative_positions


single_stocks = get_stocks_data()
funds = get_funds_data()
regions = get_regions_data()

third_party_products = get_third_party_products()

us_universe = get_universe_data(universe="S&P 500")
us_sector = get_us_sector_data()

eu_universe = get_universe_data(universe="STOXX Europe 600")
eu_sector = get_eu_sector_data()

us = calc_universe_rel_performance_vs_sector(universe=us_universe, sector=us_sector)
eu = calc_universe_rel_performance_vs_sector(universe=eu_universe, sector=eu_sector)

columns_to_analyze = ['1D', '5D', '1MO', 'YTD', '1D vs. Sector', '5D vs. Sector', '1MO vs. Sector', 'YTD vs. Sector']

us_quantiles = calculate_quantiles(us, columns_to_analyze)
eu_quantiles = calculate_quantiles(eu, columns_to_analyze)


us_metrics_positions = f"""
   1D vs. Sector < <b>{us_quantiles.loc['1D vs. Sector', '5th Quantile']}%</b>, oder<br>
   5D vs. Sector < <b>{us_quantiles.loc['5D vs. Sector', '5th Quantile']}%</b>, oder<br>
   1MO vs. Sector < <b>{us_quantiles.loc['1MO vs. Sector', '5th Quantile']}%</b>, oder<br>
   YTD vs. Sector < <b>{us_quantiles.loc['YTD vs. Sector', '5th Quantile']}%
"""

eu_metrics_positions = f"""
   1D vs. Sector < <b>{eu_quantiles.loc['1D vs. Sector', '5th Quantile']}%</b>, oder<br>
   5D vs. Sector < <b>{eu_quantiles.loc['5D vs. Sector', '5th Quantile']}%</b>, oder<br>
   1MO vs. Sector < <b>{eu_quantiles.loc['1MO vs. Sector', '5th Quantile']}%</b>, oder<br>
   YTD vs. Sector < <b>{eu_quantiles.loc['YTD vs. Sector', '5th Quantile']}%
"""

print(us_metrics_positions)
print(eu_metrics_positions)
