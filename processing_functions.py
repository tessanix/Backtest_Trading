import pandas as pd

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


def create_df_M5():
    path = "C:/Users/tessa/MotiveWave Data/"

    ### M5 ###
    df_M5 = pd.read_csv(
        filepath_or_buffer=path+"@MES.CME.TOP_STEP_5.csv",
        names=["datetime", "open", "high", "low","close", "volume"],
        header=None,
        delimiter=","
    )
    df_M5['datetime'] = pd.to_datetime(df_M5['datetime'], format='%d/%m/%Y %H:%M:%S')
    df_M5 = compute_Ichimoku_on_DataFrame(df_M5)

    ### M15 ###
    df_M15 = pd.read_csv(
        filepath_or_buffer=path+"@MES.CME.TOP_STEP_15.csv",
        names=["datetime", "open", "high", "low","close", "volume"],
        header=None,
        delimiter=","
    )
    df_M15['datetime'] = pd.to_datetime(df_M15['datetime'], format='%d/%m/%Y %H:%M:%S')
    df_M15 = compute_Ichimoku_on_DataFrame(df_M15)

    ### H1 ###
    df_H1 = pd.read_csv(
        filepath_or_buffer=path+"@MES.CME.TOP_STEP_60.csv",
        names=["datetime", "open", "high", "low","close", "volume"],
        header=None,
        delimiter=","
    )
    df_H1['datetime'] = pd.to_datetime(df_H1['datetime'], format='%d/%m/%Y %H:%M:%S')
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
    df_M5 = df_M5.merge(df_daily[['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']], 
                        left_index=True, right_index=True, how='left')

    # 5. Optionnel : remplir les valeurs manquantes si nécessaire (avec ffill ou bfill)
    df_M5[['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']] = df_M5[['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']].ffill()

    # Affichage du DataFrame mis à jour
    df_M5.dropna(inplace=True)
    df_M5.reset_index(inplace=True)

    del df_daily

    return df_M5


def sort_by_winrate(item):
    _, dict_values = item
    return dict_values['winrate (%)']

def sort_by_total_pnl(item):
    _, dict_values = item
    return dict_values['total_pnl_from_start (%)']


def create_winrate_dictionnary(trades_database, sort_option):
    tickSize = 0.25
    winrate_dictionnary = {}

    for id, trade_data in trades_database.items():
        df, sl, tp, onlyUSSession, sm = trade_data

        loser_entry_price = df.loc[df['profit_from_start(%)']<=0, 'entry_price']
        loser_exit_price = df.loc[df['profit_from_start(%)']<=0, 'exit_price']
        avg_real_sl_executed = (abs(loser_entry_price-loser_exit_price).mean())/tickSize

        wins = df.loc[df['profit_from_start(%)']>=0, 'position'].count()
        loss = df.loc[df['profit_from_start(%)']<0, 'position'].count()
        winrate = 0.0 if loss+wins == 0.0 else 100*wins/(loss+wins)
        breakevens = df.loc[df['profit_from_start(%)']==0, 'position'].count()
        avg_gain_from_start = df.loc[df['profit_from_start(%)']>=0, 'profit_from_start(%)'].mean()
        avg_loss_from_start = df.loc[df['profit_from_start(%)']<0, 'profit_from_start(%)'].mean()
        # median_times_below_breakeven = df['times_below_breakeven'].median()
        total_pnl_from_start = df['profit_from_start(%)'].sum()
        quantiles_duration = (df["exit_date"]-df["entry_date"]).quantile([0.50,0.75])

        winrate_dictionnary[id] = {
            'winrate (%)': round(winrate, 3), 
            'risk_ratio': round(tp/sl, 2), 
            "total_pnl_from_start (%)": round(total_pnl_from_start, 2),
            "avg_gain_from_start (%)": round(avg_gain_from_start, 2),
            "avg_loss_from_start (%)": round(avg_loss_from_start,2),
            "median duration": quantiles_duration.loc[0.50], 
            "75percent duration": quantiles_duration.loc[0.75],
            "avg_real_sl_executed":avg_real_sl_executed,
            'TP/SL (Ticks)': (tp, sl),
            'nbr wins/loss/breakeven' : (wins, loss, breakevens),
            "stop_method": sm,
            # "median_times_below_breakeven": round(median_times_below_breakeven,2),
            'US_session_only' : onlyUSSession,
            #'nbr_of_trades': wins.item()+loss.item(), 
        }
    if sort_option == 1:
        winrate_dictionnary = dict(sorted(winrate_dictionnary.items(), key=sort_by_winrate))
    elif sort_option == 2:
        winrate_dictionnary = dict(sorted(winrate_dictionnary.items(), key=sort_by_total_pnl))
        
    return winrate_dictionnary