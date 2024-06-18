from datetime import datetime
from typing import Dict

import pandas as pd
from pandas import DataFrame
from source_engine.opus_source import OpusSource
import os
import win32com.client as win32

mandate = {
    'D&R Aktien': '17154631',
    'D&R Aktien Nachhaltigkeit': '79939969',
    'D&R Aktien Strategie': '399443'
}

query = f"""
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


confirmations_query = """
    SELECT
        trade_date as 'Trade Date',
        valuta_date as 'Valuta Date',
        order_id,
        confirmation_status as 'Status',
        order_action as 'Action',
        volume_quantity as 'Volume',
        price_quantity as 'Price'
    FROM 
        confirmations
    WHERE 
        account_id = '{account_id}'
        AND asset_class = 'FUTURE' 
        AND asset_name = '{position_name}';
"""

opus = OpusSource()


def get_account_futures() -> pd.DataFrame:
    df = opus.read_sql(query=query)
    df.set_index(['name', 'position_name'], inplace=True)
    return df


def get_future_positions(account_id: str, position_name: str) -> pd.DataFrame:
    df = opus.read_sql(query=confirmations_query.format(account_id=account_id, position_name=position_name))
    df.set_index(['order_id'], inplace=True)
    return df


def get_futures_data() -> dict[str, DataFrame]:
    data = pd.read_excel('futures.xlsx', sheet_name=None, header=1, index_col=0)

    for sheet_name, df in data.items():
        df['#PX_LAST'] = pd.to_numeric(df['#PX_LAST'], errors='coerce')
        df['50D_SMAVG'] = df['#PX_LAST'].rolling(window=50).mean()

    return data


def momentum_table(data: pd.DataFrame) -> pd.DataFrame:
    periods = [1, 2, 3, 5, 10, 20, 30]
    metrics = {}

    last_px = data['#PX_LAST'].iloc[-1]

    for period in periods:
        if len(data) > period:
            momentum = (last_px - data['#PX_LAST'].iloc[-(period + 1)]) / data['#PX_LAST'].iloc[-(period + 1)]
            metrics[f'{period}D'] = momentum

    year_start = datetime(data.index[-1].year, 1, 1)
    if year_start in data.index:
        momentum_ytd = (last_px - data.loc[year_start, '#PX_LAST']) / data.loc[year_start, '#PX_LAST']
    else:
        first_date = data[data.index >= year_start].iloc[0]
        momentum_ytd = (last_px - first_date['#PX_LAST']) / first_date['#PX_LAST']

    metrics['YTD'] = momentum_ytd
    momentum_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
    momentum_df.set_index('Metric', inplace=True)

    return momentum_df


def escape_latex(s):
    return s.replace('&', r'\&') \
            .replace('%', r'\%') \
            .replace('$', r'\$') \
            .replace('#', r'\#') \
            .replace('_', r'\_') \
            .replace('{', r'\{') \
            .replace('}', r'\}') \
            .replace('~', r'\textasciitilde{}') \
            .replace('^', r'\textasciicircum{}')


def position_details(data: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    last_px = data['#PX_LAST'].iloc[-1]
    position_type = row['position_type']
    avg_entry_quote = row['average_entry_quote']

    metrics = {}

    if position_type == 'LONG':
        profit_loss_percentage = (last_px - avg_entry_quote) / avg_entry_quote * 100
    elif position_type == 'SHORT':
        profit_loss_percentage = (avg_entry_quote - last_px) / avg_entry_quote * 100
    else:
        raise ValueError("Unsupported position type: " + position_type)

    metrics['AEQ'] = avg_entry_quote
    metrics['% since AEQ'] = profit_loss_percentage
    metrics['Volume'] = row['volume']
    metrics['Type'] = row['position_type']
    metrics['P&L'] = ((last_px - avg_entry_quote) * row['price_per_point'] * row['volume'] * row['last_xrate_quantity']
                      * (-1 if row['position_type'] == "SHORT" else 1))

    metrics['Exposure'] = ((row['total_exposure'] * row['last_xrate_quantity']) / row['nav']) * 100

    details_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
    details_df.set_index('Metric', inplace=True)

    return details_df


def positions_overview(data: Dict[str, pd.DataFrame], positions: pd.DataFrame) -> pd.DataFrame:
    all_metrics = []

    for idx, row in positions.iterrows():
        name, positions_name = idx
        underlying_name = row['underlying_name']

        # BUG
        if underlying_name == 'Deutsche Boerse AG German Stock Index DAX':
            underlying_name = 'Deutsche Boerse AG German Stock'

        if underlying_name not in data:
            raise ValueError(f"Underlying data '{underlying_name}' not found in provided data dictionary.")

        underlying_data = data[underlying_name]
        last_px = underlying_data['#PX_LAST'].iloc[-1]

        position_type = row['position_type']
        avg_entry_quote = row['average_entry_quote']

        if position_type == 'LONG':
            profit_loss_percentage = (last_px - avg_entry_quote) / avg_entry_quote * 100
        elif position_type == 'SHORT':
            profit_loss_percentage = (avg_entry_quote - last_px) / avg_entry_quote * 100
        else:
            raise ValueError("Unsupported position type: " + position_type)

        pnl = ((last_px - avg_entry_quote) * row['price_per_point'] * row['volume'] *
               row['last_xrate_quantity'] * (-1 if position_type == "SHORT" else 1))

        exposure = ((row['total_exposure'] * row['last_xrate_quantity']) / row['nav']) * 100

        metrics = {
            'Name': name,
            'Position Name': positions_name,
            'AEQ': avg_entry_quote,
            '% since AEQ': profit_loss_percentage,
            'Volume': row['volume'],
            'Type': position_type,
            'P&L': pnl,
            'Exposure': exposure
        }

        all_metrics.append(metrics)

    metrics_df = pd.DataFrame(all_metrics)

    return metrics_df


def drawdown(series: pd.Series):
    previous_peaks = series.cummax()
    drawdowns = (series - previous_peaks) / previous_peaks
    return pd.DataFrame({
        "Peaks": previous_peaks,
        "Drawdowns": drawdowns
    })


def drawup(series: pd.Series):
    previous_lows = series.cummin()
    drawups = (series - previous_lows) / previous_lows
    return pd.DataFrame({
        "Lows": previous_lows,
        "Drawups": drawups
    })


def cleanup_aux_files():
    files = os.listdir("output")
    for file in files:
        if (file.endswith(".aux") or file.endswith(".log") or file.endswith(".out") or file.endswith(".toc")
                or file.endswith(".snm") or file.endswith(".tex")):
            os.remove(os.path.join("output", file))


def write_mail(data: Dict):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)

    mail.Subject = "Daily Reporting - Drawdown & Future Positionen"

    mail.Recipients.Add("pm-aktien")
    mail.Recipients.Add("amstatuser@donner-reuschel.lu")
    mail.Recipients.Add("jan.sandermann@donner-reuschel.de")
    mail.Recipients.Add("sadettin.yildiz@donner-reuschel.de").Type = 2

    def inplace_chart(key: str):
        image_path = data[key]
        image_path = os.path.abspath(image_path)
        attachment = mail.Attachments.Add(Source=image_path)
        attachment.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001F", key)
        return key

    if 'positions' in data.keys():
        positions_text = f"""Außerdem die <b>aktuellen Future Positionen</b> mit Valuta <b>{datetime.today().strftime('%d.%m.%Y')}</b> über alle Fonds:<br><br>
           <img src="cid:{inplace_chart(key='positions')}"><br><br>"""
    else:
        positions_text = "Aktuell keine aktiven Future Postionen.<br><br>"

    mail.HTMLBody = f"""
    <html>
      <head></head>
      <body>
        <p>Hi zusammen, <br><br>
            
            die Kurse der anhängenden Charts sind vom <b>{datetime.now().strftime('%d.%m.%Y %H:%M')}</b>.<br><br>
           <b>Drawdown</b> wichtiger Indizes Futures:<br><br>
           <img src="cid:{inplace_chart(key='drawdown')}"><br><br>
           {positions_text}
           Im Anhang findet ihr zu jedem Fond eine detaillierte Übersicht der einzelnen Future Positionen, sowie eine
           detaillierte Übersicht aller Futures.
           <br><br>
           Liebe Grüße
        </p>
      </body>
    </html>
    """

    for file_path in data.get('files', []):
        if os.path.exists(file_path):
            file_path = os.path.abspath(file_path)
            mail.Attachments.Add(Source=file_path)

    mail.Recipients.ResolveAll()
    mail.Display(True)

