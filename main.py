from plot import plot_dataframes
from utility import get_account_futures, get_futures_data

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

        plot_dataframes(data=underlying_data, account_name=name, underlying_name=underlying_name,
                        avg_entry_quote=average_entry_quote, position_type=position_type)

