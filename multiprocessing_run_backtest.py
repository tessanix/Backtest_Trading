import pandas as pd
import strategy_runner
from datetime import datetime
from strategies.DTP_Strategy import DTP
from processing_functions import create_df_M5
from multiprocessing import Pool, set_start_method, Manager
from processing_functions import save_object

def run_strategy(combination, strategy, queue):
    iteration, sl, tp, onlyUSSession, sm = combination
    print(f'iteration n°{iteration}: parameters: sl={sl}, tp={tp}, US_hours_only={onlyUSSession}, sm={sm} started')
    start_time = datetime.now()
    trades = strategy_runner.strategyLoop(strategy, sl, tp, onlyUSSession, stopMethod=sm)
    result = (iteration, [trades, sl, tp, onlyUSSession, sm])
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
        "stopMethods": [2], # [1, 2],
        "slInTicks": [50, 75, 100],
        "tpInTicks": [15, 20, 25, 30, 35, 50],
        "onlyUSSession": [False] 
    }
    params_combinations = []
    iteration = 1
    for sm in params["stopMethods"]:
        for sl in params["slInTicks"]:
            for tp in params["tpInTicks"]:
                for onlyUSSession in params["onlyUSSession"]:
                    #if tp/sl < 1.6: # On ne veut que des trade avec un risk ratio >= à 1
                        params_combinations.append((iteration, sl, tp, onlyUSSession, sm))
                        iteration+=1

    print(f'number iteration to do: {iteration-1}')   

    df_M5 = create_df_M5()
    strategy = DTP(df_M5[0:350_000], use3UT=False, useAllEntryPoints=False)

    with Manager() as manager:
        queue = manager.Queue()

        with Pool(processes=14) as pool:
            # Envoi de plusieurs tâches au pool de processus
            tasks = [pool.apply_async(run_strategy, args=(combination, strategy, queue)) for combination in params_combinations]
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
        save_object(trades_database, 'trade_datas/basicEntries_1UT_levels_StrategyStop2_multiprocess.pkl')
        print("data saved!")
