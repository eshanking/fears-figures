import sys
import matplotlib.pyplot as plt
from cycler import cycler
import seaborn as sns
import numpy as np
import os
import math
import scipy.stats
from seascapes_figures.utils import dir_manager
# from fears.utils.experiment_class import Experiment
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
import networkx as nx
from labellines import labelLine

# from seascapes_figures.utils.fitness import logistic_pharm_curve

class Plotter():

    def __init__(self):
        return

    def gen_color_cycler(self,style=None,palette='bright',n_colors=16):
        
        if style is None:
            colors = sns.color_palette(palette)
            colors = np.concatenate((colors[0:9],colors[0:7]),axis=0)
            # colors[[14,15]] = colors[[15,14]]
            
            colors[[7,8]] = colors[[8,7]]
            
            cc = (cycler(color=colors) + 
                cycler(linestyle=['-', '-','-','-','-','-','-','-','-',
                                    '--','--','--','--','--','--','--']))
        elif style == 'solid':
            colors = sns.color_palette(palette,n_colors)
            cc = cycler(color=colors)
        return cc

    def plot_timecourse(self,pop=None,counts_t=None,title_t=None):
        
        if pop is None:
            pop = self

        if (pop.counts == 0).all() and counts_t is None:
            print('No data to plot!')
            return
        elif counts_t is None:
            counts = pop.counts
        else:
            counts = counts_t # an input other than pop overrides pop
        if title_t is not None:
            title = title_t
        else:
            title = pop.fig_title    
            
        left = 0.1
        width = 0.8
        
        if pop.plot_entropy == True:
            fig,(ax1,ax3) = plt.subplots(2,1,figsize=(6,4),sharex=True) 
            ax3.set_position([left, 0.2, width, 0.2]) # ax3 is entropy
        else:
            fig,ax1 = plt.subplots(1,1,figsize=(6,4),sharex=True)
        
        ax1.set_position([left, 0.5, width, 0.6]) # ax1 is the timecourse
                
        counts_total = np.sum(counts,axis=0)
        
        sorted_index = counts_total.argsort()
        sorted_index_big = sorted_index[-8:]
        
        cc = self.gen_color_cycler()
        
        ax1.set_prop_cycle(cc)

        color = [0.5,0.5,0.5]
        
        if pop.plot_drug_curve:
            ax2 = ax1.twinx() # ax2 is the drug timecourse
            ax2.set_position([left, 0.5, width, 0.6])
            ax2.set_ylabel('Drug Concentration \n($\u03BC$M)', color=color,fontsize=20) # we already handled the x-label with ax1
            
            drug_curve = pop.drug_curve
            
            ax2.plot(drug_curve, color='black', linewidth=2.0)
            ax2.tick_params(axis='y', labelcolor=color)
            
            if pop.drug_log_scale:
                ax2.set_yscale('log')
                if min(drug_curve) <= 0:
                    axmin = 10**-3
                else:
                    axmin = min(drug_curve)
                ax2.set_ylim(axmin,2*max(drug_curve))
                ax2.legend(['Drug Conc.'],loc=(1.3,0.93),frameon=False,fontsize=15)
                
            else:
                ax2.set_ylim(0,1.1*max(drug_curve))
                ax2.legend(['Drug Conc.'],loc=(1.25,0.93),frameon=False,fontsize=15)

                
            ax2.tick_params(labelsize=15)
            ax2.set_title(title,fontsize=20)
            
        for allele in range(counts.shape[1]):
            if allele in sorted_index_big:
                ax1.plot(counts[:,allele],linewidth=3.0,label=str(pop.int_to_binary(allele)))
            else:
                ax1.plot(counts[:,allele],linewidth=3.0,label=None)
                
        ax1.legend(loc=(1.25,-.12),frameon=False,fontsize=15)
            
        ax1.set_xlim(0,pop.x_lim)
        ax1.set_facecolor(color='w')
        ax1.grid(False)

        ax1.set_ylabel('Cells',fontsize=20)
        ax1.tick_params(labelsize=15)
        
        if pop.plot_entropy == True:
            e = pop.entropy(counts)
            
            ax3.plot(e,color='black')
            ax3.set_xlabel('Time',fontsize=20)
            ax3.set_ylabel('Entropy',fontsize=20)
            if pop.entropy_lim is not None:
                ax3.set_ylim(0,pop.entropy_lim)
            ax3.tick_params(labelsize=15)
        
        if pop.y_lim is not None:
            y_lim = pop.y_lim
        else:
            y_lim = np.max(counts) + 0.05*np.max(counts)
        
        if pop.counts_log_scale:
            ax1.set_yscale('log')
            # ax1.set_ylim(1,5*10**5)
        else:
            ax1.set_ylim(0,y_lim)
        
        xlabels = ax1.get_xticks()
        xlabels = xlabels*pop.timestep_scale
        xlabels = xlabels/24
        xlabels = np.array(xlabels).astype('int')
        ax1.set_xticklabels(xlabels)
        ax1.set_xlabel('Days',fontsize=20)

        plt.show()
        return fig

    def plot_fitness_curves(self,pop=None,
                            fig_title='',
                            plot_r0 = False,
                            save=False,
                            savename=None,
                            fig=None,
                            ax=None,
                            labelsize=15,
                            linewidth=3,
                            show_legend=True,
                            show_axes_labels=True,
                            raw_data = False,
                            color_kwargs={}):
        
        if pop is None:
            pop = self

        if pop.fitness_data == 'estimate':
            
            gl = pop.growth_rate_library
            xdata = gl['drug_conc']

            fig, ax = plt.subplots(figsize = (10,6))

            cc = self.gen_color_cycler(**color_kwargs)
            ax.set_prop_cycle(cc)

            if raw_data:

                for g in range(pop.n_genotype):

                    f = gl[str(g)]
                    f = [x*60**2 for x in f]
                    ax.scatter(xdata,f,label = str(pop.int_to_binary(g)),linewidth=linewidth) 

            
            else:
                if min(xdata) == 0:
                    xmin = np.log10(xdata[1])
                else:
                    xmin = np.log10(min(xdata))
                xmax = np.log10(max(xdata))

                xdata = np.logspace(xmin,xmax)
                if not xdata[0] == 0:
                    xdata = np.insert(xdata,0,0)
                sl = pop.seascape_library

                for g in range(pop.n_genotype):
                    
                    f = []
                    sl_t = sl[str(g)]
                    ic50 = sl_t['ic50']

                    for c in xdata:
                        
                        # f_t = pop.logistic_pharm_curve(c,ic50,sl_t['g_drugless'],sl_t['hill_coeff'])
                        f_t = pop.sl_to_fitness(g,c)
                        f_t = f_t*(60**2)
                        f.append(f_t)
                        

                    ax.plot(xdata,f,label = str(pop.int_to_binary(g)),linewidth=linewidth) 

            ax.set_xscale('log')
            
            ax.tick_params(labelsize=labelsize)
            ax.set_ylabel('Growth rate (hr$^-1$)',fontsize=labelsize)
            ax.set_xlabel('Drug concentration (ug/ml)',fontsize=labelsize)

            if show_legend:
                ax.legend(fontsize=labelsize,frameon=False,loc=(1.08,-0.08))

        else:
            if ax is None:
                fig, ax = plt.subplots(figsize = (10,6))
            
            conc = np.logspace(-3,5,200)
            
            cc = self.gen_color_cycler(**color_kwargs)
            
            ax.set_prop_cycle(cc) 
            
            fit = np.zeros((pop.n_genotype,conc.shape[0]))
            
            for j in range(conc.shape[0]):
                fit[:,j] = pop.gen_fit_land(conc[j])
            
            if plot_r0:
                fit = fit-pop.death_rate
                ylabel = '$R_{0}$'
                thresh = np.ones(conc.shape)
                ax.plot(conc,thresh,linestyle='dashdot',color='black',linewidth=linewidth)
            else:
                ylabel = 'Growth Rate'
            
            for gen in range(pop.n_genotype):
                ax.plot(conc,fit[gen,:],linewidth=linewidth,label=str(pop.int_to_binary(gen)))
            
            if show_legend:
                ax.legend(fontsize=labelsize,frameon=False,loc=(1,-.10))
            
            ax.set_xscale('log')
            
            ax.set_title(fig_title,fontsize=labelsize)
            
            ax.tick_params(labelsize=labelsize)
            
            if show_axes_labels:
                ax.set_xlabel('Drug concentration ($\mathrm{\mu}$M)',fontsize=labelsize)
                ax.set_ylabel(ylabel,fontsize=labelsize)
            ax.set_frame_on(False)
            
            if save:
                if savename is None:
                    savename = 'fitness_seascape.pdf'
                r = dir_manager.get_project_root()
                savename = str(r) + os.sep + 'figures' + os.sep + savename
                plt.savefig(savename,bbox_inches="tight")
        
        return fig,ax

    def plot_msw(self,wt,pop=None,conc=None,fc=None,ncols=2,figsize=(2.5,8),labelsize=10,ticklabelsize=10):
        """
        plot_msw: method for plotting mutant selection window figures.

        Parameters
        ----------
        pop : population_class object
            
        fitness_curves : numpy array
            Columns 1-N represents a genotype that is a neighbor of column 0 
            (ancestor). Rows represent drug concentration.
        conc : numpy array
            Drug concentration used to calculate fitness_curves
        genotypes : list of ints
            Genotypes that were used to calculate the fitness_curves.
        save : bool
        
        Returns
        -------
        fig : figure object
            MSW figures

        """
        if pop is None:
            pop = self

        if conc is None:
            conc = np.logspace(-3,5,1000)
        if fc is None:
            fc =  pop.gen_fitness_curves(conc=conc)

        rows = int((pop.n_allele)/ncols)

        fig, ax = plt.subplots(rows,ncols,figsize=figsize)
        
        neighbors = pop.gen_neighbors(wt)
        wt_fitness_curve = fc[wt]

        i = 0

        if ax.ndim == 1:
            if rows > 1:
                for r in range(rows):
                    # for col in range(ncols):
                    n = neighbors[i]
                    wtlabel = pop.int_to_binary(wt)
                    ax[r].plot(conc,wt_fitness_curve,label=wtlabel,linewidth=3,color='snow')
                    
                    bitstring = pop.int_to_binary(n)    
                    ax[r].plot(conc,fc[n],label=bitstring,linewidth=3,color='black')

                    msw_left,msw_right = self.get_msw(wt_fitness_curve,fc[n],conc)
                    ax[r].axvspan(msw_left, msw_right, 
                            facecolor='#2ca02c',alpha=0.7)
                            # label='MSW')
                    ax[r].axvspan(min(conc),msw_left, 
                            facecolor='#ff7f00',alpha=0.7)
                            # label='MSW')
                    ax[r].axvspan(msw_right,max(conc), 
                            facecolor='#e41a1c',alpha=0.7)
                            # label='MSW')
                    ax[r].set_xscale('log')
                    ax[r].set_xlim([10**pop.drug_conc_range[0],10**pop.drug_conc_range[1]])
                    ax[r].legend(fontsize=10,frameon=False,loc='upper right')
                    self.shifty(ax[r],i*-0.02)
                    i+=1
                for r in range(rows):
                    # ax[r,0].set_ylabel('$R_{0}$',fontsize=10)
                    ax[r].set_ylabel('Growth rate \n(hr$^-1$)',fontsize=labelsize)
                # for c in range(rows):
                #     ax[c].set_xlabel('Drug concentration \n($\mathrm{\mu}$M)',
                #                           fontsize=15)
                    # for col in range(ncols):
                    ax[-1].set_xlabel('Drug concentration \n($\mathrm{\mu}$M)',
                                            fontsize=labelsize)
            elif ncols >1:
                for col in range(ncols):
                    n = neighbors[i]
                    wtlabel = pop.int_to_binary(wt)
                    ax[col].plot(conc,wt_fitness_curve,label=wtlabel,linewidth=3)
                    
                    bitstring = pop.int_to_binary(n)    
                    ax[col].plot(conc,fc[n],label=bitstring,linewidth=3)

                    msw_left,msw_right = self.get_msw(wt_fitness_curve,fc[n],conc)
                    ax[col].axvspan(msw_left, msw_right, 
                            facecolor='#2ca02c',alpha=0.7)
                            # label='MSW')
                    ax[col].axvspan(min(conc),msw_left, 
                            facecolor='#ff7f00',alpha=0.7)
                            # label='MSW')
                    ax[col].axvspan(msw_right,max(conc), 
                            facecolor='#e41a1c',alpha=0.7)
                            # label='MSW')
                    ax[col].set_xscale('log')
                    ax[col].set_xlim([10**pop.drug_conc_range[0],10**pop.drug_conc_range[1]])
                    ax[col].legend(fontsize=10,frameon=False,loc='upper right')
                    self.shiftx(ax[col],i*0.01)
                    i+=1
                for col in range(ncols):
                    ax[0].set_ylabel('Growth rate \n(hr$^-1$)',fontsize=labelsize)
                    ax[col].set_xlabel('Drug concentration \n($\mathrm{\mu}$M)',
                                            fontsize=labelsize)
        
        else:
            for r in range(rows):
                for col in range(ncols):
                    n = neighbors[i]
                    wtlabel = pop.int_to_binary(wt)
                    ax[r,col].plot(conc,wt_fitness_curve,label=wtlabel,linewidth=3)
                    
                    bitstring = pop.int_to_binary(n)    
                    ax[r,col].plot(conc,fc[n],label=bitstring,linewidth=3)

                    msw_left,msw_right = self.get_msw(wt_fitness_curve,fc[n],conc)
                    ax[r,col].axvspan(msw_left, msw_right, 
                            facecolor='#2ca02c',alpha=0.7)
                            # label='MSW')
                    ax[r,col].axvspan(min(conc),msw_left, 
                            facecolor='#ff7f00',alpha=0.7)
                            # label='MSW')
                    ax[r,col].axvspan(msw_right,max(conc), 
                            facecolor='#e41a1c',alpha=0.7)
                            # label='MSW')
                    ax[r,col].set_xscale('log')
                    ax[r,col].set_xlim([10**pop.drug_conc_range[0],10**pop.drug_conc_range[1]])
                    ax[r,col].legend(fontsize=10,frameon=False,loc='upper right')
                i+=1
            
            for r in range(rows):
                # ax[r,0].set_ylabel('$R_{0}$',fontsize=10)
                ax[r,0].set_ylabel('Replication \nrate',fontsize=labelsize)
            # for c in range(rows):
            #     ax[c].set_xlabel('Drug concentration \n($\mathrm{\mu}$M)',
            #                           fontsize=15)
            for col in range(ncols):
                ax[-1,col].set_xlabel('Drug concentration \n($\mathrm{\mu}$M)',
                                        fontsize=labelsize)
            
        for a in ax:
            a.tick_params(axis='both',labelsize=ticklabelsize)
            
        """
        n_genotype = pop.n_genotype
        rows = int((n_genotype-1)/2)
        fig, ax = plt.subplots(rows,2)
        g = 1
        wt_fitness_curve = fitness_curves[:,0]
        for r in range(rows):
            for col in range(2):
            
                ax[r,col].plot(conc,wt_fitness_curve,label='wt',linewidth=3)
                
                cur_fitness_curve = fitness_curves[:,g]
                gt = genotypes[g]
                bitstring = pop.int_to_binary(gt)    
                ax[r,col].plot(conc,cur_fitness_curve,label=bitstring,linewidth=3)
                
                msw_left_assigned = False
                msw_right_assigned = False
                if wt_fitness_curve[0] > cur_fitness_curve[0] \
                    and any(cur_fitness_curve>wt_fitness_curve):
                    for c in range(len(conc)):
                        if wt_fitness_curve[c] < cur_fitness_curve[c] \
                            and msw_left_assigned is False:
                            msw_left = conc[c]
                            msw_left_assigned = True
                        if (cur_fitness_curve[c] < 1 
                            and msw_right_assigned is False):
                            msw_right = conc[c]
                            msw_right_assigned = True
                    if msw_left < msw_right:
                        ax[r,col].axvspan(msw_left, msw_right, 
                                        facecolor='#2ca02c',alpha=0.5,
                                        label='MSW')
                
                ax[r,col].set_xscale('log')
                ax[r,col].legend(fontsize=10,frameon=False)

                g+=1
                
        for r in range(rows):
            ax[r,0].set_ylabel('$R_{0}$',fontsize=10)
        for c in range(2):
            ax[rows-1,c].set_xlabel('Drug concentration ($\mathrm{\mu}$M)',
                                fontsize=10)
        if save:
            r = dir_manager.get_project_root()
            savename = str(r) + os.sep + 'figures' + os.sep + 'msw.pdf'
            plt.savefig(savename,bbox_inches="tight")
        """
        return fig

    def plot_timecourse_to_axes(self,
                            counts,
                            counts_ax,
                            pop=None,
                            drug_curve=None,
                            drug_curve_label='Drug Concentration \n($\u03BC$M)',
                            drug_curve_legend_label = None,
                            # drug_curve_linestyle='--',
                            drug_ax_sci_notation=False,
                            drug_ax=None,
                            labelsize=15,
                            linewidth=3,
                            legend_labels = True,
                            label_lines = False,
                            select_labels=None,
                            label_xpos = None,
                            grayscale=False,
                            legend_size=8,
                            color_kwargs = {},
                            drug_kwargs = {},
                            label_kwargs={},
                            **kwargs):
        """
        Plots simulation timecourse to user defined axes (counts_ax).

        Parameters
        ----------
        pop : Population class object
            Population class object containing population visualization options.
        counts : numpy array
            Simulation data to be plotted.
        counts_ax : matplotlib axes object
            Axes on which data is plotted.
        drug_curve : numpy array, optional
            Optional drug concentration curve to plot. Requires additional drug
            axes. The default is None.
        drug_ax : matplotlib axes, optional
            Axes on which drug curve is plotted. The default is None.
        labelsize : float, optional
            Font size of the labels. The default is 15.
        linewidth : float, optional
            Width parameter passed to matplotlib plot function. The default is 3.

        Raises
        ------
        Exception
            Error given if no drug axes are provided but the drug curve is not 
            None (drug data needs drug axes to plot to).

        Returns
        -------
        counts_ax : matplotlib axes
            Axes with counts data plotted.
        drug_ax : matplotlib axes
            Axes with drug curve data plotted.

        """
        if pop is None:
            pop = self

        counts_total = np.sum(counts,axis=0)
        sorted_index = counts_total.argsort()
        sorted_index_big = sorted_index[-legend_size:]
        
        # print(sorted_index_big)
        if grayscale is False:     
            cc = self.gen_color_cycler(**color_kwargs)
            counts_ax.set_prop_cycle(cc)
        
        if drug_curve is not None:
            if 'color' in drug_kwargs:
                color = drug_kwargs['color']
            else:
                color='black'
            if drug_ax is None:
                drug_ax = counts_ax.twinx() # ax2 is the drug timecourse
                if drug_curve_label is None:
                    yax_label = ''
                else:
                    yax_label = drug_curve_label

                drug_ax.set_ylabel(yax_label, 
                                color=color,fontsize=labelsize)
                
            drug_ax.plot(drug_curve,zorder=0,**drug_kwargs)
            
            if pop.drug_log_scale:
                drug_ax.set_yscale('log')
                if min(drug_curve) <= 0:
                    axmin = 10**-3
                else:
                    axmin = min(drug_curve)
                drug_ax.set_ylim(axmin,2*max(drug_curve))
            else:
                drug_ax.set_ylim(0,1.1*max(drug_curve))
                
            # drug_ax.yaxis.label.set_color('gray')
            drug_ax.tick_params(labelsize=labelsize,color=color)
            plt.setp(drug_ax.get_yticklabels(), color=color)
            if drug_ax_sci_notation:
                drug_ax.ticklabel_format(style='scientific',axis='y',
                                        scilimits=(0,3))
        
        for genotype in range(counts.shape[1]):
            if genotype in sorted_index_big:
                if legend_labels:
                    # print(genotype)
                    counts_ax.plot(counts[:,genotype],linewidth=linewidth,
                                zorder=10,
                                label=str(pop.int_to_binary(genotype)),
                                **kwargs)
                else:
                    counts_ax.plot(counts[:,genotype],linewidth=linewidth,
                                zorder=10,
                                **kwargs)
            else:
                counts_ax.plot(counts[:,genotype],linewidth=linewidth,
                            zorder=10,
                            label=None)
        
        if pop.counts_log_scale:
            counts_ax.set_yscale('log')
            yl = counts_ax.get_ylim()
            yl = [10**1,yl[1]]
            counts_ax.set_ylim(yl)
        
        counts_ax.set_xlim(0,pop.x_lim)
        counts_ax.set_facecolor(color='w')
        counts_ax.grid(False)
        # counts_ax.set_ylabel('Cells',fontsize=20)
        counts_ax.tick_params(labelsize=labelsize)

        xticks = counts_ax.get_xticks()
        xlabels = xticks
        xlabels = xlabels*pop.timestep_scale
        xlabels = xlabels/24
        xlabels = np.array(xlabels).astype('int')
        counts_ax.set_xticks(xticks)
        
        counts_ax.set_xticklabels(xlabels)
        
        xl = [0,len(counts[:,0])]
        counts_ax.set_xlim(xl)
        counts_ax.spines["top"].set_visible(False)
        counts_ax.spines["right"].set_visible(False)
        
        counts_ax.patch.set_alpha(0)
        if drug_ax is not None:
            drug_ax.zorder = 0
        # counts_ax.zorder = 10
        
        if label_lines:
            lines = counts_ax.get_lines()
            
            for i in range(len(label_xpos)):
                sl = select_labels[i]
                labelLine(lines[sl],label_xpos[i],
                        fontsize=5,
                        zorder=100,
                        outline_color='white',
                        outline_width=6,
                        **label_kwargs)
        
        return counts_ax, drug_ax


    def plot_landscape(self,p=None,conc=10**0,
                    fitness=None,
                    relative=True,
                    rank=True,
                    ax=None,
                    ignore_zero=False,
                    colorbar_lim=None,
                    colorbar=True,
                    node_size = 800,
                    textsize=11,
                    resize_param=0.2,
                    square=False,
                    textcolor='black',
                    cbax=None,
                    cblabel='',
                    cbloc = [0.1,0.8,0.3,0.5],
                    network_only=False, # plots just the network without any fitness data
                    edge_color='gray',
                    plot_sub_network=False,
                    sub_network=None,
                    sub_network_color='white',
                    **kwargs):
        """
        Plots a graph representation of this landscape on the current matplotlib figure.
        If p is set to a vector of occupation probabilities, the edges in the graph will
        have thickness proportional to the transition probability between nodes.
        """
        if p is None:
            p = self

        if fitness is None:
            fitness = p.gen_fit_land(conc)
        
        if relative:
            fitness = fitness-min(fitness)
            fitness = fitness/max(fitness)
            
        if ax is None:
            fig,ax=plt.subplots()
            
        if rank:
            fitness = scipy.stats.rankdata(fitness)
            cblabel = 'Rank'
        
        if ignore_zero:
            fitness_t = [f==0 for f in fitness]
            fitness[fitness==0] = 'NaN'

        if network_only:
            colorbar = False
        
        # Figure out the length of the bit sequences we're working with
        N = int(np.log2(len(fitness)))

        # Generate all possible N-bit sequences
        genotypes = np.arange(2**N)
        genotypes = [p.int_to_binary(g) for g in genotypes]

        # Turn the unique bit sequences array into a list of tuples with the bit sequence and its corresponding fitness
        # The tuples can still be used as nodes because they are hashable objects
        genotypes = [(genotypes[i], fitness[i]) for i in range(len(genotypes))]

        # Build hierarchical structure for N-bit sequences that differ by 1 bit at each level
        hierarchy = [[] for i in range(N+1)]
        for g in genotypes: hierarchy[g[0].count("1")].append(g)

        # Add all unique bit sequences as nodes to the graph
        G = nx.DiGraph()
        G.add_nodes_from(genotypes)

        # Add edges with appropriate weights depending on the TM
        TM = p.random_mutations(len(genotypes))
        for i in range(len(TM)):
            for j in range(len(TM[i])):
                if TM[i][j] != 0 and i != j:
                    G.add_edge(genotypes[i], genotypes[j], weight=1)
        

        # just using spring layout to generate an initial dummy pos dict
        pos = nx.spring_layout(G)

        # # calculate how many entires in the longest row, it will be N choose N/2
        # # because the longest row will have every possible way of putting N/2 1s (or 0s) into N bits
        maxLen = math.factorial(N) / math.factorial(N//2)**2

        # Position the nodes in a layered hierarchical structure by modifying pos dict
        y = 1
        for row in hierarchy:
            if len(row) > maxLen: maxLen = len(row)
        for i in range(len(hierarchy)):
            levelLen = len(hierarchy[i])
            # algorithm for horizontal spacing.. may not be 100% correct?
            offset = (maxLen - levelLen + 1) / maxLen
            xs = np.linspace(0 + offset / 2, 1 - offset / 2, levelLen)
            for j in range(len(hierarchy[i])):
                pos[hierarchy[i][j]] = (xs[j], y)
            y -= 1 / N
        
        labels = dict(pos)
        for k in labels.keys():
            labels[k] = k[0]
        
        xy = np.asarray([pos[v] for v in list(G)])
        
        # draw edges
        
        edgelist = list(G.edges())
        edge_pos = np.asarray([(pos[e[0]], pos[e[1]]) for e in edgelist])

        edge_colors = []
        edge_widths = []
        if plot_sub_network:
            sub_network_str = [p.int_to_binary(b) for b in sub_network]

        for e in edgelist:

            if plot_sub_network:
                if e[0][0] in sub_network_str and e[1][0] in sub_network_str:
                    edge_colors.append('black')
                    edge_widths.append(2)
            else:
                edge_colors.append(edge_color)
                edge_widths.append(1)


        edge_collection = LineCollection(
            edge_pos,
            linewidths=edge_widths,
            antialiaseds=(1,),
            linestyle='solid',
            zorder=1,
            color=edge_colors)
        edge_collection.set_zorder(1)
        ax.add_collection(edge_collection)
        
        # draw nodes
        
        if colorbar_lim is not None:
            vmin = colorbar_lim[0]
            vmax = colorbar_lim[1]
        else:
            vmin=min(fitness)
            vmax=max(fitness)

        if not network_only:
            ax.scatter(xy[:,0],xy[:,1],
                    s=node_size,
                    c=fitness,
                    vmin=vmin,
                    vmax=vmax,
                    clip_on=False,
                    **kwargs)
            
        else:
            ax.scatter(xy[:,0],xy[:,1],
                    s=node_size,
                    c='white',
                    edgecolors='black',
                    vmin=vmin,
                    vmax=vmax,
                    clip_on=False,
                    **kwargs)
        if plot_sub_network:
            if sub_network is None:
                raise ValueError('sub_network should be a list of ints')
            ax.scatter(xy[sub_network,0],xy[sub_network,1],
                    s=node_size,
                    c=sub_network_color,
                    vmin=vmin,
                    vmax=vmax,
                    clip_on=False,
                    **kwargs)
        
        # if you don't want to include nodes with fitness = 0
        if ignore_zero:
            fitness_t = np.array(fitness_t)
            indx = np.argwhere(fitness_t==True)
            for i in indx:
                ax.scatter(xy[i,0],xy[i,1],
                s=node_size,
                c='gray',
                clip_on=False,
                **kwargs)

        if textcolor is not None:
            for n, label in labels.items():
                (x, y) = pos[n]
                if not isinstance(label, str):
                    label = str(label)  # this makes "1" and 1 labeled the same
                if plot_sub_network and n[0] in sub_network_str:
                    color = 'white'
                else:
                    color = textcolor
                ax.text(
                    x,
                    y,
                    label,
                    size=textsize,
                    color=color,
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transData,
                    clip_on=True,
                )
            
        # display colorbar    
        if colorbar:
            if 'cmap' in kwargs:
                cmap=kwargs['cmap']
                sm = plt.cm.ScalarMappable(cmap=cmap, 
                                            norm=plt.Normalize(vmin = vmin, vmax=vmax))
            else:
                sm = plt.cm.ScalarMappable(norm=plt.Normalize(
                    vmin = vmin, vmax=vmax))
            sm._A = []

            cbax = ax.inset_axes(cbloc)
            cbax.set_frame_on(False)
            cbax.set_xticks([])
            cbax.set_yticks([])
            
            cb = plt.colorbar(sm,
                            drawedges=False,
                            ax=cbax,
                            location='right',
                            aspect=10)
            cb.outline.set_visible(False)
            cb.set_label(cblabel,fontsize=10)
            
            if rank:
                ticks = [min(fitness),max(fitness)]
                cb.set_ticks(ticks)
                ticks = [max(fitness),min(fitness)]
                ticks = np.array(ticks).astype('int')
                ticks = [str(t) for t in ticks]
                cb.set_ticklabels(ticks,fontsize=10)
        
        if square:
            ydata_range = max(xy[:,1])-min(xy[:,1])
            xdata_range = max(xy[:,0])-min(xy[:,0])
            ax.set_aspect(xdata_range/ydata_range)
            
        xl = ax.get_xlim()
        xrange = xl[1]-xl[0]
        xl = [xl[0]-resize_param*xrange,xl[1]+xrange*resize_param]
        ax.set_xlim(xl)
        
        yl = ax.get_ylim()
        yrange = yl[1]-yl[0]
        yl = [yl[0]-resize_param*yrange,yl[1]+yrange*resize_param]
        ax.set_ylim(yl)
        
        ax.set_axis_off()
        return ax

    def add_landscape_to_fitness_curve(self,c,ax,pop=None,
                                    vert_lines=True,
                                    position = 'top',
                                    pad = 0,
                                    vert_lines_ydata = None,
                                    width=3,
                                    height=None,
                                    vert_lines_kwargs={},
                                    **kwargs):
        
        if pop is None:
            pop = self

        if position == 'top':
            ypos = 1+pad
        elif position == 'bottom':
            ypos = -1-pad
        else:
            raise Exception('Position argument not recognized')
        
        if height is None:
            height = width

        x = self.get_pos_in_log_space(c, width)
        lax = ax.inset_axes([x[0],ypos,x[1]-x[0],height],transform=ax.transData)
        lax = self.plot_landscape(pop,c,ax=lax,
                            **kwargs)
        
        if vert_lines:
            if vert_lines_ydata is None:
                yl = ax.get_ylim()
                ydata = np.arange(yl[0],yl[1],0.1)
            else:
                ydata = vert_lines_ydata
            xdata = np.ones(len(ydata))*c
            ax.plot(xdata,ydata,'--',color='black',**vert_lines_kwargs)        
        
        return ax,lax

    def plot_population_count(self,
                            c,
                            pop=None,
                            ax=None,
                            thresh=None,
                            normalize=False,
                            max_cells=None,
                            logscale=True,
                            **kwargs):
        if pop is None:
            pop = self

        if ax is None:
            fig,ax = plt.subplots(figsize=(6,4))
        if thresh is None:
            thresh = pop.max_cells/10
        c1 = [245,100,100]
        c1 = [c/255 for c in c1]
        c2 = [100,100,245]
        c2 = [c/255 for c in c2]
        if c[-1] < thresh:
            if normalize:
                c = c/pop.max_cells
            ax.plot(c,color=c2,label='extinct',**kwargs)
        else:
            if normalize:
                c = c/pop.max_cells
            ax.plot(c,color=c1,label='resistant',**kwargs)
        
        xticks = ax.get_xticks()
        xlabels = xticks
        xlabels = xlabels*pop.timestep_scale
        xlabels = xlabels/24
        xlabels = np.array(xlabels).astype('int')
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels)
        
        if logscale:
            ax.set_yscale('log')
        
        return ax

    def plot_kaplan_meier(self,
                        event_times,
                        pop=None,
                        label=None,
                        t_max=None,
                        n_sims=None,
                        ax=None,
                        mode='resistant',
                        errorband=True,
                        **kwargs):
        if pop is None:
            pop = self

        if t_max is None:
            t_max = int(max(event_times)) # hours
        if n_sims is None:
            n_sims = pop.n_sims
            
        survival_curve = np.ones(t_max)*100
        
        for t in range(len(survival_curve)-1):

            if t>0:
                survival_curve[t] = survival_curve[t-1]

            if any(event_times==t):
                num = np.argwhere(event_times==t)
                num = num.shape[0]
                perc = 100*num/n_sims
                survival_curve[t] = survival_curve[t]-perc
    
        survival_curve[-1] = survival_curve[-2]
        if ax is None:
            fig,ax = plt.subplot(figsize=(5,7))
        
        if mode == 'resistant':
            survival_curve = 100-survival_curve
            ylabel='% resistant'
        else:
            ylabel='% survival'
        
        ax.plot(survival_curve,label=label,**kwargs)
        
        if errorband:
            # compute error bars
            # rule of succession explanation: https://en.wikipedia.org/wiki/Rule_of_succession
            err = np.zeros(t_max)
            for t in range(t_max):
                p = (np.array(survival_curve[t]) + 1)/(n_sims + 2) # uniform prior (rule of succession) 
                n = n_sims
                q = 1-p
                # standard deviation of the estimator of the parameter of a binomial distribution
                err[t] = 100*(p*q/n)**0.5 #
        
        t = np.arange(t_max)
        
        ax.fill_between(t,survival_curve-err,survival_curve+err,alpha=0.4)
        
        # xticks = ax.get_xticks()
        # xlabels = xticks
        # # xlabels = (xlabels/24)/pop.timestep_scale
        # xlabels = np.array(xlabels).astype('int')
        # ax.set_xticks(xticks)
        # ax.set_xticklabels(xlabels)
        
        # xl = [0,len(survival_curve)]
        # ax.set_xlim(xl)
        # ax.set_ylim([0,100])
        # ax.set_ylabel(ylabel)
        # ax.set_xlabel('Days')
        return ax

    def get_msw(self,wt_fitness_curve,cur_fitness_curve,conc):

        msw_left = np.argwhere(wt_fitness_curve<cur_fitness_curve)
        msw_right = \
            np.intersect1d(np.argwhere(wt_fitness_curve<0),np.argwhere(cur_fitness_curve<0))
        
        if msw_right.shape[0] == 0:
            msw_right = max(conc)
        else:
            msw_right = conc[min(msw_right)]

        if msw_left.shape[0] == 0:
            msw_left = msw_right
        else:
            msw_left = conc[min(msw_left[0])]

        

        return msw_left, msw_right

    def msw_grid(self,
                genotypes,
                pop=None,
                ax=None,
                legend=True):
        
        if pop is None:
            pop = self

        conc = np.logspace(-3,5,1000)
        fc = pop.gen_fitness_curves(conc=conc)

        # get the row height
        n_rows = len(genotypes)*pop.n_allele + len(genotypes)
        h = 1/n_rows
        ylevel = 1 # top-down illustration

        # initialize a figure with appropriate aspect ratio
        width = 6 # inches
        row_height = 0.2 # inches

        if ax is None:
            fig,ax = plt.subplots(figsize=(width,row_height*n_rows))

        for g in genotypes:
            # g is the reference genotype
            # get neighbors
            neighbors = pop.gen_neighbors(g)
            # add a line for the reference label
            label = 'Reference = ' + pop.int_to_binary(g)

            pos = (10**-3,ylevel-(0.8*h))
            ax.annotate(label,pos,xycoords='data',annotation_clip=True,fontsize=8)

            ylevel += -h

            for n in neighbors:

                msw_left, msw_right = self.get_msw(fc[g],
                                            fc[n],
                                            conc)
        
                # wt selection window
                x = [min(conc),min(conc),msw_left,msw_left]
                y = [ylevel-h,ylevel,ylevel,ylevel-h]
                wt = ax.fill(x,y,'#ff7f00',alpha=0.7,label='reference selection')

                # mutant selection window
                # print(msw_right)
                x = [msw_left,msw_left,msw_right,msw_right]
                mt = ax.fill(x,y,'#2ca02c',alpha=0.7,label='mutant selection')

                # no selection
                x = [msw_right,msw_right,max(conc),max(conc)]
                ns = ax.fill(x,y,'#e41a1c',alpha=0.7,label='net loss')

                y = np.ones(len(conc))*ylevel
                ax.plot(conc,y,color='black',linewidth=0.5)

                label = pop.int_to_binary(n)
                pos = (10**-4.5,ylevel-(0.8*h))
                ax.annotate(label,pos,xycoords='data',annotation_clip=False,fontsize=8)

                ylevel += -h
        
        ax.set_frame_on(False)
        ax.set_xscale('log')
        ax.set_xlim([10**pop.drug_conc_range[0],10**pop.drug_conc_range[1]])
        ax.set_yticks([])
        if legend:
            ax.legend()
            h, l = ax.get_legend_handles_labels()
            ax.legend(h[0:3],l[0:3],loc = (0,1),frameon=False,ncol=3)

        return ax

    
    def plot_growth_rates(self,pop=None):
        
        if pop is None:
            pop = self

        fig,ax = plt.subplots()
        df = pop.growth_rate_data

        datakeys = df.keys()
        datakeys = datakeys[2:]
        
        for key in datakeys:
            ax.plot(np.log10(df[key]))

        return fig,ax

    # Helper methods

    def get_pos_in_log_space(self,center,width):
        """
        Returns x or y coordinates to pass to inset_axes when the axis is a log 
        scale in order to make the inset axes uniform sizes.

        Parameters
        ----------
        center : float
            Center point of the axes in data points (not log-ed).
        width : float
            Visual width of the axes (in log units).

        Returns
        -------
        x : list of floats
            x[0] = left point, x[1] = right point.
            log10(x[1]-x[0]) = width

        """

        center = np.log10(center)
        x0 = center - width/2
        x1 = center + width/2
        
        x = [10**x0,10**x1]
        
        return x

    def x_ticks_to_days(self,ax,pop=None):
        if pop is None:
            pop = self

        xticks = ax.get_xticks()
        xlabels = xticks
        xlabels = xlabels*pop.timestep_scale
        xlabels = xlabels/24
        xlabels = np.array(xlabels).astype('int')
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels)
        
        x_max = pop.n_timestep
        ax.set_xlim(0,x_max)
        
        return ax

    def shiftx(self,ax,pad):
        """
        shiftx: shifts ax in the x direction by pad units

        Parameters
        ----------
        ax : matplotlib axes
            axes whose position is shifted
        pad : float
            shift amount

        Returns
        -------
        ax : matplotlib axes
            shifted axes

        """
        pos = ax.get_position()
        pos.x0 = pos.x0+pad
        pos.x1 = pos.x1+pad
        ax.set_position(pos)
        
        return ax

    def shifty(self,ax,pad):
        """
        shifty: shifts ax in the y direction by pad units

        Parameters
        ----------
        ax : matplotlib axes
            axes whose position is shifted
        pad : float
            shift amount

        Returns
        -------
        ax : matplotlib axes
            shifted axes

        """
        pos = ax.get_position()
        pos.y0 = pos.y0+pad
        pos.y1 = pos.y1+pad
        ax.set_position(pos)
        
        return ax

    def shrinky(self,ax,pad):
        """
        shrinky: shrinks axes by pad by moving the top border down

        Parameters
        ----------
        ax : matplotlib axes
            axes whose position is shifted
        pad : float
            shrink amount

        Returns
        -------
        ax : matplotlib axes
            shrunk axes

        """
        
        pos = ax.get_position()
        pos.y1 = pos.y1-pad
        ax.set_position(pos)    
        
        return ax

    # def hilo(a, b, c):
    #     if c < b: b, c = c, b
    #     if b < a: a, b = b, a
    #     if c < b: b, c = c, b
    #     return a + c

    # def complement(r, g, b):
    #     k = hilo(r, g, b)
    #     return tuple(k - u for u in (r, g, b))