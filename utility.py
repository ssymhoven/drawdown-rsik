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

opus = OpusSource()


def get_account_futures() -> pd.DataFrame:
    df = opus.read_sql(query=query)
    df.set_index(['name', 'position_name'], inplace=True)
    return df


def get_futures_data() -> pd.DataFrame:
    data = pd.read_excel('data.xlsx', sheet_name="Futures", header=0, skiprows=[1, 2], index_col=0)
    data.index = pd.to_datetime(data.index, errors='coerce')
    data = data.sort_index()

    return data


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


def positions_overview(data: pd.DataFrame, positions: pd.DataFrame) -> pd.DataFrame:
    all_metrics = []

    for idx, row in positions.iterrows():
        name, positions_name = idx
        underlying_name = row['underlying_name']

        # BUG
        if underlying_name == 'Deutsche Boerse AG German Stock Index DAX':
            underlying_name = 'Deutsche Boerse AG German Stock'

        if underlying_name not in data.columns:
            raise ValueError(f"Underlying data '{underlying_name}' not found in provided data dictionary.")

        last_px = data[underlying_name].iloc[-1]

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


def cleanup_aux_files():
    files = os.listdir("output")
    for file in files:
        if (file.endswith(".aux") or file.endswith(".log") or file.endswith(".out") or file.endswith(".toc")
                or file.endswith(".snm") or file.endswith(".tex")):
            os.remove(os.path.join("output", file))


def write_mail(data: Dict):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)

    mail.Subject = "Daily Reporting - Positionierung, Drawdown & Risikomanagement"

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
        positions_text = f"""<h1>Aktuelle Future Positionen</h1><br><br>
           <img src="cid:{inplace_chart(key='positions')}"><br><br>"""
    else:
        positions_text = "Aktuell keine aktiven Future Postionen.<br><br>"

    mail.HTMLBody = f"""
    <html>
      <head></head>
      <body>
        <p>Guten Morgen, <br><br>
            
           <h1>Drawdown</h1>
           <img src="cid:{inplace_chart(key='drawdown')}"><br><br>
           {positions_text}
           <br><br>
           Liebe Grüße
        </p>
      </body>
    </html>
    """

    mail.Recipients.ResolveAll()
    mail.Display(True)

