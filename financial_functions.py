from values_definition import Result

def profit_for_sl_hit(followingSlinTicks, tickValue, positionSize, result):
    return followingSlinTicks*tickValue*positionSize if result==Result.WIN else -followingSlinTicks*tickValue*positionSize

def profit_for_long_stop_condition_hit(currentPrice, entryPrice, tickSize, tickValue, positionSize):
    return ((currentPrice-entryPrice)/tickSize)*tickValue*positionSize

def profit_for_short_stop_condition_hit(currentPrice, entryPrice, tickSize, tickValue, positionSize):
    return ((entryPrice-currentPrice)/tickSize)*tickValue*positionSize

def profit_for_tp_hit(tpInTicks, tickValue, positionSize):
    return tpInTicks*tickValue*positionSize