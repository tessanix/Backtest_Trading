from values_definition import Result


class PositionManager():

    def __init__(self, tickValue, tickSize, positionSize, bracketsModifier, tpToMoveInTicks, 
                percentHitToMoveTP, nbrTimeMaxMoveTP, nbrTimeMaxPassThroughTenkan, percentSlAlmostHit, slModifierAfterAlmostHit, timeTPMovedToClose): #maxTimeOutsideProfitZone,
        
        self.tickValue = tickValue
        self.tickSize = tickSize
        self.positionSize = positionSize
        self.bracketsModifier = bracketsModifier
        self.tpToMoveInTicks = tpToMoveInTicks
        self.percentHitToMoveTP = percentHitToMoveTP
        self.nbrTimeMaxMoveTP = nbrTimeMaxMoveTP
        self.nbrTimeMaxPassThroughTenkan = nbrTimeMaxPassThroughTenkan
        self.percentSlAlmostHit = percentSlAlmostHit
        self.slModifierAfterAlmostHit = slModifierAfterAlmostHit
        self.timeTPMovedToClose = timeTPMovedToClose
        self.entryDate = None
        self.nbrPassThroughTenkan = None
        self.stopLossAlmostHit = None
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
        # self.maxTimeOutsideProfitZone = maxTimeOutsideProfitZone
        # self.startTimeOutsideProfitZone = None

    def set_new_trade_attributes(self, entryDate, followingSlinTicks, tpInTicks, entryPrice, sl, tp):
        self.entryDate = entryDate
        self.followingSlinTicks = followingSlinTicks
        self.tpInTicks = tpInTicks
        self.entryPrice = entryPrice
        self.sl = sl
        self.tp = tp
        self.trade_is_done = False
        self.stopLossAlmostHit = False
        self.nbrPassThroughTenkan = 0
        self.nb_time_sl_moved = 0
        self.nb_time_tp_moved = 0
    
    def reset(self):
        self.entryDate = None
        self.followingSlinTicks = None
        self.tpInTicks = None
        self.entryPrice = None
        self.exit_price = None
        self.sl = None
        self.tp = None
        self.trade_is_done = None
        self.nbrPassThroughTenkan = None
        self.stopLossAlmostHit = None
        self.nb_time_sl_moved = None
        self.nb_time_tp_moved = None
        self.profit = None
        # self.startTimeOutsideProfitZone = None
        # self.maxTimeOutsideProfitZone = None

    # def checkToMuchTimeInNoProfitZoneDuringLong(self, currentClose, prevClose, currentDate):
    #     if prevClose > self.entryPrice and currentClose < self.entryPrice: # first time going in NO PROFIT ZONE
    #         self.startTimeOutsideProfitZone = currentDate

    #     elif prevClose < self.entryPrice and currentClose > self.entryPrice: # leaving NO PROFIT ZONE
    #         self.startTimeOutsideProfitZone = None

    #     if self.startTimeOutsideProfitZone is not None and currentDate-self.startTimeOutsideProfitZone>timedelta(minutes=self.maxTimeOutsideProfitZone):
    #         return True
    #     return False
    
    # def checkToMuchTimeInNoProfitZoneDuringShort(self, currentClose, prevClose, currentDate):
    #     if prevClose < self.entryPrice and currentClose > self.entryPrice: # first time going in NO PROFIT ZONE
    #         self.startTimeOutsideProfitZone = currentDate

    #     elif prevClose > self.entryPrice and currentClose < self.entryPrice: # leaving NO PROFIT ZONE
    #         self.startTimeOutsideProfitZone = None

    #     if self.startTimeOutsideProfitZone is not None and currentDate-self.startTimeOutsideProfitZone>timedelta(minutes=self.maxTimeOutsideProfitZone):
    #         return True
    #     return False

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

        if (self.entryPrice-currentLow)/self.tickSize>self.percentSlAlmostHit*self.followingSlinTicks \
            and self.nb_time_sl_moved==0 and self.entryPrice>currentLow and not self.trade_is_done:
            self.stopLossAlmostHit = True
    

    def checkStopLossHitDuringShortPosition(self, currentHigh):
        if currentHigh >= self.sl and not self.trade_is_done:
            result = Result.WIN  if self.entryPrice > self.sl else Result.LOSS
            self.exit_price = self.sl
            self.trade_is_done = True
            self.profit = self.profit_for_sl_hit(result)

        if (currentHigh-self.entryPrice)/self.tickSize>self.percentSlAlmostHit*self.followingSlinTicks \
            and self.nb_time_sl_moved==0 and self.entryPrice<currentHigh and not self.trade_is_done:
            self.stopLossAlmostHit = True

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

    def moveStopLossIfAlmostHitDuringLongPosition(self, currentClose):
        if self.stopLossAlmostHit and self.nb_time_sl_moved==0:

            if self.slModifierAfterAlmostHit>=0:
                potentialNewSlInTicks = self.tpInTicks*self.slModifierAfterAlmostHit
                potentialNewSl = self.entryPrice + potentialNewSlInTicks*self.tickSize

                if currentClose > potentialNewSl:
                    self.followingSlinTicks = potentialNewSlInTicks
                    self.sl = potentialNewSl
                    # self.nb_time_sl_moved += 1

            else:
                potentialNewSlInTicks = self.followingSlinTicks*abs(self.slModifierAfterAlmostHit)
                potentialNewSl = self.entryPrice - potentialNewSlInTicks*self.tickSize

                if currentClose > potentialNewSl:
                    self.followingSlinTicks = potentialNewSlInTicks
                    self.sl = potentialNewSl
                    # self.nb_time_sl_moved += 1
                
    def moveStopLossIfAlmostHitDuringShortPosition(self, currentClose):
        if self.stopLossAlmostHit and self.nb_time_sl_moved==0:

            if self.slModifierAfterAlmostHit>=0:
                potentialNewSlInTicks = self.tpInTicks*self.slModifierAfterAlmostHit
                potentialNewSl = self.entryPrice - potentialNewSlInTicks*self.tickSize

                if currentClose < potentialNewSl:
                    self.followingSlinTicks = potentialNewSlInTicks
                    self.sl = potentialNewSl
                    # self.nb_time_sl_moved += 1

            else:
                potentialNewSlInTicks = self.followingSlinTicks*abs(self.slModifierAfterAlmostHit)
                potentialNewSl = self.entryPrice + potentialNewSlInTicks*self.tickSize

                if currentClose < potentialNewSl:
                    self.followingSlinTicks = potentialNewSlInTicks
                    self.sl = potentialNewSl
                    # self.nb_time_sl_moved += 1

    def moveStopLossIfLevelHitDuringLongPosition(self, currentHigh):
        if self.nb_time_tp_moved >= self.nbrTimeMaxMoveTP:
            for i, modifier in enumerate(self.bracketsModifier):
                if modifier==[]: break
                # condition = self.nb_time_sl_moved == i and (currentHigh-self.entryPrice)/self.tickSize>modifier[0]*self.tpInTicks
                if self.nb_time_sl_moved == i and (currentHigh-self.entryPrice)/self.tickSize>modifier[0]*self.tpInTicks:
                    self.nb_time_sl_moved += 1
                    if not self.stopLossAlmostHit or modifier[1] > self.slModifierAfterAlmostHit:
                        if modifier[1]>=0:
                            self.followingSlinTicks = self.tpInTicks*modifier[1]
                            self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize
                        else:
                            self.followingSlinTicks = self.followingSlinTicks*abs(modifier[1])
                            self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize


    def moveStopLossIfLevelHitDuringShortPosition(self, currentLow):
        if self.nb_time_tp_moved >= self.nbrTimeMaxMoveTP :
            for i, modifier in enumerate(self.bracketsModifier):
                if modifier==[]: break
                #condition = self.nb_time_sl_moved == i and (self.entryPrice-currentLow)/self.tickSize>modifier[0]*self.tpInTicks
                if self.nb_time_sl_moved == i and (self.entryPrice-currentLow)/self.tickSize>modifier[0]*self.tpInTicks:
                    self.nb_time_sl_moved += 1
                    if not self.stopLossAlmostHit or modifier[1] > self.slModifierAfterAlmostHit: 
                        if modifier[1]>=0:
                            self.followingSlinTicks = self.tpInTicks*modifier[1]
                            self.sl = self.entryPrice - self.followingSlinTicks*self.tickSize
                        else:
                            self.followingSlinTicks = self.followingSlinTicks*abs(modifier[1])
                            self.sl = self.entryPrice + self.followingSlinTicks*self.tickSize

    def checkTenkanPassThroughDuingLongPosition(self, currentClose, currentOpen, currentTenkan):
        if currentOpen < currentTenkan and currentTenkan < currentClose and self.entryPrice < currentClose:
            self.nbrPassThroughTenkan+=1
        # elif self.entryPrice > currentClose and self.nbrPassThroughTenkan>0:
        #     self.nbrPassThroughTenkan=0
    
    def checkTenkanPassThroughDuingShortPosition(self, currentClose, currentOpen, currentTenkan):
        if currentOpen > currentTenkan and currentTenkan > currentClose and self.entryPrice > currentClose:
            self.nbrPassThroughTenkan+=1
        # elif self.entryPrice < currentClose and self.nbrPassThroughTenkan>0:
        #     self.nbrPassThroughTenkan=0

    def moveTragetProfitIfLevelHitDuringLongPosition(self, currentHigh, currentClose, atr_ratio): 
        if (currentHigh-self.entryPrice)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and currentClose > self.entryPrice \
        and self.nbrPassThroughTenkan < self.nbrTimeMaxPassThroughTenkan and self.nb_time_tp_moved < self.nbrTimeMaxMoveTP and not self.trade_is_done:
            self.nb_time_tp_moved+=1
            self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks*atr_ratio
            self.tp = self.tp + self.tpToMoveInTicks*self.tickSize  

    def moveTragetProfitIfLevelHitDuringShortPosition(self, currentLow, currentClose, atr_ratio): 
        if (self.entryPrice-currentLow)/self.tickSize>=self.percentHitToMoveTP*self.tpInTicks and currentClose > self.entryPrice \
        and self.nbrPassThroughTenkan < self.nbrTimeMaxPassThroughTenkan and self.nb_time_tp_moved < self.nbrTimeMaxMoveTP and not self.trade_is_done:
            self.nb_time_tp_moved+=1
            self.tpInTicks = self.tpInTicks + self.tpToMoveInTicks*atr_ratio
            self.tp = self.tp - self.tpToMoveInTicks*self.tickSize

    def checkIfCanExitLongPosition(self, openPrice, closePrice, current_kijun):

        cond1 = closePrice - self.entryPrice > 0
        cond2 = self.nb_time_tp_moved>self.timeTPMovedToClose
        cond3 = openPrice > closePrice
        cond4 = closePrice < current_kijun
       
        return cond1 and cond2 and cond3 and cond4
    
    def checkIfCanExitShortPosition(self, openPrice, closePrice, current_kijun):

        cond1 = self.entryPrice - closePrice > 0
        cond2 = self.nb_time_tp_moved>self.timeTPMovedToClose
        cond3 = openPrice < closePrice
        cond4 = closePrice > current_kijun
       
        return cond1 and cond2 and cond3 and cond4