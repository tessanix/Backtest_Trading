import pandas as pd
from strategies.Strategy import Strategy
from values_definition import Position, Trend


class DTP(Strategy):

    def __init__(self, df:pd.DataFrame, use3UT:bool, useAllEntryPoints:bool):
        self.minTick = 0.25 # tick size for SP500 (/ES)
        
        self.df_M5 = df
        self.use3UT = use3UT
        self.useAllEntryPoints = useAllEntryPoints
    
    # def determineSlAndTp(self, capital:float, price: float, keyLevels: list[float]) -> tuple[bool, float, float]:
    #     slInPips = -utility.getSlInPipsForTrade(
    #                         invested = capital*self.maxRisk,
    #                         pipValue = 50, # valeur du pip pour le SP500 pour un lot standard = 50
    #                         lotSize = 0.01 # micro lot
    #                     )
    #     tpInPips = -slInPips
    #     resistance = support = 0
    #     done = False

    #     for i in range(len(keyLevels)):
    #         sl = price+slInPips
    #         # keyLevels[i==0] is the greatest level
    #         if i==0 and sl < keyLevels[i] and keyLevels[i] < price: 
    #             slInPips = keyLevels[i]-price # négatif
    #             done = True
    #             break
    #         elif i!=0 and keyLevels[i] < price and price < keyLevels[i-1]:
    #             resistance = keyLevels[i-1]
    #             support = keyLevels[i]
    #             break

    #     if done: 
    #         return False, slInPips, tpInPips
        
    #     middleSR = (resistance+support)/2

    #     isBelowMiddleSR = price < middleSR

    #     if isBelowMiddleSR:
    #         sl = price+slInPips
    #         tp = price+tpInPips
    #         if sl < support and price*0.02 <= price-support: 
    #             slInPips = support-price # négatif
    #         if tp < resistance: 
    #             tpInPips = resistance-price

    #     return isBelowMiddleSR, slInPips, tpInPips

    # def updateSl(self, currentPrice: float, entryPrice:float, tpInPips:float) -> float:
    #     newSlInPips = 0
    #     if self.useUpdateSl and tpInPips/2 < currentPrice-entryPrice:
    #         newSlInPips = tpInPips/4 #positif
    #     return newSlInPips

    def price_crossed_above(self, prev_close_price, close_price, value) -> bool:
        if(prev_close_price <= value and value < close_price ):
            return True
        else:
            return False
        
    def price_crossed_below(self, prev_close_price, close_price, value) -> bool:
        if(prev_close_price >= value and value > close_price ):
            return True
        else:
            return False
    
    def get_2_nearest_pivot_levels(self, i, close) -> tuple[float, float]:
        pivot_levels = self.df_M5.loc[i][["S3","S2","S1","PP","R1","R2","R3"]]
        closest_lower = None
        closest_higher = None
        # Parcourir les valeurs triées pour trouver les plus proches
        for value in pivot_levels:
            if value < close:
                closest_lower = value
            elif value > close and closest_higher is None:
                closest_higher = value
        
        return closest_lower, closest_higher

    def verify_distance_from_pivot_level(self, i, position, close, tpInTicks) -> Position:
        support, resistance = self.get_2_nearest_pivot_levels(i, close)
        # pivot_level = self.df_M5.loc[i]["PP"]
        if position == Position.LONG:
            # if close < pivot_level:
            #     return Position.NONE
            tp = close + tpInTicks*self.minTick 
            if tp < resistance: 
                return position
            else: 
                return Position.NONE
        elif position == Position.SHORT:
            # if close > pivot_level:
            #     return Position.NONE
            tp = close - tpInTicks*self.minTick
            if tp > support: 
                return position
            else: 
                return Position.NONE
        else: 
            return Position.NONE
          

    def checkIfCanEnterPosition(self, i: int, tpInTicks:int) -> Position:
        position = Position.NONE

        current_tenkan = self.df_M5.loc[i]["tenkan"]
        current_kijun = self.df_M5.loc[i]["kijun"]
        current_ssa = self.df_M5.loc[i]["ssa"]
        current_ssb = self.df_M5.loc[i]["ssb"]

        current_ssa_m15 = None
        current_ssb_m15 = None
        current_ssa_h1 = None
        current_ssb_h1 = None
        convergence_UTs = Trend.NONE # "bullish" or "bearish"

        close = self.df_M5.loc[i]["close"]
        prev_close = self.df_M5.loc[i-1]["close"]

        if(self.use3UT):
            current_ssa_m15 = self.df_M5.loc[i]["ssa_m15"]
            current_ssb_m15 = self.df_M5.loc[i]["ssb_m15"]
            current_ssa_h1 = self.df_M5.loc[i]["ssa_h1"]
            current_ssb_h1 = self.df_M5.loc[i]["ssb_h1"]

            # if (isnan(current_ssa) or isnan(current_ssb) or isnan(current_tenkan) or isnan(current_kijun)
            #     or isnan(current_ssa_m15) or isnan(current_ssb_m15) or isnan(current_ssa_h1) or isnan(current_ssb_h1) ):
            #     return position
            
            if (close > current_ssb and close > current_ssa
                and close > current_ssb_m15 and close > current_ssa_m15
                and close > current_ssb_h1 and close > current_ssa_h1):
                convergence_UTs = Trend.BULLISH
            elif (close < current_ssb and close < current_ssa
                and close < current_ssb_m15 and close < current_ssa_m15
                and close < current_ssb_h1 and close < current_ssa_h1):
                convergence_UTs = Trend.BEARISH

        else:
            # if (isnan(current_ssa) or isnan(current_ssb) or isnan(current_tenkan) or isnan(current_kijun)):
            #     return position
            if (close > current_ssb and close > current_ssa):
                convergence_UTs = Trend.BULLISH
            elif (close < current_ssb and close < current_ssa):
                convergence_UTs = Trend.BEARISH

       
        if (convergence_UTs == Trend.BULLISH):
        
            if (self.price_crossed_above(prev_close, close, current_kijun) 
                and close > current_tenkan
                and close > current_kijun + 2*self.minTick 
                and self.df_M5.loc[i-1]["tenkan"] <= current_tenkan
            ):
                position = Position.LONG

            elif(self.useAllEntryPoints):
                if (self.price_crossed_above(prev_close, close, current_tenkan)
                    and self.df_M5.loc[i-20:i]["low"].min() <= self.df_M5.loc[i-20:i]["kijun"].min()
                    and current_tenkan > current_kijun
                    and self.df_M5.loc[i-1]["tenkan"] <= current_tenkan
                ):
                    position = Position.LONG
            
        
        elif (convergence_UTs == Trend.BEARISH):
        
            if (self.price_crossed_below(prev_close, close, current_kijun) 
                and close < current_tenkan
                and close <  current_kijun - 2*self.minTick
                and self.df_M5.loc[i-1]["tenkan"] >= current_tenkan
            ): 
                position = Position.SHORT

            elif(self.useAllEntryPoints):
                if (self.price_crossed_below(prev_close, close, current_tenkan)
                    and self.df_M5.loc[i-20:i]["high"].max() >= self.df_M5.loc[i-20:i]["kijun"].max()
                    and current_tenkan < current_kijun
                    and self.df_M5.loc[i-1]["tenkan"] >= current_tenkan
                ):
                    position = Position.SHORT

        position = self.verify_distance_from_pivot_level(i, position, close, tpInTicks)      
        
        return position
    
    def checkIfCanStopLongPosition(self, i: int, method:int) -> bool:
        current_kijun = self.df_M5.loc[i]["kijun"]

        if method == 1:
            high = self.df_M5.loc[i]["high"]
            return high <= current_kijun
        
        elif method == 2:
            close = self.df_M5.loc[i]["close"]
            open = self.df_M5.loc[i]["open"]
            return close < open and open <= current_kijun
        
    def checkIfCanStopShortPosition(self, i: int, method:int) -> bool:
        current_kijun = self.df_M5.loc[i]["kijun"]

        if method == 1:
            low = self.df_M5.loc[i]["low"]
            return low >= current_kijun
        
        elif method == 2:
            close = self.df_M5.loc[i]["close"]
            open = self.df_M5.loc[i]["open"]
            return close > open and open >= current_kijun

    
  