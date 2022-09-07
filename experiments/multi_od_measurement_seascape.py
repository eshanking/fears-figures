#%%
import os
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.colors as colors
import matplotlib.cm as mplcm
import scipy.optimize as sciopt
import scipy.interpolate as sciinter
import re
from fears.utils import plotter

def logistic_pharm_curve(x,IC50,g_drugless,hill_coeff):
    """Defines the logistic dose-response curve. Use if the input is a vector of drug concentration curves

    Args:
        x (numpy array): drug concentration vector
        IC50 (float)): IC50
        g_drugless (float): drugless growth rate
        hill_coeff (float): Hill coefficient

    Returns:
        numpy array: array of growth rates
    """
    g = []

    for x_t in x:
        if x_t == 0:
            g.append(g_drugless)
        else:
            g.append(g_drugless/(1+np.exp((IC50-np.log10(x_t))/hill_coeff)))

    return g

def est_ic50(gr,dc):
    indx = np.argwhere(gr)[0][0]
    ic50 = dc[indx]
    return np.log10(ic50)


def fit_hill_curve(xdata,ydata,hc=None,debug=False,interpolate=False):
    """Fits dose-response curve to growth rate data

    Args:
        xdata (list or numpy array): drug concentration curve from plate experiment
        ydata (list or numpy array): growth rate versus drug concetration for a given replicate

    Returns:
        list: List of optimized paramters: IC50, drugless growth rate, and Hill coefficient
    """
    if interpolate:
        # interpolate data
        xd_t = xdata
        yd_t = ydata
        f = sciinter.interp1d(xdata,ydata)

        if min(xdata) == 0:
            xmin = np.log10(xdata[1]) # if xdata starts at zero, set the new xmin to be the log of the next smallest value
        else:
            xmin = np.log10(min(xdata))
        xmax = np.log10(max(xdata))

        xdata = np.logspace(xmin,xmax)
        if not xdata[0] == 0:
            xdata = np.insert(xdata,0,0) # add zero back to xdata if removed before (because of log(0) error)

        ydata = f(xdata) # interpolate new ydata points
    else:
        xd_t = xdata
        yd_t = ydata

    if hc is None: # want to estimate hill coefficient as well

        ic50_est = est_ic50(yd_t,xd_t)

        p0 = [ic50_est,ydata[-1],-0.1]

        # if ydata[0] == 0:
        #     g_drugless_bound = [0,1]
        # else:
        #     # want the estimated drugless growth rate to be very close to the value given in ydata
        #     g_drugless_bound = [ydata[0]-0.0001*ydata[0],ydata[0]+0.0001*ydata[0]]

        bounds = ([ic50_est-0.5,ydata[-1]-0.05,-0.12],[ic50_est+0.5,ydata[-1]+0.05,-0.09]) # these aren't magic numbers these are just starting parameters that happen to work

        popt, pcov = sciopt.curve_fit(logistic_pharm_curve,
                                            xdata,ydata,p0=p0,bounds=bounds)
    
    # else: # we already know the hill coefficient, estimate everything else
    #     p0 = [0,ydata[0]]

    #     # print(p0)

    #     if ydata[0] == 0:
    #         g_drugless_bound = [0,1]
    #     else:
    #         # want the estimated drugless growth rate to be very close to the value given in ydata
    #         g_drugless_bound = [ydata[0]-0.0001*ydata[0],ydata[0]+0.0001*ydata[0]]

    #     fitfun = partial(self.logistic_pharm_curve_vectorized,hill_coeff=hc)

    #     bounds = ([-5,g_drugless_bound[0]],[4,g_drugless_bound[1]])
    #     popt, pcov = scipy.optimize.curve_fit(fitfun,
    #                                         xdata,ydata,p0=p0,bounds=bounds)            

    d = {'ic50':popt[0],
        'g_drugless':popt[1],
        'hc':popt[2]}


    if debug:
        # est = [logistic_pharm_curve(x,popt[0],popt[1],popt[2]) for x in xdata]
        est = logistic_pharm_curve(xdata,popt[0],popt[1],popt[2])
        fig,ax = plt.subplots()

        xd_plot = [np.log10(x) for x in xd_t if x > 0]

        xd_plot = xd_plot + [-3]

        ax.scatter(xd_plot,yd_t,marker='*')
        ax.scatter(popt[0],popt[1]/2,color='r',marker='o')
        # ax.plot(xdata,ydata)
        ax.plot(xd_plot,est,color='black')
        # ax.set_xscale('log')

        title_t = 'IC50 = ' + str(round(popt[0],2)) + ' IC50_est = ' + str(ic50_est) + '\n hc = ' + str(round(popt[2],3)) + \
                ' g = ' + str(round(popt[1],2)) + ' y0 = ' + str(round(ydata[-1],2))

        ax.set_title(title_t)

    return d

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def logistic_growth_curve(t,r,p0,k):
    """Logistic growth equation

    Args:
        t (float): time
        r (float): growth rate
        p0 (float): starting population size
        k (float): carrying capacity

    Returns:
        float: population size at time t
    """
    p = k/(1+((k-p0)/p0)*np.exp(-r*t))

    return p

