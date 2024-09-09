import locale
import os

from matplotlib.colors import LinearSegmentedColormap

from plot import plot_drawdown_chart
from utility import get_account_futures, get_futures_data, escape_latex, cleanup_aux_files, positions_overview, write_mail
import dataframe_image as dfi
from jinja2 import Template
import subprocess
from pdf2image import convert_from_path

locale.setlocale(locale.LC_ALL, 'German')
account_future_positions = get_account_futures()
futures_data = get_futures_data()

output_dir = "output"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

futures = []

if __name__ == '__main__':

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

    report_path = os.path.join(output_dir, "report.tex")
    with open(report_path, 'w') as file:
        file.write(rendered)
    subprocess.run(['pdflatex', report_path, '-output-directory', output_dir, f'-jobname=Futures_Drawdown_Overview'])
    page = convert_from_path(f'{output_dir}/Futures_Drawdown_Overview.pdf', dpi=100)[0]
    page.save(f'{output_dir}/Futures_Drawdown_Overview.png', 'PNG')
    mail_data = {'drawdown': f'{output_dir}/Futures_Drawdown_Overview.png'}

    all_positions = positions_overview(data=futures_data, positions=account_future_positions)

    if not all_positions.empty:
        max_abs_value_aeq = max(abs(all_positions['% since AEQ'].min().min()),
                                abs(all_positions['% since AEQ'].max().max()))
        cm_aeq = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"],
                                                   N=len(all_positions))

        styled_all_positions = (all_positions.style.background_gradient(cmap=cm_aeq, subset=['% since AEQ'],
                                                                        vmin=-max_abs_value_aeq, vmax=max_abs_value_aeq)
                                .format({
                                    'AEQ': "{:,.2f}",
                                    '% since AEQ': "{:.2f}%",
                                    'Volume': "{:,.0f}",
                                    'P&L': "{:,.2f}",
                                    'Exposure': "{:.2f}%"
                                }).hide(axis="index"))

        dfi.export(styled_all_positions, f"{output_dir}/Positions_Overview.png", table_conversion="matplotlib")
        mail_data.update({'positions': f'{output_dir}/Positions_Overview.png'})

    cleanup_aux_files()
    write_mail(mail_data)



