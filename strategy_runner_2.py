import pandas as pd
from datetime import timedelta
from values_definition import Position
from strategies.Strategy import Strategy
from positionManager import PositionManager

class Backtest():
    
    def __init__(self, strategy: Strategy, us_calendar_df:pd.DataFrame|None, instrument:str, usSession:bool, feesPerTrade:float, positionSize:int=1,
                    forbiddenHours:list=[], tpInTicksInitial:list=[25,70], slInTicksInitial:int=[15,40], bracketsModifier:list[list]=[[0.5, 0.15]], 
                    tpToMoveInTicks:float=5, percentHitToMoveTP:float=0.9, nbrTimeMaxMoveTP:int=2, usSessionHour:int=16, stopMethod:int=2, 
                    maxTimeOutsideProfitZone:int=30, nbrTimeMaxPassThroughTenkan:int=2, percentSlAlmostHit:float=0.75, slModifierAfterAlmostHit:float=0.1, timeTPMovedToClose:int=1): #, methodForMovingTP:int=1): # atrRatioForTp:float=0, atrRatioForSl:float=0, atrSlopeTreshold:float=0.5,
        
        self.INITIAL_CAPITAL = 50_000.0 # constant

        if instrument == "MES":
            self.tickValue, self.tickSize = 1.25, 0.25
        elif instrument == "ES":
            self.tickValue, self.tickSize = 12.5, 0.25
        elif instrument == "MNQ":
            self.tickValue, self.tickSize = 0.5, 0.25
        elif instrument == "NQ":
            self.tickValue, self.tickSize = 5.0, 0.25
        elif instrument == "MCL":
            self.tickValue, self.tickSize = 1.0, 0.01
        elif instrument == "CL":
            self.tickValue, self.tickSize = 10.0, 0.01
        else: 
            return None
        
        self.strategy = strategy
        self.feesPerTrade = feesPerTrade
        self.us_calendar_df = us_calendar_df
        self.forbiddenHours = forbiddenHours
        self.slInTicksInitial = slInTicksInitial
        self.tpInTicksInitial = tpInTicksInitial

        self.allowed_trading_hours_start = 7 if usSession == False else usSessionHour
        self.allowed_trading_hours_end = 21
        self.posManager = PositionManager(self.tickValue, self.tickSize, positionSize, bracketsModifier, tpToMoveInTicks, 
                            percentHitToMoveTP, nbrTimeMaxMoveTP, nbrTimeMaxPassThroughTenkan, percentSlAlmostHit, slModifierAfterAlmostHit, timeTPMovedToClose) #maxTimeOutsideProfitZone,
    
    def checkCanEnterPos(self, i, currentDate, currentClose, atr_ratio):
        if self.us_calendar_df is not None:
            self.us_calendar_df = self.us_calendar_df[self.us_calendar_df["datetime"]>=currentDate]
            if len(self.us_calendar_df) > 0:
                condition = (currentDate < self.us_calendar_df.iloc[0]["datetime"] - timedelta(minutes=20) or self.us_calendar_df.iloc[0]["datetime"] + timedelta(minutes=10) < currentDate)
            else:
                condition = True
        else:
            condition = True

        if (self.allowed_trading_hours_start <= currentDate.hour and currentDate.hour < self.allowed_trading_hours_end 
            and currentDate.hour not in self.forbiddenHours and condition):

            # isUsSession = currentDate.hour >= usSessionHour
            # followingSlinTicks = slInTicksInitial[1] if isUsSession else slInTicksInitial[0]
            # tpInTicks          = tpInTicksInitial[1] if isUsSession else tpInTicksInitial[0] 

            followingSlinTicks = self.slInTicksInitial[0]*atr_ratio 
            tpInTicks          = self.tpInTicksInitial[0]*atr_ratio 
        
            position   = self.strategy.checkIfCanEnterPosition(i, tpInTicks, self.tickSize)
            entryDate  = currentDate
            entryPrice = currentClose

            if position == Position.LONG:
                tp = entryPrice + tpInTicks*self.tickSize 
                sl = entryPrice - followingSlinTicks*self.tickSize 
                self.posManager.set_new_trade_attributes(entryDate, followingSlinTicks, tpInTicks, entryPrice, sl, tp)
                
            elif position == Position.SHORT:
                tp =  entryPrice - tpInTicks*self.tickSize
                sl = entryPrice + followingSlinTicks*self.tickSize
                self.posManager.set_new_trade_attributes(entryDate, followingSlinTicks, tpInTicks, entryPrice, sl, tp)

            return position
        else:
            return Position.NONE
            

    def strategyLoop(self):
        position = Position.NONE
        tradesData = []
        for i in self.strategy.df.index[1+25:]: 
            
            currentClose = self.strategy.df.loc[i, "close"]
            currentHigh = self.strategy.df.loc[i, "high"]
            currentLow = self.strategy.df.loc[i, "low"]
            currentDate = self.strategy.df.loc[i]["datetime"]
            atr_ratio = self.strategy.df.loc[i, "ATR"]/self.tickSize
            high_before_low = self.strategy.df.loc[i, "high_before_low"] #if 'high_before_low' in strategy.df.columns else False

            if position == Position.NONE:
                position = self.checkCanEnterPos(i, currentDate, currentClose, atr_ratio)
           
            else:
                currentOpen = self.strategy.df.loc[i, "open"]
                currentTenkan = self.strategy.df.loc[i, "tenkan"]
                # prevClose = strategy.df.loc[i-1, "close"]
                ################################################### LONG ###################################################
                if position == Position.LONG:

                    if high_before_low:
                        self.posManager.moveStopLossIfLevelHitDuringLongPosition(currentHigh=currentHigh)
                        self.posManager.checkTargetProfitHitDuringLongPosition(currentHigh=currentHigh)
                        self.posManager.checkStopLossHitDuringLongPosition(currentLow=currentLow)
                    else:
                        self.posManager.checkStopLossHitDuringLongPosition(currentLow=currentLow)
                        self.posManager.moveStopLossIfLevelHitDuringLongPosition(currentHigh=currentHigh)
                        self.posManager.checkTargetProfitHitDuringLongPosition(currentHigh=currentHigh)

                    self.posManager.moveStopLossIfAlmostHitDuringLongPosition(currentClose)
                    self.posManager.checkTenkanPassThroughDuingLongPosition(currentClose, currentOpen, currentTenkan)
                    self.posManager.moveTragetProfitIfLevelHitDuringLongPosition(currentHigh=currentHigh, currentClose=currentClose, atr_ratio=atr_ratio) #, currentOpen=currentOpen, currentTenkan=currentTenkan)

                    if not self.posManager.trade_is_done and ( 
                    # self.posManager.checkIfCanExitLongPosition(currentOpen, currentClose, current_kijun=strategy.df.loc[i, "kijun"])
                    #strategy.checkIfCanStopLongPosition(i, entryPrice=entryPrice, closePrice=currentClose, method=stopMethod)
                    # self.posManager.checkToMuchTimeInNoProfitZoneDuringLong(currentClose, prevClose, currentDate)
                    currentDate.hour >= 22):
                        self.posManager.long_stop_condition_hit(currentClose)            

                ################################################### SHORT ###################################################
                elif position == Position.SHORT:

                    if high_before_low:
                        self.posManager.checkStopLossHitDuringShortPosition(currentHigh=currentHigh)
                        self.posManager.moveStopLossIfLevelHitDuringShortPosition(currentLow=currentLow)
                        self.posManager.checkTargetProfitHitDuringShortPosition(currentLow=currentLow)
                    else:
                        self.posManager.moveStopLossIfLevelHitDuringShortPosition(currentLow=currentLow)
                        self.posManager.checkTargetProfitHitDuringShortPosition(currentLow=currentLow)
                        self.posManager.checkStopLossHitDuringShortPosition(currentHigh=currentHigh)
                        
                    self.posManager.moveStopLossIfAlmostHitDuringShortPosition(currentClose)
                    self.posManager.checkTenkanPassThroughDuingShortPosition(currentClose, currentOpen, currentTenkan)
                    self.posManager.moveTragetProfitIfLevelHitDuringShortPosition(currentLow=currentLow, currentClose=currentClose, atr_ratio=atr_ratio) #, currentOpen=currentOpen, currentTenkan=currentTenkan)

                    if not self.posManager.trade_is_done and ( 
                    # self.posManager.checkIfCanExitShortPosition(currentOpen, currentClose, current_kijun=strategy.df.loc[i, "kijun"])
                    #strategy.checkIfCanStopShortPosition(i, entryPrice=entryPrice, closePrice=currentClose, method=stopMethod)
                    # self.posManager.checkToMuchTimeInNoProfitZoneDuringShort(currentClose, prevClose, currentDate)
                    currentDate.hour >= 22):
                        self.posManager.short_stop_condition_hit(currentClose)

                if self.posManager.trade_is_done:
                    tradesData.append({
                        "entry_date": self.posManager.entryDate, 
                        "exit_date": currentDate, 
                        "entry_price": self.posManager.entryPrice, 
                        "exit_price": self.posManager.exit_price,
                        "position" : position,
                        "profit_including_fees_from_start(%)": 100*(self.posManager.profit-self.feesPerTrade)/self.INITIAL_CAPITAL,
                        "profit_from_start(%)":100*self.posManager.profit/self.INITIAL_CAPITAL,
                    }) 
                    self.posManager.reset()
                    position = Position.NONE   
                    position = self.checkCanEnterPos(i, currentDate, currentClose, atr_ratio)
                            
        return pd.DataFrame(tradesData)
