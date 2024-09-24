from data_provider import third_party_products
from plot import style_third_party
from utility import group_funds


def generate_third_party_report():
    esg = third_party_products[third_party_products.index.get_level_values('Name').str.contains("ESG")]
    flex = third_party_products[third_party_products.index.get_level_values('Name').str.contains("Flex")]
    strategie_select = third_party_products[third_party_products.index.get_level_values('Name').str.contains("Strategie - Select")]
    premium_select = third_party_products[third_party_products.index.get_level_values('Name').str.contains("Premium Select")]

    satellites = third_party_products[third_party_products["Query"].isin(
        ["HAL30II GR Equity", "BCBIOII GR Equity", "GSINDAI LX Equity", "DRAKTIV GR Equity", "DRAKTNA GR Equity",
         "ZPRX GR Equity",
         "GMEPISD LX Equity", "XSNR GT Equity", "SGLD LN Equity"])]

    esg_chart = style_third_party(positions=group_funds(esg), name="VV-ESG")
    flex_chart = style_third_party(positions=group_funds(flex), name="VV-Flex")
    strategie_select_chart = style_third_party(positions=group_funds(strategie_select), name="Strategie-Select")
    premium_select_chart = style_third_party(positions=group_funds(premium_select), name="Premium-Select")
    satellites_chart = style_third_party(positions=group_funds(satellites), name="Thirds-Equity")

    return {
        'flex': flex_chart,
        'esg': esg_chart,
        'strategie-select': strategie_select_chart,
        'premium-select': premium_select_chart
    }


if __name__ == '__main__':
    generate_third_party_report()