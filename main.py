import locale
import os

from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

from plot import plot_future_position_chart, plot_future_chart
from utility import get_account_futures, get_futures_data, momentum_table, escape_latex, position_details, \
    get_future_positions, cleanup_aux_files
import dataframe_image as dfi
from jinja2 import Template
import subprocess

locale.setlocale(locale.LC_ALL, 'German')
account_future_positions = get_account_futures()
futures_data = get_futures_data()

output_dir = "output"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

account_details = {}
futures = []

if __name__ == '__main__':

    # Pot Future Positions
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
            'momentum': f'output/images/{k}_momentum.png'
        })

    for name, positions in account_details.items():

        with open('drawdown-future-position-template.tex', 'r') as file:
            template = Template(file.read())

        rendered = template.render(name=escape_latex(name), data=positions)

        report_path = os.path.join(output_dir, "report.tex")

        with open(report_path, 'w') as file:
            file.write(rendered)

        subprocess.run(['pdflatex', report_path, '-output-directory', output_dir, f'-jobname={name} Futures'])

    with open('future-template.tex', 'r') as file:
        template = Template(file.read())

    rendered = template.render(data=futures)

    report_path = os.path.join(output_dir, "report.tex")

    with open(report_path, 'w') as file:
        file.write(rendered)

    subprocess.run(['pdflatex', report_path, '-output-directory', output_dir, f'-jobname=Futures Overview'])

    cleanup_aux_files()




