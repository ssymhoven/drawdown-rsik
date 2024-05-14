import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker

from utility import drawdown, drawup

line_color = '#7EC0C6'
smavg_color = '#124877'
avg_color = '#E91457'
peaks_color = '#FD7100'
drawdown_color = '#E91457'


def plot_future_position_chart(data: pd.DataFrame, account_name: str, underlying_name: str, avg_entry_quote: float,
                               position_type: str, positions: pd.DataFrame) -> str:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                   gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05},
                                   sharex=True)

    ax1.plot(data.index, data['#PX_LAST'], label=f'{underlying_name}', color=line_color)
    ax1.plot(data.index, data['50D_SMAVG'], label=f'50D SMAVG', color=smavg_color)
    ax1.axhline(y=avg_entry_quote, color=avg_color, linestyle='--', linewidth=1,
                label=f'Average Entry Quote')

    ax1.set_ylabel('Level')

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.xaxis.set_major_locator(dates.MonthLocator(interval=3))
    ax1.xaxis.set_minor_locator(dates.MonthLocator(interval=1))
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%b %Y'))
    ax1.yaxis.set_major_locator(ticker.AutoLocator())
    ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    for _, trade in positions.iterrows():
        trade_date = pd.to_datetime(trade['Trade Date'])
        price_quantity = trade['Price']
        color = 'red' if trade['Action'] == 'SELL_OPEN' else 'green'
        ax1.plot(trade_date, price_quantity, 'o', color=color)

    if position_type == 'SHORT':
        dd = drawdown(data['#PX_LAST'])
        ax1.plot(data.index, dd['Peaks'], label='Peaks', color=peaks_color, linestyle='--', linewidth=1)
        ax2.plot(data.index, dd['Drawdowns'] * 100, label='Drawdown', color=drawdown_color, linestyle='-',
                 linewidth=1.5)

        current_drawdown = dd['Drawdowns'].iloc[-1] * 100
        if current_drawdown < 0:
            ax2.text(data.index[-1], current_drawdown, f'{current_drawdown:.2f}%', color=drawdown_color, fontsize=9,
                     verticalalignment='top')

    elif position_type == 'LONG':
        du = drawup(data['#PX_LAST'])
        ax1.plot(data.index, du['Lows'], label='Lows', color=peaks_color, linestyle='--', linewidth=1)
        ax2.plot(data.index, du['Drawups'] * 100, label='Drawup', color=drawdown_color, linestyle='-',
                 linewidth=1.5)

        current_drawup = du['Drawups'].iloc[-1] * 100
        if current_drawup > 0:
            ax2.text(data.index[-1], current_drawup, f'{current_drawup:.2f}%', color=drawdown_color, fontsize=9,
                     verticalalignment='top')

    ax2.set_xlabel('Date')
    ax2.set_ylabel('%')

    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.xaxis.set_major_locator(dates.MonthLocator(interval=3))
    ax2.xaxis.set_minor_locator(dates.MonthLocator(interval=1))
    ax2.xaxis.set_major_formatter(dates.DateFormatter('%b %Y'))
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax2.yaxis.set_major_locator(ticker.AutoLocator())
    ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    ax2.axhline(0, color='grey', linestyle='--', linewidth=0.5)

    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    plt.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.35), frameon=False, ncol=5)

    filename = f"output/images/{account_name}_{underlying_name}.png"
    plt.savefig(filename)
    plt.close()

    return filename


def plot_future_chart(data: pd.DataFrame, underlying_name: str):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.1})

    ax1.plot(data.index, data['#PX_LAST'], label=f'PX_LAST', color=line_color)
    ax1.plot(data.index, data['50D_SMAVG'], label=f'50D SMAVG',
             color=smavg_color)

    dd = drawdown(data['#PX_LAST'])
    du = drawup(data['#PX_LAST'])

    ax1.plot(data.index, dd['Peaks'], label='Peaks', color=drawdown_color, linestyle='--', linewidth=1)
    ax1.plot(data.index, du['Lows'], label='Lows', color=peaks_color, linestyle='--', linewidth=1)

    ax2.plot(data.index, dd['Drawdowns'] * 100, label='Drawdown', color=drawdown_color, linestyle='-',
             linewidth=1.5)
    ax2.plot(data.index, du['Drawups'] * 100, label='Drawup', color=peaks_color, linestyle='-')

    ax1.set_ylabel('Level')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.xaxis.set_major_locator(dates.MonthLocator(interval=3))
    ax1.xaxis.set_minor_locator(dates.MonthLocator(interval=1))
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%b %Y'))

    ax2.set_xlabel('Date')
    ax2.set_ylabel('%')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.xaxis.set_major_locator(dates.MonthLocator(interval=3))
    ax2.xaxis.set_minor_locator(dates.MonthLocator(interval=1))
    ax2.xaxis.set_major_formatter(dates.DateFormatter('%b %Y'))
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax2.yaxis.set_major_locator(ticker.AutoLocator())
    ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax2.axhline(0, color='grey', linestyle='--', linewidth=0.5)

    current_drawup = du['Drawups'].iloc[-1] * 100
    ax2.text(data.index[-1], current_drawup, f'{current_drawup:.2f}%', color=peaks_color, fontsize=9,
             verticalalignment='top')

    current_drawdown = dd['Drawdowns'].iloc[-1] * 100
    ax2.text(data.index[-1], current_drawdown, f'{current_drawdown:.2f}%', color=drawdown_color, fontsize=9,
             verticalalignment='top')

    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    plt.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.35), frameon=False, ncol=6)

    filename = f"output/images/{underlying_name}.png"
    plt.savefig(filename)
    plt.close()

    return filename


def plot_drawdown_chart(data: pd.DataFrame, underlying_name: str):
    fig, ax = plt.subplots(figsize=(10, 2))

    dd = drawdown(data['#PX_LAST'])

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

    filename = f"output/images/{underlying_name}_drawdown.png"
    plt.savefig(filename)
    plt.close()

    return filename