def linear_growth_curve(t,r,p0):
    return p0+r*t

def est_logistic_params(growth_curve,t,debug=False,sigma=None,mode='logistic',
                        normalize=False):
    """Estimates growth rate from OD growth curve

    Args:
        growth_curve (list or numpy array): vector of OD data
        t (list or numpy array, optional): Time vector. If None, algorithm assumes each time step is 1 s. Defaults to None.

    Returns:
        dict: Dict of logistic growth curve paramters
    """
    # interpolate negative time

    # t_ext = t[0]

    # t = [tt+t[1] for tt in t]

    # t_ext = [t_ext] + t

    # t = t_ext

    # growth_curve = [growth_curve[0]] + growth_curve

    # normalize
    if normalize:
        norm_factor = max(growth_curve)
        growth_curve = growth_curve/norm_factor
    else:
        norm_factor = 1

    # estimate cc

    cc_est = np.mean(growth_curve[-2:])

    bounds = ([10**-6,0,cc_est-cc_est*0.1],[10**-3,0.3,cc_est+cc_est*0.1])

    p0 = [10**-3,0.1,cc_est] # starting parameters

    popt, pcov = sciopt.curve_fit(logistic_growth_curve,
                                        t,growth_curve,p0=p0,sigma=sigma,
                                        bounds=bounds)

    if mode == 'best' or debug:
        popt_linear,pcov_linear = sciopt.curve_fit(linear_growth_curve,
                                            t,growth_curve,sigma=sigma)
    
    rate_indx = 0 # index of the optimized data points referring to the growth rate
    p0_indx = 1 # index of the optimized data points referring to initial population size
    carrying_cap_indx = 2 # index of the optmized data points referring to carrying capacity

    r = popt[rate_indx]
    p0 = popt[p0_indx]*norm_factor
    cc = popt[carrying_cap_indx]*norm_factor

    min_carrying_cap = 0.4

    if r < 0: # if the growth rate is negative
        r = 0
    if cc < p0: # if the carrying capacity is less than the initial population size
        r = 0
    if cc < min_carrying_cap: # if the carrying cap is less the minimum threshold
        r = 0
    if norm_factor < 0.3:
        r = 0

    if mode == 'best' or debug:
        est = [logistic_growth_curve(tt,popt[0],popt[1],popt[2]) for tt in t]

        r_lin = popt_linear[0]
        p0_lin = popt_linear[1]

        est_linear = [linear_growth_curve(tt,r_lin,p0_lin) for tt in t]

        logistic_resid = np.linalg.norm(np.array(est)-np.array(growth_curve))
        linear_resid   = np.linalg.norm(np.array(est_linear)-np.array(growth_curve))

        if mode == 'best' and (linear_resid < logistic_resid):
            r = r_lin*10
            

    d = {'gr':r,
            'OD_0':p0,
            'OD_max':cc}   

    if debug:
        if r > 0:
            fig,ax = plt.subplots()

            ax.plot(t,growth_curve)

            est = [logistic_growth_curve(tt,popt[0],popt[1],popt[2]) for tt in t]

            # r_lin = popt_linear[0]
            # p0_lin = popt_linear[1]

            # est_linear = [linear_growth_curve(tt,r_lin,p0_lin) for tt in t]

            # logistic_resid = np.linalg.norm(np.array(est)-np.array(growth_curve))
            # linear_resid   = np.linalg.norm(np.array(est_linear)-np.array(growth_curve))
            
            # if logistic_resid < linear_resid:
            ax.plot(t,est,color='red')
            ax.plot(t,est_linear,color='black')
            # print(popt[0])
            p0 = round(popt[1]*10**5)/10**5
            k = round(popt[2]*10**5)/10**5
            r = round(r*3600,2)
            title = 'rate = ' + str(r) + ' cc = ' + str(k) + ' nf = ' + str(round(norm_factor,3))
            # else:
            #     ax.plot(t,est_linear,color='green')
            #     ax.plot(t,est,color='black')
            #     r = round(r_lin*3600,2)
            #     title = 'rate = ' + str(r)
            ax.set_title(title)   

    return d,pcov

