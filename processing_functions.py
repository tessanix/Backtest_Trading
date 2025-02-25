import pandas as pd
import pickle 
import numpy as np
import matplotlib.pyplot as plt

### SAVE THE DATA ###
def save_object(obj, filename):
    with open(filename, 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)

### LOAD THE DATA ###
def load_object(filename):
    with open(filename, 'rb') as input: 
        return pickle.load(input)
    
def compute_Ichimoku_on_DataFrame(df: pd.DataFrame):
    # Compute rolling max/min for the necessary periods
    highest_9 = df['high'].rolling(window=9).max()
    lowest_9 = df['low'].rolling(window=9).min()

    highest_26 = df['high'].rolling(window=26).max()
    lowest_26 = df['low'].rolling(window=26).min()

    highest_52 = df['high'].rolling(window=52).max()
    lowest_52 = df['low'].rolling(window=52).min()

    # Compute Ichimoku components
    df['tenkan'] = (highest_9 + lowest_9) / 2
    df['kijun'] = (highest_26 + lowest_26) / 2
    df['ssa'] = (df['tenkan'] + df['kijun']) / 2
    df['ssb'] = (highest_52 + lowest_52) / 2

    # Shift the "ssa" and "ssb" values to align them properly
    df['ssa'] = df['ssa'].shift(26)
    df['ssb'] = df['ssb'].shift(26)
    
    return df


def create_df_M5(use3UT=False): #, windowForLevels=12):
    path = "C:/Users/tessa/MotiveWave Data/"
    start_date = pd.to_datetime('2020-03-24 12:00:00') #data are weird before this data (a problem from data provider???)

    ### M5 ###
    df_M5 = pd.read_csv(
        #filepath_or_buffer=path+"@MES.CME.TOP_STEP_1.csv",
        filepath_or_buffer=path+"@CL.NYMEX.TOP_STEP_1.csv",

        names=["datetime", "open", "high", "low","close", "volume"],
        header=None,
        delimiter=","
    )
    df_M5['datetime'] = pd.to_datetime(df_M5['datetime'], format='%d/%m/%Y %H:%M:%S')
    df_M5 = df_M5[(df_M5['datetime'] >= start_date)]
    df_M5 = compute_Ichimoku_on_DataFrame(df_M5)

    if use3UT:
        ### M15 ###
        df_M15 = pd.read_csv(
            filepath_or_buffer=path+"@MES.CME.TOP_STEP_15.csv",
            names=["datetime", "open", "high", "low","close", "volume"],
            header=None,
            delimiter=","
        )
        df_M15['datetime'] = pd.to_datetime(df_M15['datetime'], format='%d/%m/%Y %H:%M:%S')
        df_M15 = df_M15[(df_M15['datetime'] >= start_date)]
        df_M15 = compute_Ichimoku_on_DataFrame(df_M15)
        
        ### H1 ###
        df_H1 = pd.read_csv(
            filepath_or_buffer=path+"@MES.CME.TOP_STEP_60.csv",
            names=["datetime", "open", "high", "low","close", "volume"],
            header=None,
            delimiter=","
        )
        df_H1['datetime'] = pd.to_datetime(df_H1['datetime'], format='%d/%m/%Y %H:%M:%S')
        df_H1 = df_H1[(df_H1['datetime'] >= start_date)]
        df_H1 = compute_Ichimoku_on_DataFrame(df_H1)

        ### ADD SSA AND SSB DATA FROM M15 AND H1 ###
        df_M5 = pd.merge(df_M5, df_M15[['datetime', 'ssa', 'ssb']], on='datetime', how='left', suffixes = ["", "_m15"])
        df_M5["ssa_m15"] = df_M5["ssa_m15"].ffill()
        df_M5["ssb_m15"] = df_M5["ssb_m15"].ffill()

        df_M5 = pd.merge(df_M5, df_H1[['datetime', 'ssa', 'ssb']], on='datetime', how='left', suffixes = ["", "_h1"])
        df_M5["ssa_h1"] = df_M5["ssa_h1"].ffill()
        df_M5["ssb_h1"] = df_M5["ssb_h1"].ffill()

        del df_M15
        del df_H1

    # 1. Convertir la colonne datetime en index pour faciliter la resampling des données journalières
    df_M5.set_index('datetime', inplace=True)

    # 2. Calculer les prix journaliers : High, Low et Close (resampling daily)
    df_daily = df_M5.resample('D').agg({'high': 'max', 'low': 'min', 'close': 'last'})

    # 3. Calculer les niveaux de point pivot (PP, R3, R2, R1, S1, S2, S3)
    df_daily['PP'] = (df_daily['high'] + df_daily['low'] + df_daily['close']) / 3
    df_daily['R1'] = (2 * df_daily['PP']) - df_daily['low']
    df_daily['R2'] = df_daily['PP'] + (df_daily['high'] - df_daily['low'])
    df_daily['R3'] = df_daily['high'] + 2 * (df_daily['PP'] - df_daily['low'])
    df_daily['S1'] = (2 * df_daily['PP']) - df_daily['high']
    df_daily['S2'] = df_daily['PP'] - (df_daily['high'] - df_daily['low'])
    df_daily['S3'] = df_daily['low'] - 2 * (df_daily['high'] - df_daily['PP'])

    # 4. Fusionner ces points pivots journaliers dans le dataframe 5min
    # On va faire un merge sur l'index (qui est 'datetime' après resampling)
    df_M5 = df_M5.merge(df_daily[['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']], left_index=True, right_index=True, how='left')
    del df_daily

    # 5. Optionnel : remplir les valeurs manquantes si nécessaire (avec ffill ou bfill)
    df_M5[['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']] = df_M5[['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']].ffill()

    # Affichage du DataFrame mis à jour
    df_M5.dropna(inplace=True)
    df_M5.reset_index(inplace=True)

    # df_M15['support']    = np.where(df_M15.low == df_M15.low.rolling(windowForLevels, center=True).min(), df_M15.low, 0) #C'est tricher car on utilise center=True mais on l'utilise quand meme pour un gain de temps de backtest
    # df_M15['resistance'] = np.where(df_M15.high == df_M15.high.rolling(windowForLevels, center=True).max(), df_M15.high, 0)
    
    # ### ADD SUPPORT AND RESISTANCE DATA FROM M15 ###
    # df_M5 = pd.merge(df_M5, df_M15[['datetime', 'support', 'resistance']], on='datetime', how='left', suffixes = ["", "_m15"])
    # df_M5["chop"] = choppiness_index(df_M5, chopPeriod)
    # df_M5.dropna(inplace=True)
    # df_M5.reset_index(inplace=True)

    return df_M5


