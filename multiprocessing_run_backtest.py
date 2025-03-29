import os, re
import pandas as pd
from datetime import datetime
from strategies.DTP_Strategy import DTP
from strategy_runner_2 import strategyLoop
from multiprocessing import Pool, set_start_method
from processing_functions import save_object, create_df, create_us_calendar_df


def convertir_en_entiers(liste):
    return [[int(element) for element in sous_liste] for sous_liste in liste]

def run_strategy(combination, positionSize, instrument, start_date, end_date):
    start_time = datetime.now()
    # combination, positionSize, instrument, start_date, end_date = arg_list
    onlyUSSession, timeframes, bracketsModifier, slInTicks, tpInTicks, tpToMoveInTicks, percentHitToMoveTP, nbrTimeMaxMoveTP, sessionHour, \
    stopMethod, nbrTimeMaxPassThroughTenkan, percentSlAlmostHit, slModifierAfterAlmostHit, ratioDistanceKijun, calendar_events = combination 

    df = create_df(timeFramesUsedInMinutes=timeframes, instrument=instrument, start_date=start_date, end_date=end_date) #, windowForLevels=windowForLevels) #, windowForLevels=windowForLevels) #chopPeriod=chopp)
    df.reset_index(inplace=True)

    us_calendar_df = create_us_calendar_df(start_date, end_date, contains=calendar_events) if len(calendar_events) > 0 else None

    strategy = DTP(df[0:], timeframes, useAllEntryPoints=False, ticksCrossed=0, tenkanCond=2, ratioDistanceKijun=ratioDistanceKijun)
                   #nbr_of_points=nbr_of_points, delta_in_ticks=delta_in_ticks) #chopValue=chopv)
    #print(f'{datetime.now()} - iteration n°{iteration} is running...') #: parameters: sl={sl}, tp={tp}, US_hours_only={onlyUSSession}, sm={sm} started')
    trades = strategyLoop(strategy, us_calendar_df, instrument, onlyUSSession, feesPerTrade=4.36, positionSize=positionSize, forbiddenHours=[], 
                          slInTicksInitial=slInTicks, tpInTicksInitial=tpInTicks, bracketsModifier=bracketsModifier, tpToMoveInTicks=tpToMoveInTicks, percentHitToMoveTP=percentHitToMoveTP, 
                          nbrTimeMaxMoveTP=nbrTimeMaxMoveTP, usSessionHour=sessionHour, stopMethod=stopMethod, nbrTimeMaxPassThroughTenkan=nbrTimeMaxPassThroughTenkan, percentSlAlmostHit=percentSlAlmostHit, slModifierAfterAlmostHit=slModifierAfterAlmostHit)
    end_time = datetime.now()

    #print(f'{datetime.now()} - iteration n°{iteration} finished in {end_time-start_time}')
    result = (start_time.replace(microsecond=0), end_time.replace(microsecond=0), 
              [trades, onlyUSSession, timeframes, bracketsModifier, slInTicks, tpInTicks, tpToMoveInTicks, percentHitToMoveTP, nbrTimeMaxMoveTP, sessionHour, stopMethod, nbrTimeMaxPassThroughTenkan, percentSlAlmostHit, slModifierAfterAlmostHit, ratioDistanceKijun, calendar_events])#chopv, chopp])
    return result


