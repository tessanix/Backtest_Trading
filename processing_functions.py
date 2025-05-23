import pandas as pd
import pickle 
import numpy as np
import matplotlib.pyplot as plt
import re
from values_definition import Position

### SAVE THE DATA ###
def save_object(obj, filename, sanitized=True):
    # Remove invalid characters for Windows file paths
    if sanitized:
        filename = re.sub(r'[<>:"|?*]', '-', filename)
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
    df['chikou'] = df['close'].shift(-26)
    
    return df


def compute_rsi(df, period=14):
    # Calculate the price differences
    delta = df['close'].diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate the rolling averages of gains and losses
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss

    # Calculate RSI using the formula
    rsi = 100 - (100 / (1 + rs))

    return rsi


def create_not_processed_df(timeFramesUsedInMinutes=["1"], instrument="MES"):
    root_path = "C:/Users/tessa/MotiveWave Data/"
    main_df = pd.DataFrame()

    for idx, timeFrame in enumerate(timeFramesUsedInMinutes):
        path =""
        if instrument == "MES":
            path = root_path+"@MES.CME.TOP_STEP_"+timeFrame+".csv"
        elif instrument == "ES":
            path = root_path+"@ES.CME.TOP_STEP_"+timeFrame+".csv"
        elif instrument == "MNQ":
            path = root_path+"@MNQ.CME.TOP_STEP_"+timeFrame+".csv"
        elif instrument == "NQ":
            path = root_path+"@NQ.CME.TOP_STEP_"+timeFrame+".csv"
        elif instrument == "MCL":
            path = root_path+"@MCL.NYMEX.TOP_STEP_"+timeFrame+".csv"
        elif instrument == "CL":
            path = root_path+"@CL.NYMEX.TOP_STEP_"+timeFrame+".csv"
        
        main_df = pd.read_csv(
            filepath_or_buffer=path,
            names=["datetime", "open", "high", "low","close", "volume"],#"high_before_low"],
            header=None,
            delimiter=",",
            dtype={'high_before_low': 'boolean'}
        )
        main_df['datetime'] = pd.to_datetime(main_df['datetime'])
    return main_df

def create_us_calendar_df(start_date="2023-03-24 12:00:00", end_date="2025-02-14 12:00:00", contains=["CPI", "Fed"]):
    df = pd.read_csv(
        filepath_or_buffer="market_data/us_calendar_high_impact.csv",
        delimiter=",",
    )
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[( pd.to_datetime(start_date) <= df['datetime']) & (df['datetime'] <=  pd.to_datetime(end_date))]
    # Filtrer les lignes qui contiennent au moins un mot-clé de la liste
    mask = df['event'].str.contains('|'.join(contains), case=False, na=False)
    df = df[mask]
    df.reset_index(inplace=True)
    return df

