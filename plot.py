from typing import List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
import dataframe_image as dfi

from utility import drawdown

drawdown_color = '#E91457'


def plot_drawdown_chart(data: pd.Series, underlying_name: str):
    fig, ax = plt.subplots(figsize=(10, 2))

    dd = drawdown(data)

    ax.plot(data.index, dd['Drawdowns'] * 100, label='Drawdown', color=drawdown_color, linestyle='-', linewidth=1.5)

    ax.set_xlabel('Date')
    ax.set_ylabel('%')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_locator(dates.MonthLocator(interval=3))
    ax.xaxis.set_minor_locator(dates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(dates.DateFormatter('%b %Y'))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.yaxis.set_major_locator(ticker.AutoLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.axhline(0, color='grey', linestyle='--', linewidth=0.5)

    current_drawdown = dd['Drawdowns'].iloc[-1] * 100
    ax.text(data.index[-1], current_drawdown, f'{current_drawdown:.2f}%', color=drawdown_color, fontsize=9,
            verticalalignment='top')

    filename = f"output/futures/{underlying_name}_drawdown.png"
    plt.savefig(filename)
    plt.close()

    return filename


def style_positions_with_bars(positions: pd.DataFrame, name: str) -> str:
    columns_to_show = ['Sector', 'AEQ', 'Volume', 'Last Price', '% since AEQ', '1D', '5D', '1MO', 'YTD', 'Δ 200D Mvag',
                       'Δ 52 Week High',
                       '1D vs. Sector', '5D vs. Sector', '1MO vs. Sector', 'YTD vs. Sector']
    positions = positions.copy()[columns_to_show]

    aeq_max_abs_value = positions['% since AEQ'].abs().max()
    trr1d_max_abs_value = positions['1D'].abs().max()
    trr5d_max_abs_value = positions['5D'].abs().max()
    trr1mo_max_abs_value = positions['1MO'].abs().max()
    trr_ytd_max_abs_value = positions['YTD'].abs().max()

    rel_trr1d_max_abs_value = positions['1D vs. Sector'].abs().max()
    rel_trr5d_max_abs_value = positions['5D vs. Sector'].abs().max()
    rel_trr_trr1mo_max_abs_value = positions['1MO vs. Sector'].abs().max()
    rel_trr_ytd_max_abs_value = positions['YTD vs. Sector'].abs().max()

    mvag_max_abs_value = positions['Δ 200D Mvag'].abs().max()
    high_max_abs_value = positions['Δ 52 Week High'].abs().max()

    positions.sort_values('% since AEQ', ascending=False, inplace=True)
    positions.index.name = 'Position Name'

    cm = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"],
                                           N=len(positions) if len(positions) > 3 else 3)

    styled = (
    positions.style.bar(subset='% since AEQ', cmap=cm, align=0, vmax=aeq_max_abs_value, vmin=-aeq_max_abs_value)
    .bar(subset='1D', cmap=cm, align=0, vmax=trr1d_max_abs_value, vmin=-trr1d_max_abs_value)
    .bar(subset='5D', cmap=cm, align=0, vmax=trr5d_max_abs_value, vmin=-trr5d_max_abs_value)
    .bar(subset='1MO', cmap=cm, align=0, vmax=trr1mo_max_abs_value, vmin=-trr1mo_max_abs_value)
    .bar(subset='YTD', cmap=cm, align=0, vmax=trr_ytd_max_abs_value, vmin=-trr_ytd_max_abs_value)
    .bar(subset='1D vs. Sector', cmap=cm, align=0, vmax=rel_trr1d_max_abs_value,
         vmin=-rel_trr1d_max_abs_value)
    .bar(subset='5D vs. Sector', cmap=cm, align=0, vmax=rel_trr5d_max_abs_value, vmin=-rel_trr5d_max_abs_value)
    .bar(subset='1MO vs. Sector', cmap=cm, align=0, vmax=rel_trr_trr1mo_max_abs_value,
         vmin=-rel_trr_trr1mo_max_abs_value)
    .bar(subset='YTD vs. Sector', cmap=cm, align=0, vmax=rel_trr_ytd_max_abs_value, vmin=-rel_trr_ytd_max_abs_value)
    .bar(subset='Δ 200D Mvag', cmap=cm, align=0, vmax=mvag_max_abs_value, vmin=-mvag_max_abs_value)
    .bar(subset='Δ 52 Week High', cmap=cm, align=0, vmax=high_max_abs_value, vmin=-high_max_abs_value)
    .set_table_styles([
        {'selector': 'th.col0',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col0',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'th.col5',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col5',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'th.col9',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col9',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'th.col11',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col11',
         'props': [('border-left', '1px solid black')]},
        {
            'selector': 'th.index_name',
            'props': [('min-width', '250px'), ('white-space', 'nowrap')]
        },
        {
            'selector': 'td.col0',
            'props': [('min-width', '200px'), ('white-space', 'nowrap')]
        }
    ])
    .format({
        'AEQ': "{:,.2f}",
        'Last Price': "{:,.2f}",
        'Volume': "{:,.0f}",
        '% since AEQ': "{:.2f}%",
        '1D': "{:.2f}%",
        '5D': "{:.2f}%",
        '1MO': "{:.2f}%",
        'YTD': "{:.2f}%",
        '1D vs. Sector': "{:.2f}%",
        '5D vs. Sector': "{:.2f}%",
        '1MO vs. Sector': "{:.2f}%",
        'YTD vs. Sector': "{:.2f}%",
        'Δ 200D Mvag': "{:.2f}%",
        'Δ 52 Week High': "{:.2f}%"
    }))

    output_path = f"output/risk/{name.replace(' ', '_').replace('&', '')}_Details.png"
    dfi.export(styled, output_path, table_conversion="selenium")
    return output_path


def style_index_with_bars(index: pd.DataFrame, name: str, hide_index: bool = False, borders: List = None) -> str:
    table_style = []
    for border in borders:
        if isinstance(border, int):
            table_style.append(
                {'selector': f'th.col{border}',
                 'props': [('border-left', '1px solid black')]})
            table_style.append({'selector': f'td.col{border}',
                 'props': [('border-left', '1px solid black')]}
            )
        if isinstance(border, str):
            if border == "last":
                table_style.append(
                    {'selector': 'tr:last-child th, tr:last-child td',
                     'props': [('border-top', '1px solid black')]}
                )

    for col in ['1D', '5D', '1MO', 'YTD', 'Δ 200D Mvag', 'Δ 52 Week High']:
        index[col] = pd.to_numeric(index[col], errors='coerce')

    trr1d_max_abs_value = index['1D'].abs().max()
    trr5d_max_abs_value = index['5D'].abs().max()
    trr1mo_max_abs_value = index['1MO'].abs().max()
    trr_ytd_max_abs_value = index['YTD'].abs().max()
    mvag_max_abs_value = index['Δ 200D Mvag'].abs().max()
    high_max_abs_value = index['Δ 52 Week High'].abs().max()

    cm = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"], N=len(index))
    styled = (
        index.style.bar(subset='1D', cmap=cm, align=0, vmax=trr1d_max_abs_value, vmin=-trr1d_max_abs_value)
        .bar(subset='5D', cmap=cm, align=0, vmax=trr5d_max_abs_value, vmin=-trr5d_max_abs_value)
        .bar(subset='1MO', cmap=cm, align=0, vmax=trr1mo_max_abs_value, vmin=-trr1mo_max_abs_value)
        .bar(subset='YTD', cmap=cm, align=0, vmax=trr_ytd_max_abs_value, vmin=-trr_ytd_max_abs_value)
        .bar(subset='Δ 200D Mvag', cmap=cm, align=0, vmax=mvag_max_abs_value, vmin=-mvag_max_abs_value)
        .bar(subset='Δ 52 Week High', cmap=cm, align=0, vmax=high_max_abs_value, vmin=-high_max_abs_value)
        .set_table_styles(table_style)
        .format({
            '1D': "{:,.2f}",
            '5D': "{:,.2f}",
            '1MO': "{:,.2f}",
            'YTD': "{:,.2f}",
            'Δ 200D Mvag': "{:.2f}%",
            'Δ 52 Week High': "{:.2f}%"
        }))

    if hide_index:
        styled = styled.hide(axis="index")

    output_path = f"output/{name.replace(' ', '_')}_Details.png"
    dfi.export(styled, output_path, table_conversion="selenium")
    return output_path


def style_third_party(positions: pd.DataFrame, name: str) -> str:
    positions = positions.apply(pd.to_numeric, errors='coerce')
    aeq_max_abs_value = positions['% since AEQ'].abs().max()
    trr1d_max_abs_value = positions['1D'].abs().max()
    trr5d_max_abs_value = positions['5D'].abs().max()
    trr1mo_max_abs_value = positions['1MO'].abs().max()
    trr_ytd_max_abs_value = positions['YTD'].abs().max()
    mvag_max_abs_value = positions['Δ 200D Mvag'].abs().max()
    high_max_abs_value = positions['Δ 52 Week High'].abs().max()

    output_path = f"output/third_party/{name}.png"
    cm = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"], N=len(positions))
    positions.sort_values('% since AEQ', ascending=False, inplace=True)

    styled = (
    (((((positions.style.bar(subset='% since AEQ', cmap=cm, align=0, vmax=aeq_max_abs_value, vmin=-aeq_max_abs_value)
         .bar(subset='1D', cmap=cm, align=0, vmax=trr1d_max_abs_value, vmin=-trr1d_max_abs_value))
        .bar(subset='5D', cmap=cm, align=0, vmax=trr5d_max_abs_value, vmin=-trr5d_max_abs_value))
       .bar(subset='1MO', cmap=cm, align=0, vmax=trr1mo_max_abs_value, vmin=-trr1mo_max_abs_value))
      .bar(subset='YTD', cmap=cm, align=0, vmax=trr_ytd_max_abs_value, vmin=-trr_ytd_max_abs_value))
     .bar(subset='Δ 200D Mvag', cmap=cm, align=0, vmax=mvag_max_abs_value, vmin=-mvag_max_abs_value))
    .bar(subset='Δ 52 Week High', cmap=cm, align=0, vmax=high_max_abs_value, vmin=-high_max_abs_value)
    .set_table_styles([
        {'selector': 'th.col0',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col0',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'th.col4',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col4',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'th.col6',
         'props': [('border-left', '1px solid black')]},
        {'selector': 'td.col6',
         'props': [('border-left', '1px solid black')]},
        {
            'selector': 'th.index_name',
            'props': [('min-width', '250px'), ('white-space', 'nowrap')]
        }
    ]).format({
        'AEQ': "{:,.2f}",
        'Last Price': "{:,.2f}",
        '% since AEQ': "{:.2f}%",
        '1D': "{:.2f}%",
        '5D': "{:.2f}%",
        '1MO': "{:.2f}%",
        'YTD': "{:.2f}%",
        'Δ 200D Mvag': "{:.2f}%",
        'Δ 52 Week High': "{:.2f}%"
    }))
    dfi.export(styled, output_path, table_conversion="selenium")
    return output_path