def main():
    start_main_time = datetime.now()
    trades_database = {}
    # use3UT = True
    # useAllEntryPoints = False
    positionSize = 1
    instrument = "ES"
    start_date = "2023-03-24 12:00"
    end_date = "2025-02-10 10:00"

    params = {
        # "windowForLevels": [6, 12],
        # "nbr_of_points":[2, 3],
        # "delta_in_ticks": [5],
        # "chopPeriod":[14, 28, 48],
        # "chopValueToCross": [61.8],
        # "patternVerif": [True,False],
        # "rsiPeriod":[14, ]
        # "rsiValues": [(50, 50), (55,45)],
        # "withCrossKijunExit":[False, True],
        #"atrRatio": [ [1.8, 1.3], [1.5, 1.5], [1.5, 2]],
        # "forbiddenHours":[[]], #[7,8,11,12],
        # "ticksCrossed":[0], # 2],3
        # "methodTenkanAngle":[2]
        # "atrRatioForTp": [0], #3,5,7], 
        # "atrRatioForSl": [0], #3,5,7,8], 
        # "methodForMovingTP": [2],
        # "atrSlopeTreshold": [0.5], 
        # "maxDailyPercentLoss":[-1.0, -2.0], 
        # "maxDailyPercentProfit":[1.5, 2.0, 2.5],
        # "dojiRatio": [3.0, 5.0, 7.0],
        "ratioDistanceKijun": [0.0, 0.2, 0.4, 0.6, 0.8],
        "slModifierAfterAlmostHit":[0.1],
        "percentSlAlmostHit":[0.7],
        # "maxTimeOutsideProfitZone": [40],
        "nbrTimeMaxPassThroughTenkan":[2],
        "exitPositionMethod": [0], #stopMethodsForKijunExitExit==0 => no exit method used
        "sessionHour":[16],
        "nbrTimeMaxMoveTP":[2],
        "calendar_events": [[]], # ["CPI", "PPI", "Fed", "FOMC", "PCE"], ["Fed", "FOMC", "PCE"]],
        "percentHitToMoveTP": [0.55],
        "tpToMoveInTicks":[12],
        "bracketsModifier": [ 
            # [[]],
            # [[0.7, -0.5]],   
            # [[0.6, -0.5]],  
            [[0.6, -0.5], [0.9, 0.2]], 
            # [[0.6, -0.4], [0.7, -0.2], [0.9, 0.25]],
            [[0.6, -0.5], [0.7, -0.1], [0.95, 0.45]],
            [[0.6, -0.5], [0.7, -0.1], [0.8, 0.2], [0.92, 0.6]],
        ],
        "slInTicksBeforeSession": [50],
        "tpInTicksBeforeSession": [25],
        "slInTicksDuringSession": [55],
        "tpInTicksDuringSession": [65],
        "onlyUSSession": [False],
        "timeFrameUsed": [["1","5","15"]] 
    }
    params_combinations = []
    # comb_to_remove = []
    # iteration = 1
    #for windowForLevels in params["windowForLevels"]:
    #    for nbr_of_points in params["nbr_of_points"]:
    #        for delta_in_ticks in params["delta_in_ticks"]:
    # for chopPeriod in params["chopPeriod"]:
    #     for chopVal in params["chopValueToCross"]:
    #for pv in params["patternVerif"]:
    # for rsiVal in params["rsiValues"]:
    # for sl in params["slInTicks"]:
    #     for tp in params["tpInTicks"]:
    # for tenkanCond in params["methodTenkanAngle"]:
    #for atrRatio in params["atrRatio"]:
    # for tenkanAngle in params["methodTenkanAngle"]:
    # for tc in params["ticksCrossed"]:
    # for forbHours in params["forbiddenHours"]:
    # for methodForMovingTP in params["methodForMovingTP"]:
    # for atrRatioForSl in params["atrRatioForSl"]:
    # for atrRatioForTp in params["atrRatioForTp"]:
    # for atrSlopeTreshold in params["atrSlopeTreshold"]:
    # for maxDailyPercentLoss in params["maxDailyPercentLoss"]:
    #     for maxDailyPercentProfit in params["maxDailyPercentProfit"]:
    # for dojiRatio in params["dojiRatio"]:
    # for maxTimeOutsideProfitZone in params["maxTimeOutsideProfitZone"]:
    for ratioDistanceKijun in params["ratioDistanceKijun"]:
        for slModifierAfterAlmostHit in params['slModifierAfterAlmostHit']:
            for percentSlAlmostHit in params['percentSlAlmostHit']:
                for nbrTimeMaxPassThroughTenkan in params["nbrTimeMaxPassThroughTenkan"]:
                    for stopMethod in params["exitPositionMethod"]:
                        for sessionHour in params["sessionHour"]:
                            for nbrTimeMaxMoveTP in params["nbrTimeMaxMoveTP"]:
                                for calendar_events in params["calendar_events"]:
                                    for percentHitToMoveTP in params["percentHitToMoveTP"]:
                                        for tpToMoveInTicks in params["tpToMoveInTicks"]:
                                            for slInTicksBeforeSession in params["slInTicksBeforeSession"]:
                                                for tpInTicksBeforeSession in params["tpInTicksBeforeSession"]:
                                                    for slInTicksDuringSession in params["slInTicksDuringSession"]:
                                                        for tpInTicksDuringSession in params["tpInTicksDuringSession"]:
                                                            for bracketsModifier in params["bracketsModifier"]:
                                                                for onlyUSSession in params["onlyUSSession"]:
                                                                    for timeframes in params["timeFrameUsed"]:
                                                                        comb = (onlyUSSession, timeframes, bracketsModifier, [slInTicksBeforeSession, slInTicksDuringSession], \
                                                                                [tpInTicksBeforeSession, tpInTicksDuringSession], tpToMoveInTicks, percentHitToMoveTP, nbrTimeMaxMoveTP, \
                                                                                sessionHour, stopMethod, nbrTimeMaxPassThroughTenkan, percentSlAlmostHit, slModifierAfterAlmostHit, ratioDistanceKijun, calendar_events)
                                                                        params_combinations.append(comb)#, rsiVal)) #, chopVal, chopPeriod)) # windowForLevels, nbr_of_points, delta_in_ticks))
                                                        #iteration+=1
    
    print(f'number combinations to test: {len(params_combinations)}')  
    
    path = re.sub(r'[<>:"|?*]', '-', f"trade_datas/{instrument}/{start_date}_{end_date}/").replace(" ", "_")
    #filename = f"size={positionSize}_timeframe={convertir_en_entiers(params['timeFrameUsed'])}_newMethod3.pkl"
    filename = re.sub(r'[<>:"|?*]', '-', f"result_file_1m_{datetime.now()}.pkl").replace(" ", '_')
    # print(path)
    os.makedirs(path, exist_ok=True) # Vérifier si le répertoire existe, sinon le créer
    
    try:
        save_object([], path+filename, sanitized=True)
        os.remove(path+filename)
        print(f"Nom de fichier: {filename}")
        print(f"Le nom de fichier est correct!")
    except OSError as err:
        print("OS error:", err)
        return

    with Pool(processes=8) as pool:
        # Envoi de plusieurs tâches au pool de processus
        results = [pool.apply_async(run_strategy, args=(combination, positionSize, instrument, start_date, end_date)) for combination in params_combinations]
        # Attendre que toutes les tâches soient terminées
        for i, result in enumerate(results):
            start_time, end_time, data = result.get()
            print(f'task {i+1}: start: {start_time}, end: {end_time}, total time: {end_time-start_time}', flush=True)
            trades_database[i+1] = data


    end_main_time = datetime.now()
    print(f'total backtest time : {end_main_time-start_main_time}')
    print("saving data...")
    save_object(trades_database, path+filename, sanitized=True)
    print("data saved!")

if __name__ == '__main__':
    set_start_method('spawn')
    pd.options.mode.chained_assignment = None  # default='warn'
    main()


    # with Pool(processes=9) as pool:
    #     args_list = [(combination, positionSize, instrument, start_date, end_date) for combination in params_combinations]
    #     result = pool.map_async(run_strategy, args_list, callback=)
    
    #     for i, (start_time, end_time, data) in enumerate(result.get()):
    #         print(f'task {i+1}: task start: {start_time}, task end: {end_time}, total time: {end_time-start_time}', flush=True)
    #         trades_database[i+1] = data