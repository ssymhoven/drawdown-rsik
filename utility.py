from datetime import datetime
from typing import Dict

import pandas as pd

import os
import win32com.client as win32


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


def calc_sector_diff(us: pd.DataFrame, eu: pd.DataFrame) -> pd.DataFrame:
    common_columns = us.columns.intersection(eu.columns)
    common_index = us.index.intersection(eu.index)

    diff = pd.DataFrame(index=common_index, columns=common_columns)

    for col in common_columns:
        for idx in common_index:
            diff.at[idx, col] = eu.at[idx, col] - us.at[idx, col]

    last_row_diff = eu.loc[eu.index[-1]] - us.loc[us.index[-1]]
    name = f"{eu.index[-1]} - {us.index[-1]}"
    diff = pd.concat([diff, pd.DataFrame([last_row_diff.values],
                                         columns=common_columns,
                                         index=[name])])
    diff.index.name = 'GICS'
    return diff


def calc_universe_rel_performance_vs_sector(universe: pd.DataFrame, sector: pd.DataFrame) -> pd.DataFrame:
    sector_mapping = sector.index.to_series().str.extract(r'(\d+)\s*(.*)')
    sector_mapping.columns = ['Sector_Number', 'Cleaned_Sector']
    sector_mapping['Full_Sector'] = sector.index
    sector_mapping_dict = sector_mapping.set_index('Cleaned_Sector')['Full_Sector'].to_dict()

    universe['Sector'] = universe['Sector'].map(sector_mapping_dict)

    def calculate_difference(row, sector):
        sector_row = sector.loc[row['Sector']]

        for time_frame in ['1D', '5D', '1MO', 'YTD']:
            row[f'{time_frame} vs. Sector'] = row[time_frame] - sector_row[time_frame]

        return row

    universe = universe.apply(
        lambda row: calculate_difference(row, sector), axis=1
    )

    return universe


def calc_position_rel_performance_vs_sector(positions: pd.DataFrame, us: pd.DataFrame, eu: pd.DataFrame) -> pd.DataFrame:
    def calculate_difference(row, benchmark_df):
        if row['Sector'] and row['Region'] in ['NORTH AMERICA', 'EU']:
            benchmark_row = benchmark_df.loc[row['Sector']]

            for time_frame in ['1D', '5D', '1MO', 'YTD']:
                row[f'{time_frame} vs. Sector'] = row[time_frame] - benchmark_row[time_frame]
        else:
            for time_frame in ['1D', '5D', '1MO', 'YTD']:
                row[f'{time_frame} vs. Sector'] = 0

        return row

    positions = positions.apply(
        lambda row: calculate_difference(row, eu if row['Region'] == 'EU' else us), axis=1
    )

    return positions


def group_funds(positions: pd.DataFrame) -> pd.DataFrame:
    positions.reset_index(inplace=True)

    positions = positions.groupby('Position Name').agg({
        '1D': 'first',
        '5D': 'first',
        '1MO': 'first',
        'YTD': 'first',
        'Δ 200D Mvag': 'first',
        'Δ 52 Week High': 'first',
        'Last Price': 'first',
        'AEQ': 'mean',
        '% since AEQ': 'mean'
    })

    return positions


def write_mail(positioning_data: Dict, futures_data: Dict, risk_data: Dict, third_party_data: Dict, allocation_data: Dict):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)

    mail.Subject = "Daily Briefing"

    mail.Recipients.Add("pm-aktien")
    mail.Recipients.Add("amstatuser@donner-reuschel.lu")
    mail.Recipients.Add("jan.sandermann@donner-reuschel.de")

    def inplace_chart(image_path: str):
        image_path = os.path.abspath(image_path)
        attachment = mail.Attachments.Add(Source=image_path)
        cid = os.path.basename(image_path)
        attachment.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001F", cid)
        return cid

    region_sector_text = '<h1>Regionen & Sektoren</h1>'
    for key, image_path in positioning_data.items():
        cid = inplace_chart(image_path)
        region_sector_text += f'<h3>{key}</h3><img src="cid:{cid}">'

    allocation_text = '<h1>Aktuelle Allokation</h1>'
    for key, image_path in allocation_data.items():
        cid = inplace_chart(image_path)
        allocation_text += f'<h3>{key}</h3><img src="cid:{cid}">'

    if 'futures' in futures_data.keys():
        futures_text = f"""<h1>Aktuelle Future Positionen</h1>
           <img src="cid:{inplace_chart(image_path=futures_data.get('futures'))}">"""
    else:
        futures_text = "Aktuell keine aktiven Future Positionen."

    risk_text = '<h1>Risikomanagement</h1>'
    for key, image_path in risk_data.items():
        cid = inplace_chart(image_path)
        risk_text += f'<h3>{key}</h3><img src="cid:{cid}">'

    mail.HTMLBody = f"""
    <html>
      <head></head>
      <body>
        <p>Guten Morgen, <br><br>
            {region_sector_text}
            {allocation_text}
            <h1>Drawdown</h1>
            <img src="cid:{inplace_chart(futures_data.get('drawdown'))}">
            {futures_text}
            {risk_text}
            <h1>Drittprodukte & Fonds</h1>
            <h3>VV-Flex</h3>
            <img src="cid:{inplace_chart(third_party_data.get('flex'))}">
            
            <h3>VV-ESG</h3>
            <img src="cid:{inplace_chart(third_party_data.get('esg'))}">
            
            <h3>D&R Strategie - Select</h3>
            <img src="cid:{inplace_chart(third_party_data.get('strategie-select'))}">
            
            <h3>D&R Premium Select</h3>
            <img src="cid:{inplace_chart(third_party_data.get('premium-select'))}">
            
            <br><br>
            Liebe Grüße
            
        </p>
      </body>
    </html>
    """

    mail.Recipients.ResolveAll()
    mail.Display(True)

