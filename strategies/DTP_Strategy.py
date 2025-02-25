import pandas as pd
from strategies.Strategy import Strategy
from values_definition import Position, Trend


class DTP(Strategy):

    def __init__(self, df:pd.DataFrame, use3UT:bool, useAllEntryPoints:bool): #, methodTenkanAngle:int ):#, nbr_of_points:int, delta_in_ticks:int):#chopValue:float):
        self.minTick = 0.01 #0.25 # tick size for SP500 (/ES)
        # self.nbr_of_points = nbr_of_points
        # self.delta_in_ticks = delta_in_ticks
        self.methodTenkanAngle = 2
        self.df_M5 = df
        self.use3UT = use3UT
        self.useAllEntryPoints = useAllEntryPoints
 
    def price_crossed_above(self, prev_close_price, close_price, value, byHowFar=0) -> bool:
        if(prev_close_price <= value and value+byHowFar < close_price ):
            return True
        else:
            return False
        
    def price_crossed_below(self, prev_close_price, close_price, value, byHowFar=0) -> bool:
        if(prev_close_price >= value and value-byHowFar > close_price ):
            return True
        else:
            return False
    
    # def get_last_support(self, i, nbr_of_points=3, delta_in_ticks=5):
    #     support_values = []
    #     for index in range(i, -1, -1):  # Recherche de haut en bas
    #         if len(support_values) < nbr_of_points:
    #             support_value = self.df_M5.loc[index, 'support']
    #             if support_value>0:
    #                 support_values.append(support_value)
    #         else:
    #             break
        
    #     support = sum(support_values)/len(support_values)
    #     for supp in support_values[1:]:
    #         if abs(support_values[0]-supp) > delta_in_ticks*self.minTick:
    #             support = 0 # no support
    #             break
    #     return support
    
    # def get_last_resistance(self, i, nbr_of_points=3, delta_in_ticks=5):
    #     resistance_values = []
    #     for index in range(i, -1, -1):  # Recherche de haut en bas
    #         resistance_value = self.df_M5.loc[index, 'resistance']
    #         if  len(resistance_values) < nbr_of_points:
    #             if resistance_value>0:
    #                 resistance_values.append(resistance_value)
    #         else: 
    #             break

    #     resistance = sum(resistance_values)/len(resistance_values)
    #     for res in resistance_values[1:]:
    #         if abs(resistance_values[0]-res) > delta_in_ticks*self.minTick:
    #             resistance = 0 # no resistance
    #             break
    #     return  resistance
    
    # def verify_distance_from_last_level(self, i, position, close, tpInTicks, nbr_of_points, delta_in_ticks) -> Position:
    #     # if nbr_of_points == 0 or delta_in_ticks == 0:
    #         # return position
        
    #     if position == Position.LONG:
    #         resistance = self.get_last_resistance(i, nbr_of_points, delta_in_ticks)
    #         tp = close + tpInTicks*self.minTick 

    #         if resistance == 0:
    #             return position
    #         elif tp < resistance: 
    #             return position
    #         else: 
    #             return Position.NONE
            
    #     elif position == Position.SHORT:
    #         support = self.get_last_support(i, nbr_of_points, delta_in_ticks)
    #         tp = close - tpInTicks*self.minTick

    #         if support == 0: # pas de support détecté
    #             return position
    #         elif tp > support: 
    #             return position
    #         else: 
    #             return Position.NONE
            
    #     else: 
    #         return Position.NONE

    
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

    def checkTenkanAngleBullish(self, i, method):
        if method == 1:
            if self.df_M5.loc[i-1]["tenkan"] < self.df_M5.loc[i]["tenkan"]:
                return True
        elif method == 2:
            if self.df_M5.loc[i-1]["tenkan"] <= self.df_M5.loc[i]["tenkan"]:
                return True
        return False
    
    def checkTenkanAngleBearish(self, i, method):
        if method == 1:
            if self.df_M5.loc[i-1]["tenkan"] > self.df_M5.loc[i]["tenkan"]:
                return True
        elif method == 2:
            if self.df_M5.loc[i-1]["tenkan"] >= self.df_M5.loc[i]["tenkan"]:
                return True
        return False

    def checkIfCanEnterPosition(self, i: int, tpInTicks:int) -> Position:
        position = Position.NONE

        # current_tenkan = self.df_M5.loc[i]["tenkan"]
        current_kijun = self.df_M5.loc[i]["kijun"]
        current_ssa = self.df_M5.loc[i]["ssa"]
        current_ssb = self.df_M5.loc[i]["ssb"]

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
        
            if (self.price_crossed_above(prev_close, close, current_kijun, byHowFar=2*self.minTick) 
                and close > self.df_M5.loc[i]["tenkan"]
                # and close > current_kijun + self.ticksAbove*self.minTick 
                # and self.df_M5.loc[i-1]["kijun"] <= self.df_M5.loc[i]["kijun"]
                and self.checkTenkanAngleBullish(i, method=self.methodTenkanAngle)
                #and self.df_M5.loc[i-1]["tenkan"] < self.df_M5.loc[i]["tenkan"]
                #and self.chop_crossed_below(self.chopValue, i)
            ):
                position = Position.LONG

            # elif(self.useAllEntryPoints):
            #     if (self.price_crossed_above(prev_close, close, current_tenkan)
            #         and self.df_M5.loc[i-20:i]["low"].min() <= self.df_M5.loc[i-20:i]["kijun"].min()
            #         and current_tenkan > current_kijun
            #         and self.df_M5.loc[i-1]["tenkan"] <= current_tenkan
            #         #and self.chop_crossed_below(self.chopValue, i)
            #     ):
            #         position = Position.LONG
            
        
        elif (convergence_UTs == Trend.BEARISH):
        
            if (self.price_crossed_below(prev_close, close, current_kijun, byHowFar=2*self.minTick) 
                and close < self.df_M5.loc[i]["tenkan"]
                # and close <  current_kijun - self.ticksAbove*self.minTick
                # and self.df_M5.loc[i-1]["kijun"] >= self.df_M5.loc[i]["kijun"]
                and self.checkTenkanAngleBearish(i, method=self.methodTenkanAngle)
                #and self.df_M5.loc[i-1]["tenkan"] > self.df_M5.loc[i]["tenkan"]
            ): 
                position = Position.SHORT

            # elif(self.useAllEntryPoints):
            #     if (self.price_crossed_below(prev_close, close, current_tenkan)
            #         and self.df_M5.loc[i-20:i]["high"].max() >= self.df_M5.loc[i-20:i]["kijun"].max()
            #         and current_tenkan < current_kijun
            #         and self.df_M5.loc[i-1]["tenkan"] >= current_tenkan
            #     ):
            #         position = Position.SHORT
        #position = self.verify_distance_from_last_level(i, position, close, tpInTicks, self.nbr_of_points, self.delta_in_ticks)
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
        
        if method == 3:
            current_tenkan = self.df_M5.loc[i]["tenkan"]
            high = self.df_M5.loc[i]["high"]
            close = self.df_M5.loc[i]["close"]
            open = self.df_M5.loc[i]["open"]
            return (high <= current_tenkan) or (close < open and open <= current_kijun)
        
    def checkIfCanStopShortPosition(self, i: int, method:int) -> bool:
        current_kijun = self.df_M5.loc[i]["kijun"]

        if method == 1:
            low = self.df_M5.loc[i]["low"]
            return low >= current_kijun
        
        elif method == 2:
            close = self.df_M5.loc[i]["close"]
            open = self.df_M5.loc[i]["open"]
            return close > open and open >= current_kijun
        
        if method == 3:
            current_tenkan = self.df_M5.loc[i]["tenkan"]
            low = self.df_M5.loc[i]["low"]
            close = self.df_M5.loc[i]["close"]
            open = self.df_M5.loc[i]["open"]
            return (low >= current_tenkan) or (close > open and open >= current_kijun)
        

    
  