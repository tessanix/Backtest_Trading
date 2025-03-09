import pandas as pd
from values_definition import Position
from strategies.Strategy import Strategy

def strategyLoop(strategy: Strategy, instrument:str, usSession:bool, stopMethod:int, feesPerTrade:float, positionSize:int=1,
                forbiddenHours:list=[], slModifiers:list[list]=[[0.5, 0.15]], atrRatio:list=(1.5, 1.2)):
    
    CAPITAL = 50_000.0 # constant
    withCrossKijunExit = False if stopMethod == 0 else True

    tickValue, tickSize = 0.0, 0.0

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
    entryDate = ""
    entryPrice = 0.0
    tradesData = []
    usSessionHour = 16
    allowed_trading_hours_start = 7 if usSession == False else usSessionHour
    allowed_trading_hours_end = 20
    isFirstTradeCandle = False

    tpInTicks          = strategy.df.loc[0]['ATR']*atrRatio[0]/tickSize
    followingSlinTicks = strategy.df.loc[0]['ATR']*atrRatio[1]/tickSize
    sl = 0.0

    for i in strategy.df.index[1:]: 

        currentPrice = strategy.df.loc[i]["close"]
        currentDate = strategy.df.loc[i]["datetime"]
        #tpInTicks = tpInTicks[0] if currentDate.hour < usSessionHour else tpInTicks[1]

        if position == Position.NONE:
            if (allowed_trading_hours_start <= currentDate.hour and currentDate.hour < allowed_trading_hours_end and currentDate.hour not in forbiddenHours):

                position = strategy.checkIfCanEnterPosition(i, tpInTicks, tickSize)
                entryDate = currentDate
                entryPrice = currentPrice
                isFirstTradeCandle = True
                tpInTicks          = strategy.df.loc[i]['ATR']*atrRatio[0]/tickSize #if currentDate.hour < usSessionHour else strategy.df.loc[i]['ATR']*1.2/tickSize
                followingSlinTicks = strategy.df.loc[i]['ATR']*atrRatio[1]/tickSize #slInTicks

        else:
            if position == Position.LONG:

                tp = entryPrice + tpInTicks*tickSize
                if isFirstTradeCandle:
                    sl = entryPrice - followingSlinTicks*tickSize 
                
                if len(slModifiers)>0: 
                    if(strategy.df.loc[i, "high"]-entryPrice)/tickSize>slModifiers[0][0]*tpInTicks:
                        followingSlinTicks = tpInTicks*slModifiers[0][1]
                        sl = entryPrice+followingSlinTicks*tickSize      
        
                if len(slModifiers)>1: 
                    if(strategy.df.loc[i, "high"]-entryPrice)/tickSize>slModifiers[1][0]*tpInTicks:
                        followingSlinTicks = tpInTicks*slModifiers[1][1]
                        sl = entryPrice+followingSlinTicks*tickSize    
  
                if currentPrice <= sl: # LOSE
                    profit = -followingSlinTicks*tickValue*positionSize if sl < entryPrice else followingSlinTicks*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                    })
                    position = Position.NONE

                elif currentPrice >= tp:# WIN
                    profit = tpInTicks*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                    })
                    position = Position.NONE

 
                elif (withCrossKijunExit and entryPrice < currentPrice and strategy.checkIfCanStopLongPosition(i, stopMethod)) \
                    or (currentDate.hour >= 22):
                    profit = ((currentPrice-entryPrice)/tickSize)*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                    })
                    position = Position.NONE
            ################################## CHECK SHORT ###################################################################################
            elif position == Position.SHORT:

                tp = entryPrice - tpInTicks*tickSize
                if isFirstTradeCandle:
                    sl = entryPrice + followingSlinTicks*tickSize

                if len(slModifiers)>0: 
                    if(entryPrice-strategy.df.loc[i, "low"])/tickSize>slModifiers[0][0]*tpInTicks:
                        followingSlinTicks = tpInTicks*slModifiers[0][1]
                        sl = entryPrice-followingSlinTicks*tickSize       

                if len(slModifiers)>1:
                    if (entryPrice-strategy.df.loc[i, "low"])/tickSize>slModifiers[1][0]*tpInTicks:
                        followingSlinTicks = tpInTicks*slModifiers[1][1]
                        sl = entryPrice-followingSlinTicks*tickSize        

                if currentPrice >= sl: # LOSE
                    profit = -followingSlinTicks*tickValue*positionSize if sl > entryPrice else followingSlinTicks*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice,
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                    })
                    position = Position.NONE

                elif currentPrice <= tp: # WIN
                    profit = tpInTicks*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice,
                        "exit_price": currentPrice, 
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                    })
                    position = Position.NONE


                elif (withCrossKijunExit and entryPrice > currentPrice and strategy.checkIfCanStopShortPosition(i, stopMethod)) \
                    or (currentDate.hour >= 22):
                    profit = ((entryPrice-currentPrice)/tickSize)*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice, 
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                    })
                    position = Position.NONE
            isFirstTradeCandle = False

    return pd.DataFrame(tradesData)
