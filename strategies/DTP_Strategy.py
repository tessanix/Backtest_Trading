import pandas as pd
from strategies.Strategy import Strategy
from values_definition import Position, Trend


class DTP(Strategy):

    def __init__(self, df:pd.DataFrame, timeframes:list[str], useAllEntryPoints:bool, ticksCrossed:int=0, tenkanCond:bool=2, ratioDistanceKijun:float=0.4):#, updateCloseFrequency:int=1 ):
        self.ratioDistanceKijun = ratioDistanceKijun
        self.tenkanCond=tenkanCond
        self.ticksCrossed = ticksCrossed
        self.df = df
        self.timeframes = timeframes
        self.useAllEntryPoints = useAllEntryPoints

        # self.open, self.high, self.low, self.close = None, None, None, None
        # self.updateCloseFrequency = updateCloseFrequency
        # self.date = None
 
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
    
    # def checkChopIndexAllowingTrade(self, i):
    #     crossed = False
    #     if i>5:
    #         for idx in range(i, i-5, -1):
    #             if(self.df.loc[idx]["chop"] < self.chopValueToCross and self.df.loc[idx-1]["chop"] >= self.chopValueToCross):
    #                 crossed = True
    #                 break
    #     return crossed
    

    # def get_last_support(self, i, minTick, nbr_of_points=3, delta_in_ticks=5):
    #     support_values = []
    #     for index in range(i, -1, -1):  # Recherche de haut en bas
    #         if len(support_values) < nbr_of_points:
    #             support_value = self.df.loc[index, 'support']
    #             if support_value>0:
    #                 support_values.append(support_value)
    #         else:
    #             break
        
    #     support = sum(support_values)/len(support_values)
    #     for supp in support_values[1:]:
    #         if abs(support_values[0]-supp) > delta_in_ticks*minTick:
    #             support = 0 # no support
    #             break
    #     return support
    

    # def get_last_resistance(self, i, minTick, nbr_of_points=3, delta_in_ticks=5):
    #     resistance_values = []
    #     for index in range(i, -1, -1):  # Recherche de haut en bas
    #         resistance_value = self.df.loc[index, 'resistance']
    #         if  len(resistance_values) < nbr_of_points:
    #             if resistance_value>0:
    #                 resistance_values.append(resistance_value)
    #         else: 
    #             break

    #     resistance = sum(resistance_values)/len(resistance_values)
    #     for res in resistance_values[1:]:
    #         if abs(resistance_values[0]-res) > delta_in_ticks*minTick:
    #             resistance = 0 # no resistance
    #             break
    #     return  resistance
    
    # def verify_distance_from_last_level(self, i, position, close, tpInTicks, minTick, nbr_of_points, delta_in_ticks) -> Position:
    #     # if nbr_of_points == 0 or delta_in_ticks == 0:
    #         # return position
        
    #     if position == Position.LONG:
    #         resistance = self.get_last_resistance(i, nbr_of_points, delta_in_ticks)
    #         tp = close + tpInTicks*minTick 

    #         if resistance == 0:
    #             return position
    #         elif tp < resistance: 
    #             return position
    #         else: 
    #             return Position.NONE
            
    #     elif position == Position.SHORT:
    #         support = self.get_last_support(i, nbr_of_points, delta_in_ticks)
    #         tp = close - tpInTicks*minTick

    #         if support == 0: # pas de support détecté
    #             return position
    #         elif tp > support: 
    #             return position
    #         else: 
    #             return Position.NONE
            
    #     else: 
    #         return Position.NONE

    def check_chikou_position(self, i, position):
        chikou_val = self.df.loc[i-26, "chikou"]
        ssa_val = self.df.loc[i-26,"ssa"]
        ssb_val = self.df.loc[i-26,"ssb"]
        # close_val = self.df.loc[i-26,"close"]

        if (ssa_val <= chikou_val and chikou_val <= ssb_val) or (ssa_val >= chikou_val and chikou_val >= ssb_val):
        # or (position == Position.LONG and chikou_val <= close_val) \
        # or (position == Position.SHORT and chikou_val >= close_val):
            position = Position.NONE

        return position
    
    # def update_internal_pivot(self, i, close, today):
    #     current_highest = self.df.loc[i, "high"]
    #     current_lowest = self.df.loc[i, "low"]
    #     if self.updateCloseFrequency == 1:
    #         self.close = close
            
    #     elif self.updateCloseFrequency == 2:
    #         if self.date.hour != today.hour:
    #             self.close = close

    #     elif self.updateCloseFrequency == 2:
    #         if self.date.day != today.day:
    #             self.close = close

    #     if self.high < current_highest:
    #         self.high = current_highest
    #     if self.low > current_lowest:
    #         self.low = current_lowest

    def get_2_nearest_pivot_levels(self, i, close) -> tuple[float, float]:
        # self.update_internal_pivot()
        pivot_levels = self.df.loc[i][["S3","S2","S1","PP","R1","R2","R3"]]

        lowers = [lvl for lvl in pivot_levels if lvl <= close]
        highers = [lvl for lvl in pivot_levels if lvl >= close]

        # Trouver le plus proche dans chaque direction
        closest_lower = max(lowers) if lowers else None
        closest_higher = min(highers) if highers else None
        # if closest_lower is None or closest_higher is None:
        #     print(f"⚠️ Pivot missing at index {i} | close = {close} | pivots = {pivot_levels}")

        return closest_lower, closest_higher
            


    # def get_largest_ssb_flat(self, i, lookback=720):
    #     if i-lookback < 0:
    #         return 0
    #     ssb_levels_count = self.df.loc[i-lookback: i, "ssb_"+self.timeframes[1]].value_counts()
    #     return ssb_levels_count.idxmax()

    def verify_distance_from_pivot_level(self, i, position, close, tpInTicks, minTick):#, ssb_higher_timeframe) -> Position:
        support, resistance = self.get_2_nearest_pivot_levels(i, close)
        if support is None or resistance is None:
            return Position.NONE
        # ssb_higher_timeframe = self.get_largest_ssb_flat(i, lookback=720)
        # if ssb_higher_timeframe > 0:
        # if ssb_higher_timeframe > support and ssb_higher_timeframe < close:
        #     support = ssb_higher_timeframe
        # elif ssb_higher_timeframe < resistance and ssb_higher_timeframe > close:
        #     resistance = ssb_higher_timeframe

        # pivot_level = self.df.loc[i]["PP"]
        distance_kijun = abs(close-self.df.loc[i,"kijun_15"])
        distance_sup_res = resistance-support
        if distance_kijun < self.ratioDistanceKijun*distance_sup_res or self.ratioDistanceKijun < 0:
            if position == Position.LONG:
                # if close < pivot_level:
                #     return Position.NONE
                tp = close + tpInTicks*minTick 
                if tp < resistance: 
                    return position
                else: 
                    return Position.NONE
            elif position == Position.SHORT:
                # if close > pivot_level:
                #     return Position.NONE
                tp = close - tpInTicks*minTick
                if tp > support: 
                    return position
                else: 
                    return Position.NONE
            else: 
                return Position.NONE
        else:
            return Position.NONE

    def checkTenkanAngleBullish(self, i):
        if self.tenkanCond == 1:
            if self.df.loc[i-1]["tenkan"] < self.df.loc[i]["tenkan"]:
                return True
        elif self.tenkanCond == 2:
            if self.df.loc[i-1]["tenkan"] <= self.df.loc[i]["tenkan"]:
                return True
        return False
    
    def checkTenkanAngleBearish(self, i):
        if self.tenkanCond == 1:
            if self.df.loc[i-1]["tenkan"] > self.df.loc[i]["tenkan"]:
                return True
        elif self.tenkanCond == 2:
            if self.df.loc[i-1]["tenkan"] >= self.df.loc[i]["tenkan"]:
                return True
        return False

    def checkIfCanEnterPosition(self, i: int, tpInTicks:int, minTick:float) -> Position:
        position = Position.NONE

        # current_tenkan = self.df.loc[i]["tenkan"]
        current_kijun = self.df.loc[i]["kijun"]
        current_ssa = self.df.loc[i]["ssa"]
        current_ssb = self.df.loc[i]["ssb"]
        # current_ssb_of_other_tf = 0
        close = self.df.loc[i]["close"]
        prev_close = self.df.loc[i-1]["close"]

        convergence_UTs = [] # liste des tendances de toutes les UTS

        if (close > current_ssb and close > current_ssa):
            convergence_UTs.append(Trend.BULLISH)
        elif (close < current_ssb and close < current_ssa):
            convergence_UTs.append(Trend.BEARISH)
  
        for tf in self.timeframes[1:]:
            # current_ssa_of_other_tf = self.df.loc[i]["ssa_"+tf]
            current_ssb_of_other_tf = self.df.loc[i]["ssb_"+tf]
            if close > current_ssb_of_other_tf :#and close > current_ssa_of_other_tf:
                convergence_UTs.append(Trend.BULLISH)
            if close < current_ssb_of_other_tf : #and close < current_ssa_of_other_tf:
                convergence_UTs.append(Trend.BEARISH)


        # for tf in self.timeframes[1:]:
        #         current_kijun_of_highest_tf = self.df.loc[i]["kijun_"+tf]
        #         if close > current_kijun_of_highest_tf:
        #             convergence_UTs.append(Trend.BULLISH)
        #         if close < current_kijun_of_highest_tf:
        #             convergence_UTs.append(Trend.BEARISH)
            # else:
            #     current_ssa_of_other_tf = self.df.loc[i]["ssa_"+tf]
            #     current_ssb_of_other_tf = self.df.loc[i]["ssb_"+tf]
            #     if close > current_ssb_of_other_tf and close > current_ssa_of_other_tf:
            #         convergence_UTs.append(Trend.BULLISH)
            #     if close < current_ssb_of_other_tf and close < current_ssa_of_other_tf:
            #         convergence_UTs.append(Trend.BEARISH)

        if all(trend == Trend.BULLISH for trend in convergence_UTs):
        
            if (self.price_crossed_above(prev_close, close, current_kijun, byHowFar=self.ticksCrossed*minTick) 
                # and self.price_crossed_above(prev_close, close, self.df.loc[i]["tenkan"], byHowFar=self.ticksCrossed*minTick) 
                # and abs(close - self.df.loc[i, "open"])/minTick < 6
                and close > self.df.loc[i]["tenkan"]
                # and self.rsiVal[0] < self.df.loc[i]["RSI"]

                # and close > current_kijun + self.ticksAbove*self.minTick 
                # and self.df.loc[i-1]["kijun"] <= self.df.loc[i]["kijun"]
                and self.checkTenkanAngleBullish(i)
                #and self.df.loc[i-1]["tenkan"] < self.df.loc[i]["tenkan"]
                #and self.chop_crossed_below(self.chopValue, i)
            ):
                position = Position.LONG

            # elif(self.useAllEntryPoints):
            #     if (self.price_crossed_above(prev_close, close, current_tenkan)
            #         and self.df.loc[i-20:i]["low"].min() <= self.df.loc[i-20:i]["kijun"].min()
            #         and current_tenkan > current_kijun
            #         and self.df.loc[i-1]["tenkan"] <= current_tenkan
            #         #and self.chop_crossed_below(self.chopValue, i)
            #     ):
            #         position = Position.LONG
            
        
        elif all(trend == Trend.BEARISH for trend in convergence_UTs):
        
            if (self.price_crossed_below(prev_close, close, current_kijun, byHowFar=self.ticksCrossed*minTick) 
                # and self.price_crossed_below(prev_close, close, self.df.loc[i]["tenkan"], byHowFar=self.ticksCrossed*minTick) 
                # and abs(self.df.loc[i, "open"] - close)/minTick < 6
                and close < self.df.loc[i]["tenkan"]
                # and self.rsiVal[1] > self.df.loc[i]["RSI"]

                # and close <  current_kijun - self.ticksAbove*self.minTick
                # and self.df.loc[i-1]["kijun"] >= self.df.loc[i]["kijun"]
                and self.checkTenkanAngleBearish(i)
                #and self.df.loc[i-1]["tenkan"] > self.df.loc[i]["tenkan"]
            ): 
                position = Position.SHORT

            # elif(self.useAllEntryPoints):
            #     if (self.price_crossed_below(prev_close, close, current_tenkan)
            #         and self.df.loc[i-20:i]["high"].max() >= self.df.loc[i-20:i]["kijun"].max()
            #         and current_tenkan < current_kijun
            #         and self.df.loc[i-1]["tenkan"] >= current_tenkan
            #     ):
            #         position = Position.SHORT
        position = self.verify_distance_from_pivot_level(i, position, close, tpInTicks, minTick) #, current_ssb_of_other_tf)
        position = self.check_chikou_position(i, position)

        # if self.checkChopIndexAllowingTrade(i) == False:
        #     position = Position.NONE
        # position = self.verify_distance_from_last_level(i, position, close, tpInTicks, minTick, self.nbr_of_points, self.delta_in_ticks)
        
        return position
    
    def checkIfCanStopLongPosition(self, i: int, entryPrice:float, closePrice:float, method:int) -> bool:
        if method == 0: return False
        cond1 = closePrice - entryPrice > 0
        current_kijun = self.df.loc[i]["kijun"]

        if method == 1:
            high = self.df.loc[i]["high"]
            cond2 = high <= current_kijun
        
        elif method == 2:
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            return close < open and open <= current_kijun
        
        elif method == 3:
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = close < open and close < current_kijun
        
        elif method == 4:
            current_tenkan = self.df.loc[i]["tenkan"]
            high = self.df.loc[i]["high"]
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = (high <= current_tenkan) or (close < open and open <= current_kijun)
        
        elif method == 5:
            current_tenkan = self.df.loc[i]["tenkan"]
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = (close < open and open < current_tenkan) or (close < open and open <= current_kijun)

        return cond1 and cond2
    
    def checkIfCanStopShortPosition(self, i: int, entryPrice:float, closePrice:float, method:int) -> bool:
        if method == 0: return False
        cond1 = entryPrice - closePrice > 0
        current_kijun = self.df.loc[i]["kijun"]

        if method == 1:
            low = self.df.loc[i]["low"]
            cond2 = low >= current_kijun
        
        elif method == 2:
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = close > open and open >= current_kijun
        
        elif method == 3:
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = close > open and close > current_kijun
        
        elif method == 4:
            current_tenkan = self.df.loc[i]["tenkan"]
            low = self.df.loc[i]["low"]
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = (low >= current_tenkan) or (close > open and open >= current_kijun)
        
        elif method == 5:
            current_tenkan = self.df.loc[i]["tenkan"]
            close = self.df.loc[i]["close"]
            open = self.df.loc[i]["open"]
            cond2 = (close > open and open > current_tenkan) or (close > open and open >= current_kijun)
        
        return cond1 and cond2
        

    
  