from data_provider import get_positions, us_sector, eu_sector, filter_positions
from plot import style_positions_with_bars
from utility import calc_position_rel_performance_vs_sector


def generate_risk_report():
    risk = {}

    positions = get_positions()
    positions = calc_position_rel_performance_vs_sector(positions=positions, eu=eu_sector, us=us_sector)

    unique_names = positions.index.get_level_values(0).unique()

    for name in unique_names:
        subset = positions.loc[name]

        _, negative_positions = filter_positions(positions=subset)

        underperformed_details_chart = style_positions_with_bars(positions=negative_positions,
                                                                 name=f'{name}_underperformed')
        risk.update({name: underperformed_details_chart})


    return risk
