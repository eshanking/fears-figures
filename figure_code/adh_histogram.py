import os
import matplotlib.pyplot as plt
# from matplotlib.ticker import AutoLocator
import matplotlib as mpl
import numpy as np
from fears.utils import results_manager
import pickle

def make_fig(exp=None,exp_info_path=None):

    if exp is None:
        exp = pickle.load(open(exp_info_path,'rb'))

    exp_folders,exp_info = results_manager.get_experiment_results(exp=exp)

    n_sims = exp_info.n_sims
    p_drop = exp_info.prob_drops

    exp_folders.reverse()
    p_drop = np.flip(p_drop)

    pop = exp_info.populations[0]
    
    # exp = exp_folders[2]

    pop = exp_info.populations[0]

    gap = int(pop.dose_schedule/pop.timestep_scale)
    n_scheduled_doses = int(np.ceil(pop.n_timestep/gap))

    extinct_sched = np.zeros(n_scheduled_doses)
    extinct_sched = np.array([extinct_sched])
    survived_sched = np.zeros(n_scheduled_doses)
    survived_sched = np.array([survived_sched])

    # k=0

    for exp in [exp_folders[2]]:

        sim_files = os.listdir(path=exp)
        sim_files = sorted(sim_files)

        p_drop_t = exp[exp.find('=')+1:]
        p_drop_t = p_drop_t.replace(',','.')
        p_drop_t = float(p_drop_t)
        
        num = np.argwhere(p_drop == p_drop_t)
        num = num[0,0]
        k=0
        while k < len(sim_files):

            sim = sim_files[k]
            sim = exp+ os.sep + sim
            data_dict = results_manager.get_data(sim)
            counts = data_dict['counts']
            counts = np.sum(counts,axis=1)
            # dc = data_dict['drug_curve']
            regimen = data_dict['regimen']
            dose_schedule = compute_doses(regimen,pop)
            dose_schedule = np.array([dose_schedule])

            if counts[-1]<1:
                extinct_sched = np.concatenate((extinct_sched,dose_schedule),axis=0)
            else:
                survived_sched = np.concatenate((survived_sched,dose_schedule),axis=0)
            k+=1

    extinct_sched = extinct_sched[1:,:]
    survived_sched = survived_sched[1:,:]

    # fig,ax = plt.subplots(2,1,figsize=(6.25,7.75),sharex=True)
    fig,ax = plt.subplots(figsize=(4,3))
    cmap = mpl.colors.ListedColormap(['cornflowerblue','w'])

    aspect = n_scheduled_doses/n_sims
    # aspect_surv = n_scheduled_doses/survived_sched.shape[0]

    # ax[0].imshow(extinct_sched,cmap=cmap)
    # ax[1].imshow(survived_sched,cmap=cmap)

    n_extinct = extinct_sched.shape[0]
    n_survived = survived_sched.shape[0]

    survived_hist = np.sum(survived_sched,axis=0)
    survived_hist = survived_hist/n_survived
    extinct_hist = np.sum(extinct_sched,axis=0)
    extinct_hist = extinct_hist/n_extinct

    dose_num = np.arange(len(survived_hist))
    # p = (1-float(p_drop_t))*np.ones(len(dose_num))

    ratio = np.divide(extinct_hist,survived_hist)

    ax.bar(dose_num,ratio,width=1,color='red',alpha=0.6,label='Resistant')
    ax.plot(dose_num,np.ones(len(dose_num)),'--',color='black')
 
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    ax.set_ylabel('Odds',fontsize=12)
    ax.set_xlabel('Scheduled dose',fontsize=12)

    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=12)

    results_manager.save_fig(fig,'dose_ratio_barplot.pdf',bbox_inches='tight')
    return p_drop_t



def compute_doses(regimen,pop):

    dose_schedule = pop.dose_schedule/pop.timestep_scale
    n_doses = int(np.floor(pop.n_timestep/dose_schedule))

    doses = np.zeros(n_doses)

    dose_num = 0

    for i in range(n_doses):
        if regimen[int(i*dose_schedule)] == 1:
            doses[dose_num] = 1
        dose_num += 1
    
    return doses
    
