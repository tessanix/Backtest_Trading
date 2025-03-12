from values_definition import Result

class PositionManager():

    def __init__(self, followingSlinTicks, tpInTicks, tickValue, 
                 tickSize, positionSize, entryPrice, sl, tp, slModifiers, trade_is_done=False):
        
        self.followingSlinTicks = followingSlinTicks
        self.tpInTicks = tpInTicks
        self.tickValue = tickValue
        self.tickSize = tickSize
        self.positionSize = positionSize
        self.entryPrice = entryPrice
        self.exit_price = None
        self.sl = sl
        self.tp = tp
        self.slModifiers = slModifiers
        self.trade_is_done = trade_is_done
        self.profit = None
        self.nb_time_sl_moved = 0

    def profit_for_sl_hit(self, result):
        profit = self.followingSlinTicks*self.tickValue*self.positionSize
        return profit if result==Result.WIN else -profit

    def profit_for_long_stop_condition_hit(self, currentPrice):
        return ((currentPrice-self.entryPrice)/self.tickSize)*self.tickValue*self.positionSize

    def profit_for_short_stop_condition_hit(self, currentPrice):
       return ((self.entryPrice-currentPrice)/self.tickSize)*self.tickValue*self.positionSize

    def profit_for_tp_hit(self):
        return self.tpInTicks*self.tickValue*self.positionSize

    def checkStopLossHitDuringLongPosition(self, currentLow):
        if currentLow <= self.sl and not self.trade_is_done:
            result = Result.WIN  if self.entryPrice < self.sl else Result.LOSS
            self.profit = self.profit_for_sl_hit(result)
            self.exit_price = self.sl
            self.trade_is_done = True

    def checkStopLossHitDuringShortPosition(self, currentHigh):
        if currentHigh >= self.sl and not self.trade_is_done:
            result = Result.WIN  if self.entryPrice > self.sl else Result.LOSS
            self.profit = self.profit_for_sl_hit(result)
            self.exit_price = self.sl
            self.trade_is_done = True

    def checkTargetProfitHitDuringLongPosition(self, currentHigh):
        if currentHigh >= self.tp and not self.trade_is_done:
            self.profit = self.profit_for_tp_hit()
            self.exit_price = self.tp
            self.trade_is_done = True
        
    def checkTargetProfitHitDuringShortPosition(self, currentLow):
        if currentLow <= self.tp and not self.trade_is_done:
            self.profit = self.profit_for_tp_hit()
            self.exit_price = self.tp
            self.trade_is_done = True
    
    def moveStopLossIfLevelHitDuringLongPosition(self, currentHigh):
        if self.nb_time_sl_moved == 0 and len(self.slModifiers)>0: 
            if (currentHigh-self.entryPrice)/self.tickSize>self.slModifiers[0][0]*self.tpInTicks:
                followingSlinTicks = self.tpInTicks*self.slModifiers[0][1]
                self.sl = self.entryPrice+followingSlinTicks*self.tickSize   
                self.nb_time_sl_moved += 1

        elif self.nb_time_sl_moved == 1 and len(self.slModifiers)>1: 
            if (currentHigh-self.entryPrice)/self.tickSize>self.slModifiers[1][0]*self.tpInTicks:
                followingSlinTicks = self.tpInTicks*self.slModifiers[1][1]
                self.sl = self.entryPrice+followingSlinTicks*self.tickSize     
                self.nb_time_sl_moved += 1

    def moveStopLossIfLevelHitDuringShortPosition(self, currentLow):
        if self.nb_time_sl_moved == 0 and len(self.slModifiers)>0: 
            if (self.entryPrice-currentLow)/self.tickSize>self.slModifiers[0][0]*self.tpInTicks:
                followingSlinTicks = self.tpInTicks*self.slModifiers[0][1]
                self.sl = self.entryPrice-followingSlinTicks*self.tickSize   
                self.nb_time_sl_moved += 1

        elif self.nb_time_sl_moved == 1 and len(self.slModifiers)>1: 
            if (self.entryPrice-currentLow)/self.tickSize>self.slModifiers[1][0]*self.tpInTicks:
                followingSlinTicks = self.tpInTicks*self.slModifiers[1][1]
                self.sl = self.entryPrice-followingSlinTicks*self.tickSize     
                self.nb_time_sl_moved += 1