import os
import matplotlib.pyplot as plt
import numpy as np
from fears.utils import results_manager
import pandas as pd
import pickle


def make_fig(adh_exp=None,exp_info_path=None):
    # suffix = '11182021_0001' # lab machine
    # suffix = '11112021_0000' # macbook
    
    # if suffix is None: 
    #     data_folder = adh_exp.results_path
    #     exp_info_file = adh_exp.experiment_info_path
    # else:
    #     data_folder = 'results_' + suffix
    #     exp_info_file = 'experiment_info_' + suffix + '.p'

    if adh_exp is None:
        adh_exp = pickle.load(open(exp_info_path,'rb'))
    
    fig,ax = plt.subplots(nrows=1,ncols=3,figsize=(8,2.5))
    
    # if suffix is None:
    #     exp_folders,exp_info = results_manager.get_experiment_results(exp=adh_exp)
    # else:
    #     exp_folders,exp_info = results_manager.get_experiment_results(suffix=suffix)
    exp_folders,exp_info = results_manager.get_experiment_results(exp=adh_exp)

    max_cells = exp_info.populations[0].max_cells
    n_timestep = exp_info.population_options['n_timestep']
    n_sims = exp_info.n_sims
    p_drop = exp_info.prob_drops
    
    exp_folders.reverse()
    p_drop = np.flip(p_drop)
    
    pop = exp_info.populations[0]
    
    km_data = {'survival':{},
               'resistance 0010':{},
               'resistance 0110':{}}
    #%%


    for exp in exp_folders:
        
        p_drop_t = exp[exp.find('=')+1:]
        p_drop_t = p_drop_t.replace(',','.')
        p_drop_t = float(p_drop_t)
        
        num = np.argwhere(p_drop == p_drop_t)
        num = num[0,0]
        
        sim_files = os.listdir(path=exp)
        sim_files = sorted(sim_files)
        
        # KM data 
        death_event_obs = np.zeros(n_sims)
        death_event_times = np.zeros(n_sims)
        
        # time to genotype 2
        gen2_resistance_obs = np.zeros(n_sims)
        gen2_resistance_times = np.zeros(n_sims)
        
        # time to genotype 6
        gen7_resistance_obs = np.zeros(n_sims)
        gen7_resistance_times = np.zeros(n_sims)
        
        k=0

        while k < len(sim_files):
        # while k < 10:
            sim = sim_files[k]
            sim = exp + os.sep + sim
            data_dict = results_manager.get_data(sim)
            data = data_dict['counts']
            
            death_event_obs[k],death_event_times[k] = \
                exp_info.extinction_time(pop,data,thresh=1)
                
            gen7_resistance_obs[k],gen7_resistance_times[k] = \
                exp_info.resistance_time(pop,data,7,thresh=.1)
    
            gen2_resistance_obs[k],gen2_resistance_times[k] = \
                exp_info.resistance_time(pop,data,2,thresh=.1)
                
            k+=1

        
        ax[0] = pop.plot_kaplan_meier(death_event_times,
                                          ax=ax[0],
                                          n_sims=n_sims,
                                          label=str(p_drop_t),
                                          mode='survival')

        ax[1] = pop.plot_kaplan_meier(gen2_resistance_times,
                                          ax=ax[1],
                                          n_sims=n_sims,
                                          label=str(p_drop_t),
                                          mode='resistant')
        
        ax[2] = pop.plot_kaplan_meier(gen7_resistance_times,
                                          ax=ax[2],
                                          n_sims=n_sims,
                                          label=str(p_drop_t),
                                          mode='resistant')
        
        # ax[0].set_yscale('log')

        km_data['survival'][str(p_drop_t)] = death_event_times
        km_data['resistance 0010'][str(p_drop_t)] = gen2_resistance_times
        km_data['resistance 0110'][str(p_drop_t)] = gen7_resistance_times
            
    
    for a in ax:
        a.spines["right"].set_visible(False)
        a.spines["top"].set_visible(False)
        a = pop.x_ticks_to_days(a)
        a.set_xlabel('Days')
        
    ax[2].legend(frameon=False,loc=[1.1,.3],title='$p_{forget}$',fontsize=8,ncol=1)
    
    pad = 0.05
    
    ax[0].set_ylabel('% surviving')
    pos1 = ax[1].get_position()
    pos1.x0 = pos1.x0 + pad
    pos1.x1 = pos1.x1 + pad
    ax[1].set_position(pos1)
    
    pos2 = ax[2].get_position()
    pos2.x0 = pos2.x0 + pad*2
    pos2.x1 = pos2.x1 + pad*2
    ax[2].set_position(pos2)
    
    ax[0].set_title('Survival of infectious agent',fontsize=8)
    ax[1].set_title('Resistant genotype = 0010',fontsize=8)
    ax[2].set_title('Resistant genotype = 0111',fontsize=8)
    results_manager.save_fig(fig,'nonadherance_km_curve.pdf',bbox_inches='tight')

    return

#%%  perform pairwise log-rank tests and compute p values

    # analysis_keys = list(km_data.keys()) # endpoints being analyzed
    # experiment_keys = [str(p) for p in p_drop] # experiments performed
    
    # comparisons = [] # vector of all pairwise comparisons without duplicates
    
    # for i in range(len(experiment_keys)):
    #     j = i+1
    #     while j < len(experiment_keys):
    #         pair = (p_drop[i],p_drop[j])
    #         j+=1
    #         comparisons.append(pair)
    
    # p_values = {'survival':{},
    #             'resistance 0010':{},
    #             'resistance 0110':{}}
    
    # for ak in  analysis_keys:
    #     for pair in comparisons:
    #         key0 = str(pair[0])
    #         key1 = str(pair[1])
    #         sr = exp_info.log_rank_test(km_data[ak][key0],km_data[ak][key1])
    #         p_values[ak][str(pair)] = float(sr.p_value)#*n_tests # Mutliple hypothesis testing correction
    
    # p_values = pd.DataFrame(p_values)
    # result_path = dir_manager.make_resultspath_absolute(
    #     'nonadherance_km_curves_p_values.csv')
    
    # p_values.to_csv(result_path)
    
# if __name__ == '__main__':
#     make_fig() 

# def unpack(sim_path):

#     data_dict = pickle.load(open(sim_path,'rb'))
#     counts = data_dict['counts']
#     drug_conc = data_dict['drug_curve']
#     regimen = data_dict['regimen']

#     return counts, drug_conc, regimen