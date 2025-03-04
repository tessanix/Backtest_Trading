import pandas as pd
from datetime import datetime
from strategies.DTP_Strategy import DTP
from strategy_runner import strategyLoop
from processing_functions import create_df
from multiprocessing import Pool, set_start_method, Manager
from processing_functions import save_object

def convertir_en_entiers(liste):
    return [[int(element) for element in sous_liste] for sous_liste in liste]

def run_strategy(combination, queue, positionSize, instrument, start_date, end_date):
    iteration, sl, tp, onlyUSSession, sm, timeframes, tc, ke = combination # windowForLevels nbr_of_points, delta_in_ticks = combination
    df_M5 = create_df(timeFramesUsedInMinutes=timeframes, instrument=instrument, start_date=start_date, end_date=end_date) #, windowForLevels=windowForLevels) #, windowForLevels=windowForLevels) #chopPeriod=chopp)
    df_M5.reset_index(inplace=True)
    strategy = DTP(df_M5[0:], timeframes, useAllEntryPoints=False, ticksCrossed=tc)
                   #nbr_of_points=nbr_of_points, delta_in_ticks=delta_in_ticks) #chopValue=chopv)
    print(f'iteration n°{iteration} is running...') #: parameters: sl={sl}, tp={tp}, US_hours_only={onlyUSSession}, sm={sm} started')
    start_time = datetime.now()
    trades = strategyLoop(strategy, instrument, sl, tp, onlyUSSession, stopMethod=sm, feesPerTrade=1.42, 
                          positionSize=positionSize, withCrossKijunExit=ke)
    result = (iteration, [trades, sl, tp, onlyUSSession, sm, timeframes, tc, ke])#chopv, chopp])
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
        "withCrossKijunExit":[False, True],
        "ticksCrossed":[0, 1],
        "stopMethods": [2,3], 
        "slInTicks": [20],
        "tpInTicks": [(30,70)],
        "onlyUSSession": [True, False],
        "timeFrameUsed": [["1"], ["1", "15"], ["5", "15", "60"], ["5", "60"], ["5", "15"], ["5"]]
        #"methodTenkanAngle":[2],
    }
    params_combinations = []
    iteration = 1
    #for windowForLevels in params["windowForLevels"]:
    #    for nbr_of_points in params["nbr_of_points"]:
    #        for delta_in_ticks in params["delta_in_ticks"]:
                # for chopPeriod in params["chopPeriod"]:
                #     for chopVal in params["chopValueToCross"]:
    for sm in params["stopMethods"]:
        for tc in params["ticksCrossed"]:
            for ke in params["withCrossKijunExit"]:
                for sl in params["slInTicks"]:
                    for tp in params["tpInTicks"]:
                        for onlyUSSession in params["onlyUSSession"]:
                            for timeframes in params["timeFrameUsed"]:
                            #if tp/sl < 1.6: # On ne veut que des trade avec un risk ratio >= à 1
                                params_combinations.append((iteration, sl, tp, onlyUSSession, sm, timeframes, tc, ke)) #, chopVal, chopPeriod)) # windowForLevels, nbr_of_points, delta_in_ticks))
                                iteration+=1
    print(f'number iteration to do: {iteration-1}')   

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
        tf = convertir_en_entiers(params['timeFrameUsed'])
        tp = "Variable" if type(params["tpInTicks"][0]) == tuple else "Fixed"
        filename = f"backtest_{instrument}_from[{start_date}]_to[{end_date}]_posSize={positionSize}_timeframe={tf}"\
            f"_stopMethod={params['stopMethods']}_TP={tp}_tickCrossed={params["ticksCrossed"]}_withCrossKijunExit={params["withCrossKijunExit"]}"\
            ".pkl"
            # f"chopValueToCross={params["chopValueToCross"]}_chopPeriod={params["chopPeriod"]}" \
            #f"_windowForLevels={params['windowForLevels']}_"\
            #f"nbr_of_points={params['nbr_of_points']}_delta_in_ticks={params['delta_in_ticks']}.pkl"
        save_object(trades_database, 'trade_datas/'+filename, sanitized=True)
        print("data saved!")
