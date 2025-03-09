import os, re
import pandas as pd
from datetime import datetime
from strategies.DTP_Strategy import DTP
from strategy_runner_2 import strategyLoop
from processing_functions import create_df
from multiprocessing import Pool, set_start_method, Manager
from processing_functions import save_object


def convertir_en_entiers(liste):
    return [[int(element) for element in sous_liste] for sous_liste in liste]

def run_strategy(combination, queue, positionSize, instrument, start_date, end_date):
    iteration, onlyUSSession, smke, timeframes, tc, forbHours, slModifiers, atrRatio, tenkanAngle = combination # windowForLevels nbr_of_points, delta_in_ticks = combination
    df_M5 = create_df(timeFramesUsedInMinutes=timeframes, instrument=instrument, start_date=start_date, end_date=end_date) #, windowForLevels=windowForLevels) #, windowForLevels=windowForLevels) #chopPeriod=chopp)
    df_M5.reset_index(inplace=True)
    strategy = DTP(df_M5[0:], timeframes, useAllEntryPoints=False, ticksCrossed=tc, tenkanCond=tenkanAngle)
                   #nbr_of_points=nbr_of_points, delta_in_ticks=delta_in_ticks) #chopValue=chopv)
    print(f'iteration n°{iteration} is running...') #: parameters: sl={sl}, tp={tp}, US_hours_only={onlyUSSession}, sm={sm} started')
    start_time = datetime.now()
    trades = strategyLoop(strategy, instrument, onlyUSSession, stopMethod=smke, feesPerTrade=1.42, 
                          positionSize=positionSize, forbiddenHours=forbHours, slModifiers=slModifiers, atrRatio=atrRatio)
    result = (iteration, [trades, onlyUSSession, smke, timeframes, tc, slModifiers, forbHours, atrRatio, tenkanAngle])#chopv, chopp])
    end_time = datetime.now()
    print(f'iteration n°{iteration} finished in {end_time-start_time}')
    queue.put(result)

if __name__ == '__main__':
    start_main_time = datetime.now()

    pd.options.mode.chained_assignment = None  # default='warn'
    set_start_method('spawn')

    trades_database = {}
    # use3UT = True
    # useAllEntryPoints = False
    positionSize = 1
    instrument = "ES"
    start_date = "2023-03-24 12:00"
    end_date = "2025-02-14 12:00"

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
        "atrRatio": [ [1.8, 1.3], [1.5, 1.5], [2, 1.4], [1.5, 2]],
        "slModifiers": [[], [[0.5, 0.15]], [[0.5, 0.00], [0.764, 0.3]]], #[0.7, 0.2], [0.6,0.12]],
        "forbiddenHours":[[]], #[7,8,11,12],
        "ticksCrossed":[0,1,2],
        "KijunExitMethod": [3], #stopMethodsForKijunExitExit==0 => no exit method used
        # "slInTicks": [[]],#[10, 20],
        # "tpInTicks": [[]], #[(25,70)], #(25,65)],
        "onlyUSSession": [False, True],
        "timeFrameUsed": [["5"], ["5", "15"]], #, ["1", "5", "15"]],
        "methodTenkanAngle":[1, 2]
    }
    params_combinations = []
    comb_to_remove = []
    iteration = 1
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
    for tenkanAngle in params["methodTenkanAngle"]:
        for atrRatio in params["atrRatio"]:
            for slModifiers in params["slModifiers"]:
                for forbHours in params["forbiddenHours"]:
                    for smke in params["KijunExitMethod"]:
                        for tc in params["ticksCrossed"]:
                            for onlyUSSession in params["onlyUSSession"]:
                                for timeframes in params["timeFrameUsed"]:
                                    comb = (iteration, onlyUSSession, smke, timeframes, tc, forbHours, slModifiers, atrRatio, tenkanAngle)
                                    params_combinations.append(comb)#, rsiVal)) #, chopVal, chopPeriod)) # windowForLevels, nbr_of_points, delta_in_ticks))
                                    iteration+=1
    print(f'number iteration to do: {iteration-1}')   
    
    filename = f"size={positionSize}_timeframe={convertir_en_entiers(params['timeFrameUsed'])}_"\
        f"KijunExitMethod={params['KijunExitMethod']}_forbiddenHours={params["forbiddenHours"]}_"\
        f"slModifiers={params["slModifiers"]}_atrRatio={params["atrRatio"]}_real.pkl"

    path = re.sub(r'[<>:"|?*]', '-', f"trade_datas/{instrument}/[{start_date}]_[{end_date}]/")
    os.makedirs(path, exist_ok=True) # Vérifier si le répertoire existe, sinon le créer
    try:
        save_object([], path+filename, sanitized=True)
        os.remove(path+filename)
        print(f"Nom de fichier: {filename}")
        print(f"Le nom de fichier est correct!")
    except OSError as err:
        print("OS error:", err)

    with Manager() as manager:
        queue = manager.Queue()

        with Pool(processes=12) as pool:
            # Envoi de plusieurs tâches au pool de processus
            tasks = [pool.apply_async(run_strategy, args=(combination, queue, positionSize, instrument, start_date, end_date)) for combination in params_combinations]
            # Attendre que toutes les tâches soient terminées
            for task in tasks: 
                task.get()

        # Récupérer les résultats de la queue
        while not queue.empty():
            iteration, data = queue.get()
            trades_database[iteration] = data
        
        end_main_time = datetime.now()
        print(f'total backtest time : {end_main_time-start_main_time}')
        print("saving data...")
        save_object(trades_database, path+filename, sanitized=True)
        print("data saved!")
