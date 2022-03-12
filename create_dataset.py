"""
Script for creating a dataset for trading bot.

Usage:
  create_dataset.py <csv-file> <column-name> [--short-sma=<short-sma>]
    [--long-sma=<long-sma>] [--short-rsi=<short-rsi>]
    [--long-rsi=<long-rsi>]
"""

import logging
import coloredlogs

import pandas as pd

from docopt import docopt


header = "shortEMA,shortSMA,shortRSI,longEMA,longSMA,longRSI,HBB,LBB,Previous,Value\r\n"


def calculate(stock_data, short_sma_period, long_sma_period, short_rsi_period, long_rsi_period):
    logging.info('{},{},{},{}'.format(short_sma_period,
                 long_sma_period, short_rsi_period, long_rsi_period))

    # Arrays with the values while running the for loop
    short_sma_values = []
    long_sma_values = []
    short_rsi_values = []
    long_rsi_values = []

    # Result lines to be written to the file
    result = [header]

    # Set some upfront previous data
    previous_value = 0
    last_short_ema = 0
    last_long_ema = 0

    for value in stock_data:
        if previous_value == 0:
            previous_value = value
            continue

        # SHORT Simple Moving Average Indicator
        short_sma = 0
        short_sma_count = 0
        short_sum1 = 0
        for val in short_sma_values:
            short_sum1 += val
            short_sma_count += 1
        if short_sma_count > 0:
            short_sma = short_sum1 / short_sma_count
        else:
            short_sma = value
        short_sma_values.append(value)
        #####################################

        # LONG Simple Moving Average Indicator
        long_sma = 0
        long_sma_count = 0
        long_sum1 = 0
        for val in long_sma_values:
            long_sum1 += val
            long_sma_count += 1
        if long_sma_count > 0:
            long_sma = long_sum1 / long_sma_count
        else:
            long_sma = value
        long_sma_values.append(value)
        #####################################

        # SHORT Relative Strength Index
        short_avg_loss = 0
        short_avg_gain = 0
        short_gains = 0
        short_losses = 0
        short_rsi = 0
        for val in short_rsi_values:
            if val < 0:
                short_losses += 1
                short_avg_loss += val * -1
            elif val > 0:
                short_gains += 1
                short_avg_gain += val
        if short_gains > 0:
            short_avg_gain = short_avg_gain / short_gains
        if short_losses > 0:
            short_avg_loss = short_avg_loss / short_losses

            rs = short_avg_gain / short_avg_loss
            short_rsi = 100 - (100 / (1 + rs))

        short_rsi_values.append(value - previous_value)
        #########################################

        # LONG Relative Strength Index
        long_avg_loss = 0
        long_avg_gain = 0
        long_gains = 0
        long_losses = 0
        long_rsi = 0
        for val in long_rsi_values:
            if val < 0:
                long_losses += 1
                long_avg_loss += val * -1
            elif val > 0:
                long_gains += 1
                long_avg_gain += val
        if long_gains > 0:
            long_avg_gain = long_avg_gain / long_gains
        if long_losses > 0:
            long_avg_loss = long_avg_loss / long_losses

            rs = long_avg_gain / long_avg_loss
            long_rsi = 100 - (100 / (1 + rs))

        long_rsi_values.append(value - previous_value)
        #########################################

        # SHORT Exponencial Moving Average (EMA)
        weighted_multiplier = 2 / (short_sma_period + 1)

        short_ema = value * weighted_multiplier + \
            last_short_ema * (1 - weighted_multiplier)

        last_short_ema = short_ema
        #########################################

        # SHORT Exponencial Moving Average (EMA)
        weighted_multiplier = 2 / (long_sma_period + 1)

        long_ema = value * weighted_multiplier + \
            last_long_ema * (1 - weighted_multiplier)

        last_long_ema = long_ema
        #########################################

        # SHORT Bollinger Bands
        # -- Standard deviation
        sd = 0
        for val in short_sma_values:
            sd += (val - short_sma) ** 2
        if short_sma_count > 0:
            sd = (sd / short_sma_count) ** 0.5
        # --

        # -- Higher band
        higher_band = short_sma + 2 * sd

        # -- Lower band
        lower_band = short_sma - 2 * sd
        ##########################################

        # Result array
        if short_rsi != 0 and long_rsi != 0 and short_sma != 0 and long_sma != 0:
            result.append("{},{},{},{},{},{},{},{},{},{}\r\n".format(short_ema, long_ema, short_sma,
                          long_sma, short_rsi, long_rsi, higher_band, lower_band, previous_value, value))

        # Moving arrays - deleting the first item so it's always the same size
        if short_sma_values.__len__() >= short_sma_period:
            short_sma_values.__delitem__(0)
        if short_rsi_values.__len__() >= short_rsi_period:
            short_rsi_values.__delitem__(0)
        if long_sma_values.__len__() >= long_sma_period:
            long_sma_values.__delitem__(0)
        if long_rsi_values.__len__() >= long_rsi_period:
            long_rsi_values.__delitem__(0)

        # Previous values to be used in the next run
        previous_value = value

    return result


def main(csv_file, column_name, short_sma_period, long_sma_period, short_rsi_period, long_rsi_period):
    """
    Args: [python create_dataset.py --help]
    """

    df = pd.read_csv(csv_file)

    stock_data = list(df[column_name])

    result = calculate(stock_data, short_sma_period,
                       long_sma_period, short_rsi_period, long_rsi_period)

    open(str(csv_file).replace('.csv', '_result.csv'), 'w+').writelines(result)


if __name__ == "__main__":
    args = docopt(__doc__)

    csv_file = args["<csv-file>"]
    column_name = args["<column-name>"]

    # Periods to be calculated
    short_sma_period = int(args["--short-sma"]) if args["--short-sma"] else 24
    long_sma_period = int(args["--long-sma"]) if args["--long-sma"] else 168
    short_rsi_period = int(args["--short-rsi"]) if args["--short-rsi"] else 12
    long_rsi_period = int(args["--long-rsi"]) if args["--long-rsi"] else 84

    coloredlogs.install(level="DEBUG")

    try:
        main(csv_file, column_name, short_sma_period,
             long_sma_period, short_rsi_period, long_rsi_period)
    except KeyboardInterrupt:
        print("Aborted!")