def sort_by_winrate(item):
    _, dict_values = item
    return dict_values['Winrate [%]']

def sort_by_total_pnl(item):
    _, dict_values = item
    return dict_values['Total return net [%]']

def create_winrate_dictionnary(trades_database, sort_option=2, tickSize = 0.25):
    winrate_dictionnary = {}

    for id, trade_data in trades_database.items():
        df, sl, tp, onlyUSSession, sm, use3UT = trade_data #, nbr_of_points, delta_in_ticks, windowForLevels = trade_data

        loser_entry_price = df.loc[df['profit_from_start(%)']<0, 'entry_price']
        loser_exit_price = df.loc[df['profit_from_start(%)']<0, 'exit_price']
        avg_real_sl_executed = (abs(loser_entry_price-loser_exit_price).mean())/tickSize

        wins = df.loc[df['profit_from_start(%)']>0, 'position'].count()
        loss = df.loc[df['profit_from_start(%)']<0, 'position'].count()
        winrate = 0.0 if loss+wins == 0.0 else 100*wins/(loss+wins)
        breakevens = df.loc[df['profit_from_start(%)']==0, 'position'].count()
        # avg_gain_from_start = df.loc[df['profit_from_start(%)']>0, 'profit_from_start(%)'].mean()
        # avg_loss_from_start = df.loc[df['profit_from_start(%)']<0, 'profit_from_start(%)'].mean()

        avg_gain_including_fees_from_start = df.loc[df['profit_including_fees_from_start(%)']>0, 'profit_including_fees_from_start(%)'].mean()
        avg_loss_including_fees_from_start = df.loc[df['profit_including_fees_from_start(%)']<0, 'profit_including_fees_from_start(%)'].mean()

        # median_times_below_breakeven = df['times_below_breakeven'].median()
        total_return_without_fees_from_start = df['profit_from_start(%)'].sum()
        total_return_including_fees_from_start = df['profit_including_fees_from_start(%)'].sum()

        quantiles_duration = (df["exit_date"]-df["entry_date"]).quantile([0.50,0.75])
        mean_tp = tp[0]+tp[1]/2

        winrate_dictionnary[id] = {
            'Winrate [%]': round(winrate, 3), 
            "Total return brut [%]": round(total_return_without_fees_from_start, 2),
            "Total return net [%]": round(total_return_including_fees_from_start, 2),
            # "Avg. gain brut [%]": round(avg_gain_from_start, 2),
            # "Avg. loss brut [%]": round(avg_loss_from_start,2),
            "Avg. gain net [%]": round(avg_gain_including_fees_from_start, 2),
            "Avg. loss net [%]": round(avg_loss_including_fees_from_start,2),
            'Risk ratio': round(mean_tp/avg_real_sl_executed, 2), 
            'Nbr Wins/Loss/Breakeven' : (wins, loss, breakevens),
            "Avg. executed SL [Ticks]": round(avg_real_sl_executed, 1),
            'TP [Ticks]': (tp[0], tp[1]),
            "Q2 duration (médiane)": quantiles_duration.loc[0.50], 
            "Q3 duration (75%)": quantiles_duration.loc[0.75],
            "stop_method": sm,
            'US_session_only' : onlyUSSession,
            'use3UT': use3UT,
            # 'mta':mta,
            # 'chopValue': chopValue, 
            # 'chopPeriod':
            # 'nbr_of_points':nbr_of_points,
            # 'delta_in_ticks':delta_in_ticks,
            # 'windowForLevels':windowForLevels,
            # "ticksAbove": ticksAbove
            #'nbr_of_trades': wins.item()+loss.item(), 
        }
    if sort_option == 1:
        winrate_dictionnary = dict(sorted(winrate_dictionnary.items(), key=sort_by_winrate))
    elif sort_option == 2:
        winrate_dictionnary = dict(sorted(winrate_dictionnary.items(), key=sort_by_total_pnl))
        
    return winrate_dictionnary

