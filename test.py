import re

import pandas as pd
from dateutil.relativedelta import relativedelta

from utility import get_future_positions


def extract_date(asset_name):
    match = re.search(r'([A-Za-z]+)(\d{2})$', asset_name.strip())
    if match:
        month = match.group(1)
        year = '20' + match.group(2)
        return pd.to_datetime(f'{month} {year}', format='%b %Y')
    return None


if __name__ == '__main__':
    futures = get_future_positions(account_id='17154503', position_name='EURO STOXX 50     Sep24')
    trade_dates_multiple_assets = futures.groupby('Trade Date')['asset_name'].nunique()
    trade_dates_multiple_assets = trade_dates_multiple_assets[trade_dates_multiple_assets > 1].index
    filtered_df = futures[futures['Trade Date'].isin(trade_dates_multiple_assets)]
    asset_names_to_keep = filtered_df['asset_name'].unique()
    filtered_df = futures[futures['asset_name'].isin(asset_names_to_keep)]

    last_asset_name = filtered_df.iloc[-1]['asset_name']
    last_date = extract_date(last_asset_name)

    filtered_rows = []
    current_date = last_date

    for index, row in filtered_df[::-1].iterrows():
        if row['asset_name'] == last_asset_name:
            filtered_rows.append(row)
        else:
            asset_date = extract_date(row['asset_name'])
            if asset_date == current_date - relativedelta(months=3):
                filtered_rows.append(row)
                current_date -= relativedelta(months=3)
                last_asset_name = row['asset_name']
            else:
                break

    final_filtered_df = pd.DataFrame(filtered_rows[::-1])

    print(final_filtered_df)

