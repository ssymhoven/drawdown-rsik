import pandas as pd
from pandas import DataFrame
from source_engine.opus_source import OpusSource

mandate = {
    'D&R Aktien': '17154631',
    'D&R Aktien Nachhaltigkeit': '79939969',
    'D&R Aktien Strategie': '399443'
}

query = f"""
    SELECT
        accountsegments.name, 
        reportings.report_date, 
        positions.name as position_name,
        positions.average_entry_quote,
        positions.volume,
        positions.position_type,
        positions.underlying_name
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

opus = OpusSource()


def get_account_futures() -> pd.DataFrame:
    df = opus.read_sql(query=query)
    df.set_index(['name', 'position_name'], inplace=True)
    df['average_entry_quote'] = round(df['average_entry_quote'], 2)
    return df


def get_futures_data() -> dict[str, DataFrame]:
    data = pd.read_excel('futures.xlsx', sheet_name=None, header=1, index_col=0)

    for sheet_name, df in data.items():
        df['#PX_LAST'] = pd.to_numeric(df['#PX_LAST'], errors='coerce')
        df['50D_SMAVG'] = df['#PX_LAST'].rolling(window=50).mean()

    return data
