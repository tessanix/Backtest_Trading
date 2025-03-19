from values_definition import Result

class PositionManager():

    def __init__(self, followingSlinTicks, tpInTicks, tickValue, 
                 tickSize, positionSize, entryPrice, sl, tp, bracketsModifier, 
                 tpToMoveInTicks, percentHitToMoveTP, nbrTimeMaxMoveTP, trade_is_done=False): #atrSlopeTreshold
        
        self.followingSlinTicks = followingSlinTicks
        self.tpInTicks = tpInTicks
        self.tickValue = tickValue
        self.tickSize = tickSize
        self.positionSize = positionSize
        self.entryPrice = entryPrice
        self.exit_price = None
        self.sl = sl
        self.tp = tp
        self.bracketsModifier = bracketsModifier
        self.trade_is_done = trade_is_done
        self.profit = None
        # self.atrSlopeTreshold = atrSlopeTreshold
        self.tpToMoveInTicks = tpToMoveInTicks
        self.percentHitToMoveTP = percentHitToMoveTP
        self.nbrTimeMaxMoveTP = nbrTimeMaxMoveTP
        self.nbrPassThroughTenkan = 0
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
        if self.nbrPassThroughTenkan >0:
            if self.nb_time_sl_moved == 0 and len(self.bracketsModifier)>0: 
                if (currentHigh-self.entryPrice)/self.tickSize>self.bracketsModifier[0][0]*self.tpInTicks:
                    if self.bracketsModifier[0][1]>0:
                        self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[0][1]
                        self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize
                    else:
                        self.followingSlinTicks = self.followingSlinTicks*abs(self.bracketsModifier[0][1])
                        self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize
                    self.nb_time_sl_moved += 1

            elif self.nb_time_sl_moved == 1 and len(self.bracketsModifier)>1: 
                if (currentHigh-self.entryPrice)/self.tickSize>self.bracketsModifier[1][0]*self.tpInTicks:
                    if self.bracketsModifier[1][1]>0:
                        self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[1][1]
                        self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize   
                    else:
                        self.followingSlinTicks = self.followingSlinTicks*abs(self.bracketsModifier[1][1])
                        self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize
                    self.nb_time_sl_moved += 1

    def moveStopLossIfLevelHitDuringShortPosition(self, currentLow):
        if self.nbrPassThroughTenkan >0:
            if self.nb_time_sl_moved == 0 and len(self.bracketsModifier)>0: 
                if (self.entryPrice-currentLow)/self.tickSize>self.bracketsModifier[0][0]*self.tpInTicks:
                    if self.bracketsModifier[0][1]>0:
                        self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[0][1]
                        self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize   
                    else:
                        self.followingSlinTicks = self.tpInTicks*abs(self.bracketsModifier[0][1])
                        self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize   
                    self.nb_time_sl_moved += 1

            elif self.nb_time_sl_moved == 1 and len(self.bracketsModifier)>1: 
                if (self.entryPrice-currentLow)/self.tickSize>self.bracketsModifier[1][0]*self.tpInTicks:
                    if self.bracketsModifier[1][1]>0:
                        self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[1][1]
                        self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize   
                    else:
                        self.followingSlinTicks = self.tpInTicks*abs(self.bracketsModifier[1][1])
                        self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize   
                    self.nb_time_sl_moved += 1

    # def moveTragetProfitIfLevelHitDuringLongPosition1(self, currentHigh, atrSlope):
    #     if (currentHigh-self.entryPrice)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and atrSlope > self.atrSlopeTreshold:
    #         self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks
    #         self.tp = self.tp + self.tpToMoveInTicks*self.tickSize   

    # def moveTragetProfitIfLevelHitDuringShortPosition1(self, currentLow, atrSlope):
    #     if (self.entryPrice-currentLow)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and atrSlope > self.atrSlopeTreshold:
    #         self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks
    #         self.tp = self.tp - self.tpToMoveInTicks*self.tickSize   

    def moveTragetProfitIfLevelHitDuringLongPosition(self, currentClose, currentOpen, currentHigh, currentTenkan):
        if (currentHigh-self.entryPrice)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and currentClose > self.entryPrice \
            and currentOpen < currentTenkan and currentTenkan < currentClose and self.nbrPassThroughTenkan < self.nbrTimeMaxMoveTP:
            self.nbrPassThroughTenkan+=1
            self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks
            self.tp = self.tp + self.tpToMoveInTicks*self.tickSize   

    def moveTragetProfitIfLevelHitDuringShortPosition(self, currentClose, currentOpen, currentLow, currentTenkan):
        if (self.entryPrice-currentLow)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and currentClose < self.entryPrice \
            and currentOpen > currentTenkan and currentTenkan > currentClose and self.nbrPassThroughTenkan < self.nbrTimeMaxMoveTP:
            self.nbrPassThroughTenkan+=1
            self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks
            self.tp = self.tp - self.tpToMoveInTicks*self.tickSize   

  