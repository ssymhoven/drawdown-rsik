import locale

from plot import plot_futurue_position_chart
from utility import get_account_futures, get_futures_data, momentum_table, escape_latex, position_details
from jinja2 import Template
import subprocess

locale.setlocale(locale.LC_ALL, 'German')
account_future_positions = get_account_futures()
futures_data = get_futures_data()


if __name__ == '__main__':

    for (name, position_name), row in account_future_positions.iterrows():
        underlying_name = row['underlying_name']
        average_entry_quote = row['average_entry_quote']
        position_type = row['position_type']

        underlying_data = futures_data.get(underlying_name, None)

        if underlying_data is None:
            raise Exception(f"Error: {underlying_name} not found in futures_data dictionary.")

        chart = plot_futurue_position_chart(data=underlying_data, account_name=name, underlying_name=underlying_name,
                                            avg_entry_quote=average_entry_quote, position_type=position_type)

        momentum = momentum_table(data=underlying_data).T
        momentum = momentum.map(lambda x: f'{x:.2f}%')
        momentum_latex_table = momentum.to_latex(index=True, escape=True, header=True, longtable=True)

        details = position_details(data=underlying_data, row=row).T
        details['AEQ'] = details['AEQ'].map(lambda x: f'{x:.2f}')
        details['% since AEQ'] = details['% since AEQ'].map(lambda x: f'{x:.2f}%')
        details['Volume'] = details['Volume'].map(lambda x: f'{x:.0f}')
        details['P&L'] = details['P&L'].map(lambda x: locale.format_string('%.2f', x, True))
        details['Exposure'] = details['Exposure'].map(lambda x: f'{x:.2f}%')

        details_latex_table = details.to_latex(index=True, escape=True, header=True, longtable=True)

        data = {
            'name': escape_latex(name),
            'position_name': escape_latex(underlying_name),
            'chart': chart,
            'momentum': momentum_latex_table,
            'position': details_latex_table
        }

        with open('template.tex', 'r') as file:
            template = Template(file.read())

        rendered = template.render(data=data)

        with open('filled_report.tex', 'w') as file:
            file.write(rendered)

        subprocess.run(['pdflatex', 'filled_report.tex', '-output-directory=output', f'-jobname={name}_{underlying_name}'])
        subprocess.run(['pdflatex', 'filled_report.tex', '-output-directory=output', f'-jobname={name}_{underlying_name}'])

