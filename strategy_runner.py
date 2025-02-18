import pandas as pd
from tqdm import tqdm
from strategies.Strategy import Strategy
from values_definition import Position

def strategyLoop(strategy: Strategy, slInTicks:int, tpInTicks:int, usSession:bool, times_below_before_breakeven:int) -> pd.DataFrame:

    CAPITAL = 50_000.0 # constant
    followingSl = slInTicks

    tickValue = 1.25
    tickSize = 0.25 # 1 tick = variation of price of 0.25 for SP500
    positionSize = 3 #nbr of contracts

    position = Position.NONE
    entryDate = ""
    entryPrice = 0.0
    tradesData = []
    maxBar = len(strategy.df_M5) - 1 
    allowed_trading_hours_start = 8 if usSession == False else 16
    allowed_trading_hours_end = 21
    times_below_breakeven = 0
    isFirstTradeCandle = False

    with tqdm(total=maxBar) as pbar:
        for i in strategy.df_M5.index[1:]: 
  
            currentPrice = strategy.df_M5.loc[i]["close"]
            currentDate = strategy.df_M5.loc[i]["datetime"]

            if position is Position.NONE:
                if (allowed_trading_hours_start <= currentDate.hour and currentDate.hour < allowed_trading_hours_end):
                    position = strategy.checkIfCanEnterPosition(i, tpInTicks)
                    entryDate = currentDate
                    entryPrice = currentPrice
                    times_below_breakeven = 0
                    isFirstTradeCandle = True
                    followingSl = slInTicks

            else:
                prevPrice = strategy.df_M5.loc[i-1]["close"]
                if position is Position.LONG:
                    sl = entryPrice - followingSl*tickSize
                    tp = entryPrice + tpInTicks*tickSize

                    if (not isFirstTradeCandle) and (prevPrice <= entryPrice) and (entryPrice < currentPrice):
                        times_below_breakeven+=1
                        
                    if currentPrice <= sl: # LOSE
                        profit = -followingSl*tickValue*positionSize
                        tradesData.append({
                            "entry_date": entryDate, 
                            "exit_date": strategy.df_M5.loc[i]["datetime"], 
                            "entry_price": entryPrice, 
                            "position" : position,
                            # "profit": profit,
                            "profit_from_start(%)":(profit/CAPITAL)*100,
                            "times_below_breakeven": times_below_breakeven,
                        })
                        position = Position.NONE

                    elif currentPrice >= tp:# WIN
                        profit = tpInTicks*tickValue*positionSize
                        tradesData.append({
                            "entry_date": entryDate, 
                            "exit_date": strategy.df_M5.loc[i]["datetime"], 
                            "entry_price": entryPrice, 
                            "position" : position,
                            # "profit": profit,
                            "profit_from_start(%)":(profit/CAPITAL)*100,
                            "times_below_breakeven": times_below_breakeven,
                        })
                        position = Position.NONE

                    elif times_below_before_breakeven>0 and times_below_breakeven>=times_below_before_breakeven: # and currentPrice >= entryPrice + tpInTicks*tickSize/2: # tp/2
                        followingSl = 0 # => breakeven
                    
                    elif currentDate.hour >= 22:
                        profit = (currentPrice-entryPrice)*tickValue*positionSize
                        tradesData.append({
                            "entry_date": entryDate, 
                            "exit_date": strategy.df_M5.loc[i]["datetime"], 
                            "entry_price": entryPrice, 
                            "position" : position,
                            # "profit": profit,
                            "profit_from_start(%)":(profit/CAPITAL)*100,
                            "times_below_breakeven": times_below_breakeven,
                        })
                        position = Position.NONE

                elif position is Position.SHORT:
                    sl = entryPrice + followingSl*tickSize
                    tp = entryPrice - tpInTicks*tickSize

                    if (not isFirstTradeCandle) and (prevPrice >= entryPrice) and (entryPrice > currentPrice):
                        times_below_breakeven+=1

                    if currentPrice >= sl: # LOSE
                        profit = -followingSl*tickValue*positionSize
                        tradesData.append({
                            "entry_date": entryDate, 
                            "exit_date": strategy.df_M5.loc[i]["datetime"], 
                            "entry_price": entryPrice, 
                            "position" : position,
                            # "profit": profit,
                            "profit_from_start(%)":(profit/CAPITAL)*100,
                            "times_below_breakeven": times_below_breakeven,
                        })
                        position = Position.NONE

                    elif currentPrice <= tp: # WIN
                        profit = tpInTicks*tickValue*positionSize
                        tradesData.append({
                            "entry_date": entryDate, 
                            "exit_date": strategy.df_M5.loc[i]["datetime"], 
                            "entry_price": entryPrice, 
                            "position" : position,
                            # "profit": profit,
                            "profit_from_start(%)":(profit/CAPITAL)*100,
                            "times_below_breakeven": times_below_breakeven,
                        })
                        position = Position.NONE

                    elif times_below_before_breakeven>0 and times_below_breakeven>=times_below_before_breakeven: #currentPrice <= entryPrice - tpInTicks*tickSize/2: # tp/2
                        followingSl = 0 # => breakeven

                    elif currentDate.hour >= 22:
                        profit = (entryPrice-currentPrice)*tickValue*positionSize
                        tradesData.append({
                            "entry_date": entryDate, 
                            "exit_date": strategy.df_M5.loc[i]["datetime"], 
                            "entry_price": entryPrice, 
                            "position" : position,
                            # "profit": profit,
                            "profit_from_start(%)":(profit/CAPITAL)*100,
                            "times_below_breakeven": times_below_breakeven,
                        })
                        position = Position.NONE
                isFirstTradeCandle = False

            pbar.update(1)

    return pd.DataFrame(tradesData)