def true_range(df):
    tr = pd.DataFrame(index=df.index)
    tr['HL'] = df['high'] - df['low']
    tr['HC_prev'] = (df['high'] - df['close'].shift(1)).abs()
    tr['LC_prev'] = (df['low'] - df['close'].shift(1)).abs()
    tr['TR'] = tr[['HL', 'HC_prev', 'LC_prev']].max(axis=1)
    return tr['TR']

# Function to calculate the Choppiness Index (CHOP)
def choppiness_index(df, period=14):
    tr = true_range(df)
    tr_sum = tr.rolling(window=period).sum()
    max_range = df['high'].rolling(window=period).max() - df['low'].rolling(window=period).min()
    
    chop = 100 * (np.log10(tr_sum) - np.log10(max_range)) / np.log10(period)
    return chop

def plot_backtested_return_curve(
    pathOfData='trade_datas/basicEntries_3UT_levels_breakeven=0_StrategyStop1&2.pkl',
    plotAllDatas=False,
    dataIdsSelected=[8,14],
    plotSize = (20,16)
):
    trades_database = load_object(pathOfData)
    selected_ids = trades_database.keys() if plotAllDatas else dataIdsSelected

    plt.figure(figsize=plotSize)

    for id in selected_ids:
        df_temp =  trades_database[id][0]

        # Définir 'datetime' comme index pour pouvoir utiliser resample
        df_temp.set_index('entry_date', inplace=True)

        # Resampler les données par semaine (par exemple, la somme des profits par semaine)
        df_temp = df_temp.resample('W').agg({'profit_from_start(%)': ['sum']})

        capital = 50_000
        l = []
        for profit in df_temp['profit_from_start(%)']["sum"]:
            capital += 50_000 * profit/ 100
            l.append(capital)

        plt.plot(df_temp.index, l, label=f"Strategy {id}")  # Use a label for each plot for better identification

        del df_temp

    # Add labels and title
    plt.xlabel("Time")
    plt.ylabel("Capital")
    plt.xticks(rotation=45)
    plt.title("Capital Growth Across Multiple Strategies")
    plt.legend()  # Show legend for all plots
    plt.grid(True)
    plt.show()