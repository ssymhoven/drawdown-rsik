import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker

line_color = '#7EC0C6'
smavg_color = '#124877'
avg_color = '#E91457'


def plot_dataframes(data: pd.DataFrame, account_name: str, underlying_name: str, avg_entry_quote: float,
                    position_type: str):
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(data.index, data['#PX_LAST'], label=f'PX_LAST ({data["#PX_LAST"].iloc[-1]})', color=line_color)
    ax.plot(data.index, data['50D_SMAVG'], label=f'50D SMAVG ({data["50D_SMAVG"].iloc[-1]})', color=smavg_color)
    ax.axhline(y=avg_entry_quote, color=avg_color, linestyle='--', linewidth=1,
               label=f'Average Entry Quote ({avg_entry_quote})')

    ax.set_xlim(data.index.min(), data.index.max())
    ax.set_title(f'{account_name} - {position_type} {underlying_name}')
    ax.set_xlabel('Date')
    ax.set_ylabel('Level')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.xaxis.set_minor_locator(dates.MonthLocator(interval=1))
    ax.xaxis.set_major_locator(dates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(dates.DateFormatter('%b %Y'))
    ax.yaxis.set_major_locator(ticker.AutoLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=3)

    plt.tight_layout()
    plt.savefig(f"output/{account_name}_{underlying_name}.png")