def get_background(data_dict,bg_keys):
    avg = 0
    for key in bg_keys:
        avg+=data_dict[key]
    avg = avg/len(bg_keys)
    return avg

def od_data_to_dict(df):
    """Takes an OD data file and returns a dict with each data well as a key

    OD data files refers to the type of data that is a single OD reading in time (i.e
    not timeseries data).

    Args:
        df (pandas dataframe): Parsed OD data file

    Returns:
        dict: Dict of key-value pairs where each key is a well location and each value
        is the OD reading.
    """
    rownum = 0
    d = {}

    for k0 in df['Rows']:
        for k1 in df.columns[1:]:
            if k0.isnumeric():
                key = k1+k0
            else:
                key = k0+k1
            d[key] = df[k1][rownum]
        rownum+=1

    return d                    

def parse_od_data_file(df):
    """Loads the raw OD data files and strips metadata

    OD data files refers to the type of data that is a single OD reading in time (i.e
    not timeseries data).

    Args:
        data_path (str): path to data file

    Returns:
        pandas dataframe: Formatted dataframe with metadata stripped
    """

    # get the first column as an array
    col_0 = df.columns[0]
    col_0_array = np.array(df[col_0])

    data_start_indx = np.argwhere(col_0_array=='<>')
    data_start_indx = data_start_indx[0][0]

    # the data end index should be the first NaN after the data start index
    col_0_array_bool = [pd.isna(x) for x in col_0_array]
    data_end_indx = np.argwhere(col_0_array_bool[data_start_indx:])
    data_end_indx = data_end_indx[0][0] + data_start_indx - 1

    df_filt = df.loc[data_start_indx:data_end_indx,:]

    # fix the columns
    i = 0
    columns = list(df_filt.iloc[0])
    columns_t = []
    for c in columns:
        if type(c) is not str:
            columns_t.append(str(int(c)))
        else:
            columns_t.append(c)
        i+=1
    
    columns_t[0] = 'Rows'

    df_filt.columns = columns_t

    df_filt = df_filt.drop(df_filt.index[0])
    df_filt = df_filt.reset_index(drop=True)

    return df_filt

