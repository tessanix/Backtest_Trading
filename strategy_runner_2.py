import pandas as pd
from values_definition import Position, Result
from strategies.Strategy import Strategy
from financial_functions import ( profit_for_long_stop_condition_hit, 
                                profit_for_short_stop_condition_hit, 
                                profit_for_sl_hit, 
                                profit_for_tp_hit )

def strategyLoop(strategy: Strategy, instrument:str, usSession:bool, stopMethod:int, feesPerTrade:float, positionSize:int=1,
                forbiddenHours:list=[], slModifiers:list[list]=[[0.5, 0.15]], atrRatio:list=[1.5, 1.2]):
    
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
        # currentOpen = strategy.df.loc[i, "open"]
        currentHigh = strategy.df.loc[i, "high"]
        currentLow = strategy.df.loc[i, "low"]

        currentDate = strategy.df.loc[i]["datetime"]
        
        high_before_low = strategy.df.loc[i, "high_before_low"] if 'high_before_low' in strategy.df.columns else False

        if position == Position.NONE:
            if (allowed_trading_hours_start <= currentDate.hour and currentDate.hour < allowed_trading_hours_end and currentDate.hour not in forbiddenHours):

                tpInTicks          = strategy.df.loc[i, 'ATR']*atrRatio[0]/tickSize
                followingSlinTicks = strategy.df.loc[i, 'ATR']*atrRatio[1]/tickSize
                position           = strategy.checkIfCanEnterPosition(i, tpInTicks, tickSize)
                entryDate          = currentDate
                entryPrice         = currentClose #currentPrice
                isFirstTradeCandle = True
                trade_is_done      = False
        else:
            ################################################### LONG ###################################################
            if position == Position.LONG:

                tp = entryPrice + tpInTicks*tickSize
                if isFirstTradeCandle:
                    sl = entryPrice - followingSlinTicks*tickSize 
                
                if len(slModifiers)>0 and (currentHigh-entryPrice)/tickSize>slModifiers[0][0]*tpInTicks:
                    followingSlinTicks = tpInTicks*slModifiers[0][1]
                    sl = entryPrice+followingSlinTicks*tickSize      
    
                if len(slModifiers)>1 and (currentHigh-entryPrice)/tickSize>slModifiers[1][0]*tpInTicks:
                    followingSlinTicks = tpInTicks*slModifiers[1][1]
                    sl = entryPrice+followingSlinTicks*tickSize    

                if high_before_low:
                    if currentHigh >= tp:
                        profit = profit_for_tp_hit(tpInTicks, tickValue, positionSize)
                        exit_price = tp
                        trade_is_done = True
                    
                    elif currentLow <= sl:
                        result = Result.WIN  if entryPrice < sl else Result.LOSS
                        profit = profit_for_sl_hit(followingSlinTicks, tickValue, positionSize, result)
                        exit_price = sl
                        trade_is_done = True
                else:
                    if currentLow <= sl:
                        result = Result.WIN  if entryPrice < sl else Result.LOSS
                        profit = profit_for_sl_hit(followingSlinTicks, tickValue, positionSize, result)
                        exit_price = sl
                        trade_is_done = True

                    elif currentHigh >= tp:
                        profit = profit_for_tp_hit(tpInTicks, tickValue, positionSize)
                        exit_price = tp
                        trade_is_done = True

                if not trade_is_done and \
                    ((withCrossKijunExit and entryPrice < currentClose and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                    or (currentDate.hour >= 22)):
                    profit = profit_for_long_stop_condition_hit(currentClose, entryPrice, tickSize, tickValue, positionSize)
                    exit_price = entryPrice + (currentClose-entryPrice)
                    trade_is_done = True

            ################################################### SHORT ###################################################
            elif position == Position.SHORT:

                tp = entryPrice - tpInTicks*tickSize
                if isFirstTradeCandle:
                    sl = entryPrice + followingSlinTicks*tickSize

                if len(slModifiers)>0 and (entryPrice-currentLow)/tickSize>slModifiers[0][0]*tpInTicks:
                    followingSlinTicks = tpInTicks*slModifiers[0][1]
                    sl = entryPrice-followingSlinTicks*tickSize       

                if len(slModifiers)>1 and (entryPrice-currentLow)/tickSize>slModifiers[1][0]*tpInTicks:
                    followingSlinTicks = tpInTicks*slModifiers[1][1]
                    sl = entryPrice-followingSlinTicks*tickSize        

                if high_before_low:
                    if currentHigh >= sl:
                        result = Result.WIN  if entryPrice > sl else Result.LOSS
                        profit = profit_for_sl_hit(followingSlinTicks, tickValue, positionSize, result)
                        exit_price = sl
                        trade_is_done = True

                    elif currentLow <= tp:
                        profit = profit_for_tp_hit(tpInTicks, tickValue, positionSize)
                        exit_price = tp
                        trade_is_done = True

                else:
                    if currentLow <= tp:
                        profit = profit_for_tp_hit(tpInTicks, tickValue, positionSize)
                        exit_price = tp
                        trade_is_done = True

                    elif currentHigh >= sl:
                        result = Result.WIN  if entryPrice > sl else Result.LOSS
                        profit = profit_for_sl_hit(followingSlinTicks, tickValue, positionSize, result)
                        exit_price = sl
                        trade_is_done = True

                if not trade_is_done and \
                    ((withCrossKijunExit and entryPrice > currentClose and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                    or (currentDate.hour >= 22)):
                    profit = profit_for_short_stop_condition_hit(currentClose, entryPrice, tickSize, tickValue, positionSize)
                    exit_price = entryPrice - (entryPrice-currentClose)
                    trade_is_done = True

            isFirstTradeCandle = False

            if trade_is_done:
                tradesData.append({
                    "entry_date": entryDate, 
                    "exit_date": currentDate, 
                    "entry_price": entryPrice, 
                    "exit_price": exit_price,
                    "position" : position,
                    "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                    "profit_from_start(%)":100*profit/CAPITAL,
                }) 
                position = Position.NONE   

    return pd.DataFrame(tradesData)
