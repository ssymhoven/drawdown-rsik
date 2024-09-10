import os

from matplotlib.colors import LinearSegmentedColormap

from data_provider import get_account_futures, get_futures_data
from plot import plot_drawdown_chart
from utility import escape_latex, cleanup_aux_files, positions_overview, write_mail
import dataframe_image as dfi
from jinja2 import Template
import subprocess
from pdf2image import convert_from_path


account_future_positions = get_account_futures()
futures_data = get_futures_data()


def generate_futures_report():
    futures = []

    for c in futures_data.columns:
        data = futures_data[c]
        data.dropna(inplace=True)
        drawdown_chart = plot_drawdown_chart(data=data, underlying_name=c)

        futures.append({
            'name': escape_latex(c),
            'drawdown': drawdown_chart
        })

    with open('templates/future-overview-drawdown-template.tex', 'r') as file:
        template = Template(file.read())
    rendered = template.render(data=futures)

    report_path = os.path.join("output", "futures", "report.tex")
    with open(report_path, 'w') as file:
        file.write(rendered)

    subprocess.run(['pdflatex', report_path, '-output-directory', 'output/futures', f'-jobname=Futures_Drawdown_Overview'])
    page = convert_from_path('output/futures/Futures_Drawdown_Overview.pdf', dpi=100)[0]
    page.save('output/futures/Futures_Drawdown_Overview.png', 'PNG')
    mail_data = {'drawdown': 'output/futures/Futures_Drawdown_Overview.png'}

    all_positions = positions_overview(data=futures_data, positions=account_future_positions)

    if not all_positions.empty:
        max_abs_value_aeq = max(abs(all_positions['% since AEQ'].min().min()),
                                abs(all_positions['% since AEQ'].max().max()))
        cm = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"], N=len(all_positions) if len(all_positions) > 3 else 3)

        styled_all_positions = (all_positions.style.bar(subset='% since AEQ', cmap=cm, align=0, vmax=max_abs_value_aeq, vmin=-max_abs_value_aeq)
                                .set_table_styles([
                                    {'selector': 'th.col1',
                                     'props': [('border-left', '1px solid black')]},
                                    {'selector': 'td.col1',
                                     'props': [('border-left', '1px solid black')]}
                                ])
                                                        .format({
                                    'AEQ': "{:,.2f}",
                                    '% since AEQ': "{:.2f}%",
                                    'Volume': "{:,.0f}",
                                    'P&L': "{:,.2f}",
                                    'Exposure': "{:.2f}%"
                                }).hide(axis="index"))

        dfi.export(styled_all_positions, 'output/futures/Positions_Overview.png', table_conversion="selenium")
        mail_data.update({'futures': 'output/futures/Positions_Overview.png'})

    cleanup_aux_files()

    return mail_data
