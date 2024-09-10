from data_provider import us_sector, eu_sector, regions
from plot import style_index_with_bars
from utility import calc_sector_diff


def generate_positioning_report():

    diff = calc_sector_diff(us=us_sector, eu=eu_sector)
    us_sector_chart = style_index_with_bars(index=us_sector, name='US', hide_index=False, borders=[0, 4, "last"])
    eu_sector_chart = style_index_with_bars(index=eu_sector, name='EU', hide_index=False, borders=[0, 4, "last"])
    diff_sector_chart = style_index_with_bars(index=diff, name='EU_vs_US', hide_index=False, borders=[0, 4, "last"])
    regions_chart = style_index_with_bars(index=regions, name='Regions', hide_index=False, borders=[0, 4])

    return {
        'Regionen': regions_chart,
        'EU': eu_sector_chart,
        'US': us_sector_chart,
        'EU vs. US': diff_sector_chart,
    }