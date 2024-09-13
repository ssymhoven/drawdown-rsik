import locale
import os

from bm import generate_allocation_report
from futures import generate_futures_report
from positioning import generate_positioning_report
from risk import generate_risk_report
from third_party import generate_third_party_report
from utility import write_mail

locale.setlocale(locale.LC_ALL, 'German')
output_dir = "output"
os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)


if __name__ == '__main__':
    positioning_mail_data = generate_positioning_report()
    futures_mail_data = generate_futures_report()
    risk_mail_data = generate_risk_report()
    third_party_mail_data = generate_third_party_report()
    allocation_mail_data = generate_allocation_report()

    write_mail(positioning_mail_data, futures_mail_data, risk_mail_data, third_party_mail_data, allocation_mail_data)




