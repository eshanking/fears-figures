from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
# from seascapes_figures.utils import results_manager

def f(x, y):

    f_t = y**2*np.sqrt(x)

    return f_t

x = np.linspace(0, 1, 30)
y = np.linspace(0, 1, 30)

X, Y = np.meshgrid(x, y)
Z = f(X, Y)

Z = Z/np.max(Z)

fig = plt.figure(figsize=plt.figaspect(0.5))
ax = plt.axes(projection='3d')
ax.plot_surface(X, Y, Z, #rstride=1, cstride=1,
                cmap='magma', edgecolor='none')

ax.set_zlabel('Growth rate (hr^-1)',fontsize=15)
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.set_zticks([0,0.5,1])
ax.set_zticklabels([0,0.5,1],fontsize=13)

ax.set_title('$P_{z_{i}→z_{j}} = r_{m}^{||z_{i}-z_{j}||_{2}}$',fontsize=17)

fig.savefig('f30_surface_plot.pdf',bbox_inches='tight')

# ax.annotate('z',(0,0),fontsize=13,xycoords='axes points')

# ax.set_xlabel('Genotype space')

# results_manager.save_fig(fig,'f30_surface_plot.pdf')