import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker

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

    filename = f"output/images/{underlying_name}_drawdown.png"
    plt.savefig(filename)
    plt.close()

    return filename