def get_plate_paths(folder_path):
    """Gets plate data paths
    Returns:
        list: list of plate data paths
    """
    plate_files = os.listdir(path=folder_path)

    #Need to make sure we are only attempting to load .csv or .xlsx data
    plate_files = [i for i in plate_files]

    plate_files.sort()

    plate_data_paths = []

    for pf in plate_files:
        if pf != '.DS_Store':
            plate_path = folder_path + os.sep + pf
            plate_data_paths.append(plate_path)

    plate_data_paths.sort(key=natural_keys)
    return plate_data_paths

def get_data_file_paths(plate_path):
    files = os.listdir(path=plate_path)

    #Need to make sure we are only attempting to load .csv or .xlsx data
    files = [i for i in files if ('.csv' in i) or ('.xlsx' in i)]

    files.sort()

    file_data_paths = []

    for pf in files:
        if pf != '.DS_Store':
            file_path = plate_path + os.sep + pf
            file_data_paths.append(file_path)

    return file_data_paths

def get_start_time(df,col=4):

    # first start time is shaking, so we take the second (start of scan)
    f = df[df == 'Start Time'].stack().index.tolist()[1]

    row = f[0]
    date_time = df.iloc[row,col]

    yr = int(date_time[0:4])
    mon = int(date_time[5:7])
    day = int(date_time[8:10])

    hr = int(date_time[11:13])
    min = int(date_time[14:16])
    sec = int(date_time[17:19])

    dt = datetime.datetime(yr,mon,day,hour=hr,minute=min,second=sec)


    return dt

#%%
num_colors = 12
cm = cm.get_cmap('viridis',12)

cNorm  = colors.Normalize(vmin=0, vmax=num_colors-1)
scalarMap = mplcm.ScalarMappable(norm=cNorm, cmap=cm)

bg_keys = ['A12','B12','C12','D12','E12','F12','G12','H12']
drug_conc = [10000,2000,400,80,16,3.2,0.64,0.128,0.0256,0.00512,0,'control']
# folder_path = '/Users/eshanking/repos/seascapes_figures/data/08312022'
folder_path = '/Users/kinge2/repos/seascapes_figures/data/multi_od/08312022'

plate_paths = get_plate_paths(folder_path)

fig,ax_list = plt.subplots(ncols=4,nrows=4,figsize=(15,12))

count = 0

gr_lib = {}

for pp in plate_paths:

    row = int(np.floor(count/4))
    col = int(np.mod(count,4))

    ax = ax_list[row,col]

    # fig,ax = plt.subplots()

    data_paths0 = get_data_file_paths(pp)

    timeseries_dict = {}
    timeseries_dict['Time'] = []

    for p in data_paths0:

        df = pd.read_excel(p)
        t = get_start_time(df)
        df = parse_od_data_file(df)

        data_dict = od_data_to_dict(df)
        data_dict['Time'] = t

        # bg = get_background(data_dict,bg_keys)
        for key in data_dict:
            if key != 'Time':
                if key in timeseries_dict.keys():
                    od = data_dict[key]
                    timeseries_dict[key].append(data_dict[key])
                else:
                    od = data_dict[key]
                    timeseries_dict[key] = [od]
        timeseries_dict['Time'].append(t)

    # sort out time
    t_vect = timeseries_dict['Time']
    t0= t_vect[0]
    t_vect = [(t-t0).total_seconds() for t in t_vect]

    # get summary data

    replicates = ['A','B','C','D','E','F','G','H']
    conditions = np.linspace(1,12,num=12)
    conditions = [str(int(c)) for c in conditions]

    data_avg = {}
    data_std = {}

    for t in range(len(data_paths0)):
        for c in conditions:
            d = []
            for r in replicates:
                key = r + c
                od = timeseries_dict[key][t]
                d.append(od)

            if c in data_avg.keys():
                data_avg[c].append(np.mean(d))
                data_std[c].append(np.std(d))
            else:
                data_avg[c] = [np.mean(d)]
                data_std[c] = [np.std(d)]

    # for key in timeseries_dict:
    #     if key != 'Time':
    #         drug_indx = int(key[1:])
    #         dc = drug_conc[drug_indx-1]
    #         color = cmap[drug_indx-1]
    #         ax.scatter(t_vect,timeseries_dict[key],color=color,label=str(dc))
    grl_t_est = []
    grl_t_err = []

    for c in conditions:

        # curve fit

        d,pcov = est_logistic_params(data_avg[c],t_vect,#sigma=data_std[c],
                                     debug=False,mode='logistic')

        drug_indx = int(c)-1
        dc = drug_conc[drug_indx]
        color = scalarMap.to_rgba([drug_indx])
        # ax.errorbar(t_vect,data_avg[c],yerr=data_std[c],label=c,color=color,fmt='*')
        ax.errorbar(t_vect,data_avg[c],label=c,color=color,fmt='*')

        # plot curve fit
        # if d['gr'] != 0:
        cf = [logistic_growth_curve(t,d['gr'],d['OD_0'],d['OD_max']) for t in t_vect]
        ax.plot(t_vect,cf,color=color)
        
        # if c not in grl_t_est.keys():
        grl_t_est.append(d['gr'])
        err = np.sqrt(np.diag(pcov))[0]
        grl_t_err.append(err)
    
    grl_t = {'avg':grl_t_est,
             'err':grl_t_err}
    
    gr_lib[str(count)] = grl_t

    handles, labels = ax.get_legend_handles_labels()

    # ax.legend(handles[0:12], labels[0:12])
    ax.set_title(str(count))
    count += 1

