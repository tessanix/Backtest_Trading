from values_definition import Result

class PositionManager():

    def __init__(self, tickValue, tickSize, positionSize, bracketsModifier, 
                 tpToMoveInTicks, percentHitToMoveTP, nbrTimeMaxMoveTP): #atrSlopeTreshold
        
        self.tickValue = tickValue
        self.tickSize = tickSize
        self.positionSize = positionSize
        self.bracketsModifier = bracketsModifier
        self.tpToMoveInTicks = tpToMoveInTicks
        self.percentHitToMoveTP = percentHitToMoveTP
        self.nbrTimeMaxMoveTP = nbrTimeMaxMoveTP
        self.nbrPassThroughTenkan = None
        self.nb_time_sl_moved = None
        self.nb_time_tp_moved = None
        self.followingSlinTicks = None
        self.tpInTicks = None
        self.sl = None
        self.tp = None
        self.entryPrice = None
        self.exit_price = None
        self.trade_is_done = None
        self.profit = None

    def set_new_trade_attributes(self, followingSlinTicks, tpInTicks, entryPrice, sl, tp):
        self.followingSlinTicks = followingSlinTicks
        self.tpInTicks = tpInTicks
        self.entryPrice = entryPrice
        self.sl = sl
        self.tp = tp
        self.trade_is_done = False
        self.nbrPassThroughTenkan = 0
        self.nb_time_sl_moved = 0
        self.nb_time_tp_moved = 0
    
    def reset(self):
        self.followingSlinTicks = None
        self.tpInTicks = None
        self.entryPrice = None
        self.exit_price = None
        self.sl = None
        self.tp = None
        self.trade_is_done = None
        self.nbrPassThroughTenkan = None
        self.nb_time_sl_moved = None
        self.nb_time_tp_moved = None
        self.profit = None


    def profit_for_sl_hit(self, result):
        profit = self.followingSlinTicks*self.tickValue*self.positionSize
        return profit if result==Result.WIN else -profit

    def profit_for_tp_hit(self):
        return self.tpInTicks*self.tickValue*self.positionSize

    def long_stop_condition_hit(self, currentClose):
        #if not self.trade_is_done:
        self.exit_price = currentClose
        self.trade_is_done = True
        self.profit = ((currentClose-self.entryPrice)/self.tickSize)*self.tickValue*self.positionSize

    def short_stop_condition_hit(self, currentClose):
        #if not self.trade_is_done:
        self.exit_price = currentClose
        self.trade_is_done = True
        self.profit = ((self.entryPrice-currentClose)/self.tickSize)*self.tickValue*self.positionSize

    def checkStopLossHitDuringLongPosition(self, currentLow):
        if currentLow <= self.sl and not self.trade_is_done:
            result = Result.WIN  if self.entryPrice < self.sl else Result.LOSS
            self.exit_price = self.sl
            self.trade_is_done = True
            self.profit = self.profit_for_sl_hit(result)

    def checkStopLossHitDuringShortPosition(self, currentHigh):
        if currentHigh >= self.sl and not self.trade_is_done:
            result = Result.WIN  if self.entryPrice > self.sl else Result.LOSS
            self.exit_price = self.sl
            self.trade_is_done = True
            self.profit = self.profit_for_sl_hit(result)

    def checkTargetProfitHitDuringLongPosition(self, currentHigh):
        if currentHigh >= self.tp and not self.trade_is_done:
            self.exit_price = self.tp
            self.trade_is_done = True
            self.profit = self.profit_for_tp_hit()
        
    def checkTargetProfitHitDuringShortPosition(self, currentLow):
        if currentLow <= self.tp and not self.trade_is_done:
            self.exit_price = self.tp
            self.trade_is_done = True
            self.profit = self.profit_for_tp_hit()
    
    # def moveStopLossIfLevelHitDuringLongPosition(self, currentHigh):
    #     if self.nbrPassThroughTenkan >0:
    #         if self.nb_time_sl_moved == 0 and len(self.bracketsModifier)>0: 
    #             if (currentHigh-self.entryPrice)/self.tickSize>self.bracketsModifier[0][0]*self.tpInTicks:
    #                 if self.bracketsModifier[0][1]>0:
    #                     self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[0][1]
    #                     self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize
    #                 else:
    #                     self.followingSlinTicks = self.followingSlinTicks*abs(self.bracketsModifier[0][1])
    #                     self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize
    #                 self.nb_time_sl_moved += 1

    #         elif self.nb_time_sl_moved == 1 and len(self.bracketsModifier)>1: 
    #             if (currentHigh-self.entryPrice)/self.tickSize>self.bracketsModifier[1][0]*self.tpInTicks:
    #                 if self.bracketsModifier[1][1]>0:
    #                     self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[1][1]
    #                     self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize   
    #                 else:
    #                     self.followingSlinTicks = self.followingSlinTicks*abs(self.bracketsModifier[1][1])
    #                     self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize
    #                 self.nb_time_sl_moved += 1


    def moveStopLossIfLevelHitDuringLongPosition(self, currentHigh):
        # if self.nbrPassThroughTenkan >0:
        if self.nb_time_tp_moved > 0:
            for i, modifier in enumerate(self.bracketsModifier):
                if modifier == []: break
                if self.nb_time_sl_moved == i and (currentHigh-self.entryPrice)/self.tickSize>modifier[0]*self.tpInTicks: 
                    if modifier[1]>0:
                        self.followingSlinTicks = self.tpInTicks*modifier[1]
                        self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize
                    else:
                        self.followingSlinTicks = self.followingSlinTicks*abs(modifier[1])
                        self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize

                    self.nb_time_sl_moved += 1

    # def moveStopLossIfLevelHitDuringShortPosition(self, currentLow):
    #     if self.nbrPassThroughTenkan >0:
    #         if self.nb_time_sl_moved == 0 and len(self.bracketsModifier)>0: 
    #             if (self.entryPrice-currentLow)/self.tickSize>self.bracketsModifier[0][0]*self.tpInTicks:
    #                 if self.bracketsModifier[0][1]>0:
    #                     self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[0][1]
    #                     self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize   
    #                 else:
    #                     self.followingSlinTicks = self.tpInTicks*abs(self.bracketsModifier[0][1])
    #                     self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize   
    #                 self.nb_time_sl_moved += 1

    #         elif self.nb_time_sl_moved == 1 and len(self.bracketsModifier)>1: 
    #             if (self.entryPrice-currentLow)/self.tickSize>self.bracketsModifier[1][0]*self.tpInTicks:
    #                 if self.bracketsModifier[1][1]>0:
    #                     self.followingSlinTicks = self.tpInTicks*self.bracketsModifier[1][1]
    #                     self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize   
    #                 else:
    #                     self.followingSlinTicks = self.tpInTicks*abs(self.bracketsModifier[1][1])
    #                     self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize   
    #                 self.nb_time_sl_moved += 1
    
    def moveStopLossIfLevelHitDuringShortPosition(self, currentLow):
        # if self.nbrPassThroughTenkan >0:
        if self.nb_time_tp_moved > 0:
            for i, modifier in enumerate(self.bracketsModifier):
                if modifier == []: break
                if self.nb_time_sl_moved == i and (self.entryPrice-currentLow)/self.tickSize>modifier[0]*self.tpInTicks: 
                    if modifier[1]>0:
                        self.followingSlinTicks = self.tpInTicks*modifier[1]
                        self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize
                    else:
                        self.followingSlinTicks = self.followingSlinTicks*abs(modifier[1])
                        self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize

                    self.nb_time_sl_moved += 1

    def checkTenkanPassThroughDuingLongPosition(self, currentClose, currentOpen, currentTenkan):
        if currentOpen < currentTenkan and currentTenkan < currentClose and self.entryPrice < currentClose:
            self.nbrPassThroughTenkan+=1
    
    def checkTenkanPassThroughDuingShortPosition(self, currentClose, currentOpen, currentTenkan):
        if currentOpen > currentTenkan and currentTenkan > currentClose and self.entryPrice > currentClose:
            self.nbrPassThroughTenkan+=1

    def moveTragetProfitIfLevelHitDuringLongPosition(self, currentHigh, currentClose): # currentOpen, , currentTenkan):
        # if (currentHigh-self.entryPrice)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks \
        # and self.nbrPassThroughTenkan < self.nbrTimeMaxMoveTP:
        if (currentHigh-self.entryPrice)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and currentClose > self.entryPrice \
        and self.nbrPassThroughTenkan < 2 and self.nb_time_tp_moved < self.nbrTimeMaxMoveTP and self.nbrTimeMaxMoveTP and not self.trade_is_done:
            # self.nbrPassThroughTenkan+=1
            self.nb_time_tp_moved+=1
            self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks
            self.tp = self.tp + self.tpToMoveInTicks*self.tickSize   

    def moveTragetProfitIfLevelHitDuringShortPosition(self, currentLow, currentClose): # currentOpen, , currentTenkan):
        # if (self.entryPrice-currentLow)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks \
        # and self.nbrPassThroughTenkan < self.nbrTimeMaxMoveTP:
        if (self.entryPrice-currentLow)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and currentClose > self.entryPrice \
        and self.nbrPassThroughTenkan < 2 and self.nb_time_tp_moved < self.nbrTimeMaxMoveTP and not self.trade_is_done:
            # self.nbrPassThroughTenkan+=1
            self.nb_time_tp_moved+=1
            self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks
            self.tp = self.tp - self.tpToMoveInTicks*self.tickSize   

  