import pandas as pd
from values_definition import Position
from strategies.Strategy import Strategy
from positionManager import PositionManager
# from pattern_verification import verify_bull_reversal_doji, verify_bear_reversal_doji
from datetime import timedelta

def strategyLoop(strategy: Strategy, us_calendar_df:pd.DataFrame, instrument:str, usSession:bool, stopMethod:int, feesPerTrade:float, positionSize:int=1,
                forbiddenHours:list=[], tpInTicksInitial:list=[25,70], slInTicksInitial:int=[15,40], slModifiers:list[list]=[[0.5, 0.15]]): #atrRatio:list=[1.5, 1.2]):
    
    CAPITAL = 50_000.0 # constant
    withCrossKijunExit = False if stopMethod == 0 else True

    if instrument == "MES":
        tickValue, tickSize = 1.25, 0.25
    elif instrument == "ES":
        tickValue, tickSize = 12.5, 0.25
    elif instrument == "MNQ":
        tickValue, tickSize = 0.5, 0.25
    elif instrument == "NQ":
        tickValue, tickSize = 5.0, 0.25
    elif instrument == "MCL":
        tickValue, tickSize = 1.0, 0.01
    elif instrument == "CL":
        tickValue, tickSize = 10.0, 0.01
    else: 
        return None

    position = Position.NONE
    tradesData = []
    usSessionHour = 16
    allowed_trading_hours_start = 7 if usSession == False else usSessionHour
    allowed_trading_hours_end = 20

    for i in strategy.df.index[1:]: 

        currentClose = strategy.df.loc[i, "close"]
        currentOpen = strategy.df.loc[i, "open"]
        currentHigh = strategy.df.loc[i, "high"]
        currentLow = strategy.df.loc[i, "low"]
        currentDate = strategy.df.loc[i]["datetime"]
        
        high_before_low = strategy.df.loc[i, "high_before_low"] if 'high_before_low' in strategy.df.columns else False

        if position == Position.NONE:
            us_calendar_df = us_calendar_df[us_calendar_df["datetime"]>=currentDate]
            if len(us_calendar_df) > 0:
                condition = (currentDate < us_calendar_df.iloc[0]["datetime"] - timedelta(minutes=20) or us_calendar_df.iloc[0]["datetime"] + timedelta(minutes=10) < currentDate)
            else:
                condition = True
            if (allowed_trading_hours_start <= currentDate.hour and currentDate.hour < allowed_trading_hours_end 
                and currentDate.hour not in forbiddenHours and condition):

                followingSlinTicks = slInTicksInitial[0] if currentDate.hour < usSessionHour else slInTicksInitial[1]#strategy.df.loc[i, 'ATR']*atrRatio[1]/tickSize
                tpInTicks          = tpInTicksInitial[0] if currentDate.hour < usSessionHour else tpInTicksInitial[1]  #strategy.df.loc[i, 'ATR']*atrRatio[0]/tickSize
                
                position           = strategy.checkIfCanEnterPosition(i, tpInTicks, tickSize)
                entryDate          = currentDate
                entryPrice         = currentClose

                if position != Position.NONE:
                    tp = entryPrice + tpInTicks*tickSize if position == Position.LONG else entryPrice - tpInTicks*tickSize
                    sl = entryPrice - followingSlinTicks*tickSize if position == Position.LONG else entryPrice + followingSlinTicks*tickSize
                    posManager = PositionManager(followingSlinTicks, tpInTicks, tickValue, tickSize, 
                                                 positionSize, entryPrice, sl, tp, slModifiers, trade_is_done=False)
        else:
            ################################################### LONG ###################################################
            if position == Position.LONG:

                if high_before_low:
                    posManager.moveStopLossIfLevelHitDuringLongPosition(currentHigh=currentHigh)
                    posManager.checkTargetProfitHitDuringLongPosition(currentHigh=currentHigh)
                    posManager.checkStopLossHitDuringLongPosition(currentLow=currentLow)
                else:
                    posManager.checkStopLossHitDuringLongPosition(currentLow=currentLow)
                    posManager.moveStopLossIfLevelHitDuringLongPosition(currentHigh=currentHigh)
                    posManager.checkTargetProfitHitDuringLongPosition(currentHigh=currentHigh)

                if not posManager.trade_is_done and \
                    ((withCrossKijunExit and entryPrice < currentClose and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                    or (currentDate.hour >= 22)
                    # or verify_bear_reversal_doji(currentClose, currentOpen, currentHigh, x=xRatio)
                    ):
                    posManager.profit = posManager.profit_for_long_stop_condition_hit(currentClose)
                    posManager.exit_price = currentClose
                    posManager.trade_is_done = True

            ################################################### SHORT ###################################################
            elif position == Position.SHORT:

                if high_before_low:
                    posManager.checkStopLossHitDuringShortPosition(currentHigh=currentHigh)
                    posManager.moveStopLossIfLevelHitDuringShortPosition(currentLow=currentLow)
                    posManager.checkTargetProfitHitDuringShortPosition(currentLow=currentLow)
                else:
                    posManager.moveStopLossIfLevelHitDuringShortPosition(currentLow=currentLow)
                    posManager.checkTargetProfitHitDuringShortPosition(currentLow=currentLow)
                    posManager.checkStopLossHitDuringShortPosition(currentHigh=currentHigh)

                if not posManager.trade_is_done and \
                    ((withCrossKijunExit and entryPrice > currentClose and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                    or (currentDate.hour >= 22)
                    # or verify_bull_reversal_doji(currentClose, currentOpen, currentLow, x=xRatio)
                    ):
                    posManager.profit = posManager.profit_for_short_stop_condition_hit(currentClose)
                    posManager.exit_price = currentClose
                    posManager.trade_is_done = True

            if posManager.trade_is_done:
                tradesData.append({
                    "entry_date": entryDate, 
                    "exit_date": currentDate, 
                    "entry_price": posManager.entryPrice, 
                    "exit_price": posManager.exit_price,
                    "position" : position,
                    "profit_including_fees_from_start(%)": 100*(posManager.profit-feesPerTrade)/CAPITAL,
                    "profit_from_start(%)":100*posManager.profit/CAPITAL,
                }) 
                del posManager
                position = Position.NONE   

    return pd.DataFrame(tradesData)
