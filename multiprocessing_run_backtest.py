import pandas as pd
import strategy_runner
from datetime import datetime
from strategies.DTP_Strategy import DTP
from processing_functions import create_df_M5
from multiprocessing import Pool, set_start_method, Manager
from processing_functions import save_object

def run_strategy(combination, queue):
    iteration, sl, tp, onlyUSSession, sm, use3UT = combination #, windowForLevels, nbr_of_points, delta_in_ticks = combination
    df_M5 = create_df_M5(use3UT=use3UT) #, windowForLevels=windowForLevels) #chopPeriod=chopp)
    strategy = DTP(df_M5[0:], use3UT=use3UT, useAllEntryPoints=False)#, nbr_of_points=nbr_of_points, delta_in_ticks=delta_in_ticks) #chopValue=chopv)
    print(f'iteration n°{iteration}: parameters: sl={sl}, tp={tp}, US_hours_only={onlyUSSession}, sm={sm} started')
    start_time = datetime.now()
    trades = strategy_runner.strategyLoop(strategy, sl, tp, onlyUSSession, stopMethod=sm, feesPerTrade=1.42)
    result = (iteration, [trades, sl, tp, onlyUSSession, sm, use3UT]) #, windowForLevels, nbr_of_points, delta_in_ticks])#chopv, chopp])
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

    params = {
        # "windowForLevels": [6, 12, 24],
        # "nbr_of_points":[2, 4, 5],
        # "delta_in_ticks": [5],
        #"methodTenkanAngle":[2],
        "stopMethods": [2], # [1, 2],
        "slInTicks": [100], #25, 50]
        "tpInTicks": [(20,20), (20,30), (25,25), (30,30), (25,35), (35,35), (35,45), (25,40), (30,40), (20,40)],
        "onlyUSSession": [False],
        "use3UT": [False]
    }
    params_combinations = []
    iteration = 1
    # for windowForLevels in params["windowForLevels"]:
    #     for nbr_of_points in params["nbr_of_points"]:
    #         for delta_in_ticks in params["delta_in_ticks"]:
    for sm in params["stopMethods"]:
        #for mta in params["methodTenkanAngle"]:
        for sl in params["slInTicks"]:
            for tp in params["tpInTicks"]:
                for onlyUSSession in params["onlyUSSession"]:
                    for use3UT in params["use3UT"]:
                    #if tp/sl < 1.6: # On ne veut que des trade avec un risk ratio >= à 1
                        params_combinations.append((iteration, sl, tp, onlyUSSession, sm, use3UT)) #, windowForLevels, nbr_of_points, delta_in_ticks))
                        iteration+=1

    print(f'number iteration to do: {iteration-1}')   

    with Manager() as manager:
        queue = manager.Queue()

        with Pool(processes=10) as pool:
            # Envoi de plusieurs tâches au pool de processus
            tasks = [pool.apply_async(run_strategy, args=(combination, queue)) for combination in params_combinations]
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
        save_object(trades_database, 'trade_datas/CL/basicEntries_pivot_StrategyStop2_1contracts_2TP_1M.pkl')
        print("data saved!")
