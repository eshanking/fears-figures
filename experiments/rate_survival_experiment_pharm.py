from seascapes_figures.classes.experiment_class import Experiment
import numpy as np
    
def make_data():
    np.random.seed(2021)
    
   #  max_doses = [100]
    max_doses = [100]
    curve_types = ['pharm']
    experiment_type = 'rate-survival'
    n_sims = 100
   #  n_sims = 1
    
    # slopes = np.array([0.4,0.5,0.6,0.7])*10**-3

    # slopes = np.array([0.4])*10**-3

   #  slopes = np.array([0.5,1,2,4])*10**-4
    slopes = np.array([2,2.5,3,3.5])*10**-4
    
    init_counts = np.zeros(16)
    init_counts[0] = 10**10
    
    options = {'doubling_time':1,
               # 'death_rate':0.0144,
               'death_rate':0.028,
            #    'mut_rate':10**-9,
               'mut_rate':1.4*10**-8,
               # 'mut_rate':10**-3,
               'carrying_cap':True,
               'max_cells':10**11,
               'n_timestep':2920,
               'init_counts':init_counts,
               # 'k_abs':0.95,
               # 'k_elim':0.00839,
               'k_elim':0,
            #    'max_dose':100,
               'dose_schedule':24,
               'pad_right':False,
               'timestep_scale':3,
               'plot':False,
            #    'ic50_data':'pyrimethamine_ic50.csv',
               'fitness_data':'estimate',
               'null_seascape':False,
               # 'null_seascape_dose':1
               # 'null_seascape_method':'sort'
               }
    
    e = Experiment(max_doses=max_doses,
                   slopes=slopes,
                   curve_types = curve_types,
                   experiment_type = experiment_type,
                   n_sims=n_sims,
                   passage = False,
                   passage_time = 96,
                   population_options=options,
                   debug=False)
    
    
    e.run_experiment()
    
    return e

if __name__ == '__main__':
    make_data()