def create_df(timeFramesUsedInMinutes=["1"], instrument="ES", 
              start_date="2023-03-24 12:00:00", end_date="2025-02-14 12:00:00", putVolumeInData=False, ATRperiod=14 ): 
    root_path = "market_data/"

    start_date = pd.to_datetime(start_date) #data are weird before this date (a problem from data provider???)
    end_date = pd.to_datetime(end_date)
    main_df = pd.DataFrame()
    usecols = ["datetime", "open", "high", "low", "close", "high_before_low", "volume"] if putVolumeInData else ["datetime", "open", "high", "low", "high_before_low", "close"]
    for idx, timeFrame in enumerate(timeFramesUsedInMinutes):
        if instrument == "ES":
            path = root_path+f"ES_{timeFrame}m_2-10-2020-12-00PM_3-10-2025-12-00PM_preprocessed.csv"
        else:
            print("Intrument "+instrument+" not found")
            return
        
        if idx == 0:
            main_df = pd.read_csv(
                filepath_or_buffer=path,
                usecols=usecols,
                delimiter=";",
            )
            main_df['datetime'] = pd.to_datetime(main_df['datetime'], format='%Y-%m-%d %H:%M:%S') #format='%d/%m/%Y %H:%M:%S')
            if start_date < main_df.iloc[0]['datetime'] or main_df.iloc[-1]['datetime'] < end_date:
                print("AAAAAAAAAAAAA error")
                return 
            main_df = main_df[(start_date <= main_df['datetime']) & (main_df['datetime'] <= end_date)]
            main_df = compute_Ichimoku_on_DataFrame(main_df)
            # main_df['RSI'] = compute_rsi(main_df, period=rsiPeriod)

        else:
            next_timeframe_df = pd.read_csv(
                filepath_or_buffer=path,
                usecols=["datetime", "open", "high", "low", "close"],
                # names=["datetime", "open", "high", "low","close", "volume"],
                # header=None,
                delimiter=";"
            )
            next_timeframe_df['datetime'] = pd.to_datetime(next_timeframe_df['datetime'], format='%Y-%m-%d %H:%M:%S')#format='%d/%m/%Y %H:%M:%S')
            if start_date < next_timeframe_df.iloc[0]['datetime'] or next_timeframe_df.iloc[-1]['datetime'] < end_date:
                print("aaaaaaaaaa error")
                return
            next_timeframe_df = next_timeframe_df[(start_date <= next_timeframe_df['datetime'] ) & (next_timeframe_df['datetime'] <= end_date)]
            next_timeframe_df = compute_Ichimoku_on_DataFrame(next_timeframe_df)
            ### ADD SSA AND SSB DATA FROM SUPERIOR TIMEFRAME ###
            suffixe = "_"+timeFrame
            main_df = pd.merge(main_df, next_timeframe_df[['datetime', 'ssb', 'ssa', 'kijun']], on='datetime', how='left', suffixes = ["", suffixe])
            main_df[["ssb"+suffixe, 'ssa'+suffixe, 'kijun'+suffixe]] = main_df[[ "ssb"+suffixe,'ssa'+suffixe, 'kijun'+suffixe]].ffill()


    main_df.set_index('datetime', inplace=True)

    df_daily = main_df.resample('D').agg({'high': 'max', 'low': 'min', 'close': 'last'})

   # Décalage d’un jour pour utiliser les données de la veille
    df_daily['high_prev'] = df_daily['high'].shift(1)
    df_daily['low_prev'] = df_daily['low'].shift(1)
    df_daily['close_prev'] = df_daily['close'].shift(1)

    # Calcul des pivots classiques avec les données de la veille
    df_daily['PP'] = (df_daily['high_prev'] + df_daily['low_prev'] + df_daily['close_prev']) / 3
    df_daily['R1'] = (2 * df_daily['PP']) - df_daily['low_prev']
    df_daily['R2'] = df_daily['PP'] + (df_daily['high_prev'] - df_daily['low_prev'])
    df_daily['R3'] = df_daily['PP'] + 2 * (df_daily['high_prev'] - df_daily['low_prev'])
    df_daily['S1'] = (2 * df_daily['PP']) - df_daily['high_prev']
    df_daily['S2'] = df_daily['PP'] - (df_daily['high_prev'] - df_daily['low_prev'])
    df_daily['S3'] = df_daily['PP'] - 2 * (df_daily['high_prev'] - df_daily['low_prev'])

    pivots_levels = ['PP', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3']
    df_daily = df_daily[pivots_levels]
    main_df = main_df.merge(df_daily, left_index=True, right_index=True, how='left')

    main_df[pivots_levels] = main_df[pivots_levels].ffill()
    
    # Compute ATR:
    main_df["ATR"] = calculate_atr(main_df, ATRperiod)

    #remove Nan values
    cols_to_check = [col for col in main_df.columns if col != 'chikou']
    main_df.dropna(subset=cols_to_check, inplace=True)
    main_df.reset_index(inplace=True)

    return main_df


def sort_by_winrate(item):
    _, dict_values = item
    return dict_values['Winrate [%]']

def sort_by_total_pnl(item):
    _, dict_values = item
    return dict_values['Total return net [%]']

def sort_by_total_pnl_with_fees(item):
    _, dict_values = item
    return dict_values['Total return brut [%]']

def create_winrate_dictionnary(trades_database, sort_option=2, tickSize = 0.25, 
    start_date="2023-03-24 12:00:00", end_date="2025-02-14 12:00:00"):

    winrate_dictionnary = {}

    for id, trade_data in trades_database.items():
        #df, sl, tp, onlyUSSession, smke, timeframes, tc, tenkanCond, slModifiers, fbh, atrRatio = trade_data #,  nbr_of_points, delta_in_ticks, windowForLevels = trade_data
        df, onlyUSSession, timeframes, bracketsModifier, slInTicks, tpInTicks, tpToMoveInTicks, \
        percentHitToMoveTP, nbrTimeMaxMoveTP, sessionHour, stopMethod, nbrTimeMaxPassThroughTenkan, percentSlAlmostHit, slModifierAfterAlmostHit, ratioDistanceKijun, timeTPMovedToClose, calendar_events = trade_data
        if not df.empty:
            df = df[(start_date <= df["entry_date"] ) & (df["entry_date"] <= end_date)]

            loser_entry_price = df.loc[df['profit_from_start(%)']<0, 'entry_price']
            loser_exit_price = df.loc[df['profit_from_start(%)']<0, 'exit_price']
            avg_real_sl_executed = (abs(loser_entry_price-loser_exit_price).mean())/tickSize
            
            winner_entry_price = df.loc[df['profit_from_start(%)']>0, 'entry_price']
            winner_exit_price = df.loc[df['profit_from_start(%)']>0, 'exit_price']
            avg_real_tp_executed = (abs(winner_entry_price-winner_exit_price).mean())/tickSize

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

            winrate_dictionnary[id] = {
                'Winrate [%]': round(winrate, 3), 
                "Total return brut [%]": round(total_return_without_fees_from_start, 2),
                "Total return net [%]": round(total_return_including_fees_from_start, 2),
                # "Avg. gain brut [%]": round(avg_gain_from_start, 2),
                # "Avg. loss brut [%]": round(avg_loss_from_start,2),
                "Avg. gain net [%]": round(avg_gain_including_fees_from_start, 3),
                "Avg. loss net [%]": round(avg_loss_including_fees_from_start,3),
                'Risk ratio': round(avg_real_tp_executed/avg_real_sl_executed, 2), 
                'Nbr Wins/Loss/Breakeven' : (wins, loss, breakevens),
                "Avg. executed TP [Ticks]": round(avg_real_tp_executed, 1),
                "Avg. executed SL [Ticks]": round(avg_real_sl_executed, 1),

                '[SL1, TP1] / [SL2, TP2] [Ticks]': (slInTicks[0],tpInTicks[0], slInTicks[1], tpInTicks[1]),
                # 'TP [Ticks]': (tp[0], tp[1]),
                "Q2 duration (médiane)": quantiles_duration.loc[0.50], 
                "Q3 duration (75%)": quantiles_duration.loc[0.75],
                # 'timeframes': timeframes,
                'bracketsModifier':bracketsModifier,
                "percentHitToMoveTP":percentHitToMoveTP,
                "timeTPMovedToClose":timeTPMovedToClose,
                "slModifierAfterAlmostHit":slModifierAfterAlmostHit,
                "percentSlAlmostHit":percentSlAlmostHit,
                # "PassThrTenkan":nbrTimeMaxPassThroughTenkan,
                # "ratioDistanceKijun":ratioDistanceKijun,
                "tpToMoveInTicks":tpToMoveInTicks,
                "nbrTimeMaxMoveTP":nbrTimeMaxMoveTP,
                "maxLossStreak, avgLossStreak": get_loss_streak_data(df),
                # 'tenkanCond':tenkanAngle,
                # "forbbiden Hours":forbHours,
                # "atrRatioForTp":atrRatioForTp,
                # "atrRatioForSl":atrRatioForSl,
                # "atrSlopeTreshold":atrSlopeTreshold,
                # "maxTimeOutsideProfitZone":maxTimeOutsideProfitZone,
                # "methodForMovingTP":methodForMovingTP,
                # "maxDailyPercentLoss":maxDailyPercentLoss,
                # "maxDailyPercentProfit":maxDailyPercentProfit,
                # "stopMethod": stopMethod,
            # "sessionHour":sessionHour,
                
                #'US_session_only' : onlyUSSession,
                # "calendar_event":calendar_events,
                # 'ticksCrossed': tc,
                # 'rsiVal': rsiVal
                # "patternVerif":pv
                # 'chopValue': chopVal, 
                # 'mta':mta,
                # 'chopPeriod':chopPeriod,
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
    elif sort_option == 3:
        winrate_dictionnary = dict(sorted(winrate_dictionnary.items(), key=sort_by_total_pnl_with_fees))

    return winrate_dictionnary



# Step 1: Identify losing trades (where exit price is less than entry price)
def get_loss_streak_data(tradesData):
    tradesData['is_loss'] = tradesData['exit_price'] < tradesData['entry_price']
    # Step 2: Identify streaks of losing trades
    loss_streaks = []
    current_streak = 0
    for idx, loss in enumerate(tradesData['is_loss']):
        if loss:
            if current_streak == 0:  # This is the start of a new streak
                streak_start_date = tradesData.loc[idx, 'entry_date']
            current_streak += 1
        else:
            if current_streak > 0:  # We reached the end of a losing streak
                streak_end_date = tradesData.loc[idx - 1, 'exit_date']
                loss_streaks.append({
                    'streak_length': current_streak,
                    'start_date': streak_start_date,
                    'end_date': streak_end_date
                })
            current_streak = 0  # Reset streak count

    # Don't forget to add the last streak if it's a losing streak
    if current_streak > 0:
        streak_end_date = tradesData.loc[len(tradesData) - 1, 'exit_date']
        loss_streaks.append({
            'streak_length': current_streak,
            'start_date': streak_start_date,
            'end_date': streak_end_date
        })

    # Step 3: Calculate maximum losing streak and average losing streak
    if loss_streaks:
        max_loss_streak = max(loss_streaks, key=lambda x: x['streak_length'])
        avg_loss_streak = sum([streak['streak_length'] for streak in loss_streaks]) / len(loss_streaks)
    else:
        max_loss_streak = None
        avg_loss_streak = 0

    return max_loss_streak['streak_length'], round(avg_loss_streak, 2)



def return_trade_datas_dataframe(trade_datas_name, sort_option=2, start_date="2023-03-24 12:00:00", end_date="2025-02-14 12:00:00"):
    trades_database = load_object('trade_datas/'+trade_datas_name)
    winrate_dictionnary = create_winrate_dictionnary(trades_database, sort_option=sort_option, start_date=start_date, end_date=end_date)
    return pd.DataFrame.from_dict(winrate_dictionnary, orient='index')

def describe_daily_and_weekly_trade_datas(trade_datas_name, selected_Id=6):
    pathOfData = 'trade_datas/'+trade_datas_name
    trades_database = load_object(pathOfData)
    df_temp =  trades_database[selected_Id][0]
    # Définir 'datetime' comme index pour pouvoir utiliser resample
    df_temp.set_index('entry_date', inplace=True)
    # Resampler les données par semaine (par exemple, la somme des profits par semaine)
    df_weekly = df_temp.resample('W').agg({'profit_including_fees_from_start(%)': ['sum']})
    df_daily = df_temp.resample('D').agg({'profit_including_fees_from_start(%)': ['sum']})
    del df_temp
    print(df_daily.describe(),'\n', df_weekly.describe())


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


def plot_bars_of_profit_for_every_weeks(name, selected_Id):
    pathOfData = "trade_datas/"+name
    trades_database = load_object(pathOfData)
    df_temp =  trades_database[selected_Id][0]
    df_temp['exit_week'] = df_temp['exit_date'].dt.to_period('W')
    result = df_temp.groupby(['exit_week']).agg({'profit_from_start(%)': ['sum']})

    result = pd.DataFrame({
        'week': result['profit_from_start(%)'].index,
        'total_profit': [x[0] for x in result['profit_from_start(%)'].values]
    })
    # Affichage du graphique
    plt.figure(figsize=(16, 10))
    plt.bar(result['week'].astype(str), result['total_profit'], color='skyblue')

    # Ajouter des labels et un titre
    plt.xlabel('Semaine')
    plt.ylabel('Profit Total')
    plt.title('Profit Total par Semaine')

    # Rotation des labels et espacement des étiquettes
    plt.xticks(rotation=45, ha='right', fontsize=8)

    # Espacement des étiquettes (afficher chaque 6ème semaine par exemple)
    plt.xticks(ticks=range(0, len(result), 6))  # Afficher toutes les 6 semaines

    # Affichage du graphique
    plt.tight_layout()
    plt.show()


def get_winrate_by_short_and_long_position(name, selected_Id):
    pathOfData = "trade_datas/"+name
    trades_database = load_object(pathOfData)
    df_temp =  trades_database[selected_Id][0]
    nbr_win_short = df_temp[(df_temp['profit_from_start(%)']>0) & (df_temp['position']==Position.SHORT)]['position'].count()
    nbr_lose_short = df_temp[(df_temp['profit_from_start(%)']<0) & (df_temp['position']==Position.SHORT)]['position'].count()
    nbr_win_long = df_temp[(df_temp['profit_from_start(%)']>0) & (df_temp['position']==Position.LONG)]['position'].count()
    nbr_lose_long = df_temp[(df_temp['profit_from_start(%)']<0) & (df_temp['position']==Position.LONG)]['position'].count()
    print(f'winrate short: {nbr_win_short/(nbr_win_short+nbr_lose_short)}, winrate long: {nbr_win_long/(nbr_win_long+nbr_lose_long)}')


def calculate_atr(df, period=14):
    """
    Calculates the Average True Range (ATR) for a given OHLC dataframe.

    Args:
    - df (pd.DataFrame): The dataframe with columns ['Open', 'High', 'Low', 'Close'].
    - period (int): The period over which to calculate the ATR (default is 14).

    Returns:
    - pd.Series: A Series with the ATR values.
    """
    # Calculate True Range (TR)
    df['Previous Close'] = df['close'].shift(1)  # Previous day's close
    df['TR'] = pd.DataFrame({
        'High-Low': df['high'] - df['low'],
        'High-Previous Close': abs(df['high'] - df['Previous Close']),
        'Low-Previous Close': abs(df['low'] - df['Previous Close'])
    }).max(axis=1)

    # Calculate ATR as the rolling mean of True Range
    df['ATR'] = df['TR'].rolling(window=period).mean()

    return df['ATR']