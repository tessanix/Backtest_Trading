import pandas as pd
# from tqdm import tqdm
from values_definition import Position
from strategies.Strategy import Strategy

def strategyLoop(strategy: Strategy, slInTicks:int, tpInTicks:tuple[int,int], usSession:bool, stopMethod:int, feesPerTrade:float) -> pd.DataFrame:

    CAPITAL = 50_000.0 # constant
    followingSl = slInTicks

    tickValue = 10 #1.25
    tickSize = 0.01 #0.25 # 1 tick = variation of price of 0.25 for SP500
    positionSize = 1 #nbr of contracts

    position = Position.NONE
    entryDate = ""
    entryPrice = 0.0
    tradesData = []
    # maxBar = len(strategy.df_M5) - 1 
    usSessionHour = 16
    allowed_trading_hours_start = 7 if usSession == False else usSessionHour
    allowed_trading_hours_end = 20
    tpInTicksChosen = tpInTicks[0]
    # times_below_breakeven = 0
    # isFirstTradeCandle = False

    # with tqdm(total=maxBar) as pbar:
    for i in strategy.df_M5.index[1:]: 

        currentPrice = strategy.df_M5.loc[i]["close"]
        currentDate = strategy.df_M5.loc[i]["datetime"]
        if currentDate.hour < usSessionHour:
            tpInTicksChosen = tpInTicks[0]
        else:
            tpInTicksChosen = tpInTicks[1]

        if position == Position.NONE:
            if (allowed_trading_hours_start <= currentDate.hour and currentDate.hour < allowed_trading_hours_end):

                position = strategy.checkIfCanEnterPosition(i, tpInTicksChosen)
                entryDate = currentDate
                entryPrice = currentPrice
                # times_below_breakeven = 0
                # isFirstTradeCandle = True
                followingSl = slInTicks

        else:
            # prevPrice = strategy.df_M5.loc[i-1]["close"]
            if position == Position.LONG:
                sl = entryPrice - followingSl*tickSize
                tp = entryPrice + tpInTicksChosen*tickSize

                # if (not isFirstTradeCandle) and (prevPrice <= entryPrice) and (entryPrice < currentPrice):
                #     times_below_breakeven+=1
                    
                if currentPrice <= sl: # LOSE
                    profit = -followingSl*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                        # "times_below_breakeven": times_below_breakeven,
                    })
                    position = Position.NONE

                elif currentPrice >= tp:# WIN
                    profit = tpInTicksChosen*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                        # "times_below_breakeven": times_below_breakeven,
                    })
                    position = Position.NONE

                # elif times_below_breakeven_treshold>0 and times_below_breakeven>=times_below_breakeven_treshold: # and currentPrice >= entryPrice + tpInTicks*tickSize/2: # tp/2
                #     followingSl = 0 # => breakeven
                
                elif strategy.checkIfCanStopLongPosition(i, stopMethod) or currentDate.hour >= 22:
                    profit = (currentPrice-entryPrice)*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                        # "times_below_breakeven": times_below_breakeven,
                    })
                    position = Position.NONE

            elif position == Position.SHORT:
                sl = entryPrice + followingSl*tickSize
                tp = entryPrice - tpInTicksChosen*tickSize

                # if (not isFirstTradeCandle) and (prevPrice >= entryPrice) and (entryPrice > currentPrice):
                #     times_below_breakeven+=1

                if currentPrice >= sl: # LOSE
                    profit = -followingSl*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice,
                        "exit_price": currentPrice,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                        # "times_below_breakeven": times_below_breakeven,
                    })
                    position = Position.NONE

                elif currentPrice <= tp: # WIN
                    profit = tpInTicksChosen*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice,
                        "exit_price": currentPrice, 
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                        # "times_below_breakeven": times_below_breakeven,
                    })
                    position = Position.NONE

                # elif times_below_breakeven_treshold>0 and times_below_breakeven>=times_below_breakeven_treshold: #currentPrice <= entryPrice - tpInTicks*tickSize/2: # tp/2
                #     followingSl = 0 # => breakeven

                elif strategy.checkIfCanStopShortPosition(i, stopMethod) or currentDate.hour >= 22:
                    profit = (entryPrice-currentPrice)*tickValue*positionSize
                    tradesData.append({
                        "entry_date": entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": entryPrice, 
                        "exit_price": currentPrice, 
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(profit-feesPerTrade)/CAPITAL,
                        "profit_from_start(%)":100*profit/CAPITAL,
                        # "times_below_breakeven": times_below_breakeven,
                    })
                    position = Position.NONE
            # isFirstTradeCandle = False

            # pbar.update(1)

    return pd.DataFrame(tradesData)
