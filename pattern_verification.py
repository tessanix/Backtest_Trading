from values_definition import Trend

def isUpCandle(df, idx):
    if df.loc[idx,"close"] > df.loc[idx,"open"]:
        return True
    return False

def isDownCandle(df, idx):
    if df.loc[idx,"close"] < df.loc[idx,"open"]:
        return True
    return False


def verify_stop_by_engulfing_pattern(df, last_m15_candle_idx, actual_position, minTick):
    if actual_position == Trend.BULLISH: 
        # We want to identify a bearich engulfing here : 
        if (isUpCandle(df, last_m15_candle_idx) # derniere bougie baissière
        and isDownCandle(df, last_m15_candle_idx-1) # avant derniere bougie haussière 
        and df.loc[last_m15_candle_idx, "close"] + minTick < df.loc[last_m15_candle_idx-1, "open"] #taille de bougie supérieur à la précédente +1tick
        and df.loc[last_m15_candle_idx, "open"] > df.loc[last_m15_candle_idx-1, "close"] + minTick): 
            return True # pattern trouvé !
    elif actual_position == Trend.BEARISH:
        # We want to identify a bullish engulfing here : 
        if (isDownCandle(df, last_m15_candle_idx) # derniere bougie haussière
        and isUpCandle(df, last_m15_candle_idx-1) # avant derniere bougie baissière 
        and df.loc[last_m15_candle_idx, "close"] > df.loc[last_m15_candle_idx-1, "open"] +minTick  #taille de bougie supérieur à la précédente +1tick
        and df.loc[last_m15_candle_idx, "open"] + minTick < df.loc[last_m15_candle_idx-1, "close"]): 
            return True # pattern trouvé !
    return False # pattern non trouvé !


def verify_stop_by_3_loss_momentum(df, last_m15_candle_idx, actual_position):
    last1_m15_candle_size = abs(df.loc[last_m15_candle_idx-1, "close"] - df.loc[last_m15_candle_idx-1, "open"])
    last2_m15_candle_size = abs(df.loc[last_m15_candle_idx-2, "close"] - df.loc[last_m15_candle_idx-2, "open"])
    last3_m15_candle_size = abs(df.loc[last_m15_candle_idx-3, "close"] - df.loc[last_m15_candle_idx-3, "open"])

    if actual_position == Trend.BULLISH: 
        for i in range(1, 4):
            if not isUpCandle(df, last_m15_candle_idx-i):
                return False
        if last1_m15_candle_size < last2_m15_candle_size and last2_m15_candle_size < last3_m15_candle_size and isDownCandle(df, last_m15_candle_idx):
            return True
    elif actual_position == Trend.BEARISH: 
        for i in range(1, 4):
            if not isDownCandle(df, last_m15_candle_idx-i):
                return False
        if last1_m15_candle_size < last2_m15_candle_size and last2_m15_candle_size < last3_m15_candle_size and isUpCandle(df, last_m15_candle_idx):
            return True
    return False