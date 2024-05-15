import locale
import os

from matplotlib.colors import LinearSegmentedColormap

from plot import plot_future_position_chart, plot_future_chart, plot_drawdown_chart
from utility import get_account_futures, get_futures_data, momentum_table, escape_latex, position_details, \
    get_future_positions, cleanup_aux_files, positions_overview, write_mail
import dataframe_image as dfi
from jinja2 import Template
import subprocess
from pdf2image import convert_from_path

locale.setlocale(locale.LC_ALL, 'German')
account_future_positions = get_account_futures()
futures_data = get_futures_data()

output_dir = "output"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

account_details = {}
futures = []
mail = False

if __name__ == '__main__':
    mail_data = {
        'files': list(),
    }

    for (name, position_name), row in account_future_positions.iterrows():

        if name not in account_details:
            account_details[name] = {
                "positions": []
            }

        underlying_name = row['underlying_name']
        average_entry_quote = row['average_entry_quote']
        position_type = row['position_type']

        underlying_data = futures_data.get(underlying_name, None)

        if underlying_data is None:
            raise Exception(f"Error: {underlying_name} not found in futures_data dictionary.")

        positions = get_future_positions(account_id=row['account_id'], position_name=position_name)

        chart = plot_future_position_chart(data=underlying_data, account_name=name, underlying_name=underlying_name,
                                           avg_entry_quote=average_entry_quote, position_type=position_type,
                                           positions=positions)
        # Positions
        styled_positions = positions.style.format({
            'Volume': '{:,.0f}',
            'Price': '{:,.2f}'
        }).hide(axis="index")

        dfi.export(styled_positions, f"output/images/{name}_{underlying_name}_orders.png", table_conversion="matplotlib")

        # Momentum
        momentum = momentum_table(data=underlying_data).T
        max_abs_value = max(abs(momentum.min().min()), abs(momentum.max().max()))
        cm = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"], N=10)
        styled_momentum = momentum.style.background_gradient(cmap=cm, vmin=-max_abs_value, vmax=max_abs_value).format("{:.2%}")
        dfi.export(styled_momentum, f"output/images/{name}_{underlying_name}_momentum.png", table_conversion="matplotlib")

        details = position_details(data=underlying_data, row=row).T
        styled_details = details.style.format({
            'AEQ': "{:,.2f}",
            '% since AEQ': "{:.2f}%",
            'Volume': "{:,.0f}",
            'P&L': "{:,.2f}",
            'Exposure': "{:.2f}%"
        })

        dfi.export(styled_details, f"output/images/{name}_{underlying_name}_details.png", table_conversion="matplotlib")

        data = {
            'name': escape_latex(underlying_name),
            'type': position_type,
            'chart': chart,
            'momentum': f"output/images/{name}_{underlying_name}_momentum.png",
            'details': f"output/images/{name}_{underlying_name}_details.png",
            'orders': f"output/images/{name}_{underlying_name}_orders.png"
        }

        account_details[name].get('positions').append(data)

    # Plot indices
    for (k, v) in futures_data.items():
        chart = plot_future_chart(data=v, underlying_name=k)
        drawdown_chart = plot_drawdown_chart(data=v, underlying_name=k)

        momentum = momentum_table(data=v).T
        max_abs_value = max(abs(momentum.min().min()), abs(momentum.max().max()))
        cm = LinearSegmentedColormap.from_list("custom_red_green", ["red", "white", "green"], N=10)
        styled_momentum = momentum.style.background_gradient(cmap=cm, vmin=-max_abs_value, vmax=max_abs_value).format(
            "{:.2%}")
        dfi.export(styled_momentum, f"output/images/{k}_momentum.png",
                   table_conversion="matplotlib")

        futures.append({
            'name': escape_latex(k),
            'chart': chart,
            'momentum': f'output/images/{k}_momentum.png',
            'drawdown': drawdown_chart
        })

    # Plot Future Positions Report
    for name, positions in account_details.items():

        with open('drawdown-future-position-template.tex', 'r') as file:
            template = Template(file.read())

        rendered = template.render(name=escape_latex(name), data=positions)

        report_path = os.path.join(output_dir, "report.tex")

        with open(report_path, 'w') as file:
            file.write(rendered)

        subprocess.run(['pdflatex', report_path, '-output-directory', output_dir, f'-jobname={name}_Futures'])
        files = mail_data.get('files')
        files.append(f'{output_dir}/{name}_Futures.pdf')

    # Render Future Detail Report
    with open('future-overview-detail-template.tex', 'r') as file:
        template = Template(file.read())
    rendered = template.render(data=futures)

    report_path = os.path.join(output_dir, "report.tex")
    with open(report_path, 'w') as file:
        file.write(rendered)
    subprocess.run(['pdflatex', report_path, '-output-directory', output_dir, f'-jobname=Futures_Detail_Overview'])
    mail_data.get('files').append(f'{output_dir}/Futures_Detail_Overview.pdf')

    # Render Future Drawdown Report
    with open('future-overview-drawdown-template.tex', 'r') as file:
        template = Template(file.read())
    rendered = template.render(data=futures)

    report_path = os.path.join(output_dir, "report.tex")
    with open(report_path, 'w') as file:
        file.write(rendered)
    subprocess.run(['pdflatex', report_path, '-output-directory', output_dir, f'-jobname=Futures_Drawdown_Overview'])
    page = convert_from_path(f'{output_dir}/Futures_Drawdown_Overview.pdf', dpi=120)[0]
    page.save(f'{output_dir}/Futures_Drawdown_Overview.png', 'PNG')
    mail_data.update({'drawdown': f'{output_dir}/Futures_Drawdown_Overview.png'})

    all_positions = positions_overview(data=futures_data, positions=account_future_positions)
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

    if mail:
        write_mail(mail_data)