# plot dose-response curves
plt.tight_layout()

cc = plotter.gen_color_cycler()

#%%
fig2,ax2 = plt.subplots()
ax2.set_prop_cycle(cc)


for key in gr_lib:
    gr_t = [g*3600 for g in gr_lib[key]['avg'][0:-1]]

    dc_log = drug_conc

    dc_log = [dc for dc in dc_log if type(dc) != str]

    dc_log = [np.log10(dc) for dc in dc_log if dc > 0]

    dc_log = dc_log + [-3]

    ax2.plot(dc_log,gr_t)


plt.show()
xtl = ax2.get_xticklabels()
xt = ax2.get_xticks()
# xtl_new = xtl
xtl[1].set_text('nd')
ax2.set_xticks(xt)
ax2.set_xticklabels(xtl)

ax2.set_xlim(-3,4)

# ax2.set_xlim(0,10**4)

#%%

seascape_lib = {}
for key in gr_lib:
    
    gr_t = gr_lib[key]['avg'][0:-1]
    gr_t = [gr*3600 for gr in gr_t]

    dc = [d for d in drug_conc if type(d) != str]

    d = fit_hill_curve(dc,gr_t,debug=False,interpolate=False)
    seascape_lib[key] = d

fig3,ax3 = plt.subplots(figsize=(8,6))
ax3.set_prop_cycle(cc)

for key in seascape_lib:
    dc_fit = np.logspace(-3.5,4)
    
    ic50 = seascape_lib[key]['ic50']
    g_drugless = seascape_lib[key]['g_drugless']
    hc = seascape_lib[key]['hc']

    g_est = logistic_pharm_curve(dc_fit,ic50,g_drugless,hc)

    ax3.plot(dc_fit,g_est,linewidth=2,label=int(key))

ax3.set_xscale('log')

ax3.set_ylabel('Growth rate ($hr^{-1}$)',fontsize=15)
ax3.set_xlabel('Drug Concentration (ug/mL)',fontsize=15)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

ax3.tick_params(axis='both', labelsize=12)
ax3.legend(loc=(1,0),frameon=False)
# ax3.tick_params(axis='both', which='minor', labelsize=8)

#%%
fig.savefig('logistic_growth_fit.pdf')
fig2.savefig('new_seascape.pdf',bbox_inches='tight')
fig3.savefig('e_coli_seascape.pdf')
# %%
