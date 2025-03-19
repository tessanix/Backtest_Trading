import pandas as pd
from datetime import timedelta
from values_definition import Position
from strategies.Strategy import Strategy
from positionManager import PositionManager
from pattern_verification import verify_bull_reversal_doji, verify_bear_reversal_doji

def strategyLoop(strategy: Strategy, us_calendar_df:pd.DataFrame|None, instrument:str, usSession:bool, stopMethod:int, feesPerTrade:float, positionSize:int=1,
                forbiddenHours:list=[], tpInTicksInitial:list=[25,70], slInTicksInitial:int=[15,40], bracketsModifier:list[list]=[[0.5, 0.15]], 
                tpToMoveInTicks:float=5, percentHitToMoveTP:float=0.9, nbrTimeMaxMoveTP:int=2, usSessionHour:int=16, dojiRatio:float=3.0): #, methodForMovingTP:int=1): # atrRatioForTp:float=0, atrRatioForSl:float=0, atrSlopeTreshold:float=0.5,
    
    INITIAL_CAPITAL = 50_000.0 # constant
    # actual_capital = INITIAL_CAPITAL
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
    allowed_trading_hours_start = 7 if usSession == False else usSessionHour
    allowed_trading_hours_end = 20

    for i in strategy.df.index[1:]: 
        
        currentClose = strategy.df.loc[i, "close"]
        currentHigh = strategy.df.loc[i, "high"]
        currentLow = strategy.df.loc[i, "low"]
        currentDate = strategy.df.loc[i]["datetime"]
        
        high_before_low = strategy.df.loc[i, "high_before_low"] if 'high_before_low' in strategy.df.columns else False

        if position == Position.NONE:

            if us_calendar_df is not None:
                us_calendar_df = us_calendar_df[us_calendar_df["datetime"]>=currentDate]
                if len(us_calendar_df) > 0:
                    condition = (currentDate < us_calendar_df.iloc[0]["datetime"] - timedelta(minutes=20) or us_calendar_df.iloc[0]["datetime"] + timedelta(minutes=10) < currentDate)
                else:
                    condition = True
            else:
                condition = True

            if (allowed_trading_hours_start <= currentDate.hour and currentDate.hour < allowed_trading_hours_end 
                and currentDate.hour not in forbiddenHours and condition):

                followingSlinTicks = slInTicksInitial[0] if currentDate.hour < usSessionHour else slInTicksInitial[1]
                tpInTicks          = tpInTicksInitial[0] if currentDate.hour < usSessionHour else tpInTicksInitial[1] 
               
                position   = strategy.checkIfCanEnterPosition(i, tpInTicks, tickSize)
                entryDate  = currentDate
                entryPrice = currentClose

                if position != Position.NONE:
                    tp = entryPrice + tpInTicks*tickSize if position == Position.LONG else entryPrice - tpInTicks*tickSize
                    sl = entryPrice - followingSlinTicks*tickSize if position == Position.LONG else entryPrice + followingSlinTicks*tickSize
                    posManager = PositionManager(followingSlinTicks, tpInTicks, tickValue, tickSize, positionSize, entryPrice, 
                                                sl, tp, bracketsModifier, tpToMoveInTicks, percentHitToMoveTP, nbrTimeMaxMoveTP, trade_is_done=False) #atrSlopeTreshold
        else:
            #currentAtrSlope = strategy.df.loc[i, "atr_slope_in_percent"]
            currentOpen = strategy.df.loc[i, "open"]
            currentTenkan = strategy.df.loc[i, "tenkan"]
            ################################################### LONG ###################################################
            if position == Position.LONG:

                if high_before_low:
                    posManager.moveStopLossIfLevelHitDuringLongPosition(currentHigh=currentHigh)
                    posManager.moveTragetProfitIfLevelHitDuringLongPosition(currentClose, currentOpen, currentHigh, currentTenkan)
                    posManager.checkTargetProfitHitDuringLongPosition(currentHigh=currentHigh)
                    posManager.checkStopLossHitDuringLongPosition(currentLow=currentLow)
                else:
                    posManager.checkStopLossHitDuringLongPosition(currentLow=currentLow)
                    posManager.moveStopLossIfLevelHitDuringLongPosition(currentHigh=currentHigh)
                    posManager.moveTragetProfitIfLevelHitDuringLongPosition(currentClose, currentOpen, currentHigh, currentTenkan)
                    posManager.checkTargetProfitHitDuringLongPosition(currentHigh=currentHigh)

                if not posManager.trade_is_done and \
                    ((withCrossKijunExit and entryPrice < currentClose and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                      or (currentDate.hour >= 22)
                      or verify_bear_reversal_doji(currentClose, currentOpen, currentHigh, dojiRatio=dojiRatio)
                    ):
                    posManager.profit = posManager.profit_for_long_stop_condition_hit(currentClose)
                    posManager.exit_price = currentClose
                    posManager.trade_is_done = True

            ################################################### SHORT ###################################################
            elif position == Position.SHORT:

                if high_before_low:
                    posManager.checkStopLossHitDuringShortPosition(currentHigh=currentHigh)
                    posManager.moveStopLossIfLevelHitDuringShortPosition(currentLow=currentLow)
                    posManager.moveTragetProfitIfLevelHitDuringShortPosition(currentClose, currentOpen, currentLow, currentTenkan)
                    posManager.checkTargetProfitHitDuringShortPosition(currentLow=currentLow)
                else:
                    posManager.moveStopLossIfLevelHitDuringShortPosition(currentLow=currentLow)
                    posManager.moveTragetProfitIfLevelHitDuringShortPosition(currentClose, currentOpen, currentLow, currentTenkan)
                    posManager.checkTargetProfitHitDuringShortPosition(currentLow=currentLow)
                    posManager.checkStopLossHitDuringShortPosition(currentHigh=currentHigh)

                if not posManager.trade_is_done and \
                    ((withCrossKijunExit and entryPrice > currentClose and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                      or (currentDate.hour >= 22)
                      or verify_bull_reversal_doji(currentClose, currentOpen, currentLow, dojiRatio=dojiRatio)
                    ):
                    posManager.profit = posManager.profit_for_short_stop_condition_hit(currentClose)
                    posManager.exit_price = currentClose
                    posManager.trade_is_done = True

            if posManager.trade_is_done:
                # actual_capital += posManager.profit
                # current_profit_in_percent =  100*posManager.profit/actual_capital
                # if current_profit_in_percent > 0:
                #     todayPercentProfit += current_profit_in_percent
                # else:
                #     todayPercentLoss += current_profit_in_percent
                tradesData.append({
                    "entry_date": entryDate, 
                    "exit_date": currentDate, 
                    "entry_price": posManager.entryPrice, 
                    "exit_price": posManager.exit_price,
                    "position" : position,
                    "profit_including_fees_from_start(%)": 100*(posManager.profit-feesPerTrade)/INITIAL_CAPITAL,
                    "profit_from_start(%)":100*posManager.profit/INITIAL_CAPITAL,
                }) 
                del posManager
                position = Position.NONE   

    return pd.DataFrame(tradesData)
