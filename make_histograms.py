import os
import h5py
import numpy as np
import matplotlib.pyplot as plt


gridname = "Garstec_AS09_chiara.hdf5"
grid = h5py.File(gridname, "r")

basepath = "grid/tracks"

dage, nmod, tage, dnu = [], [], [], []
for name, libitem in grid[basepath].items():
    #ind = np.where(libitem["xcen"][:] > 1e-5)[0][-1]
    #if ind < 2:
    #    continue
    age = libitem["age"][:ind]
    dage.append(np.mean(np.diff(age)))
    nmod.append(ind)
    tage.append(age[-1] - age[0])
    dnu.append(libitem["dnufit"][ind])

datas = [dage, nmod, tage, [t/i for t,i in zip(tage,nmod)], dnu]
labs  = [r"Mean $\Delta t$ (Myr)", r"Nmod(MS)", 
         r"$\Delta T$ (Myr)", r"$\Delta T/\mathrm{Nmod(MS)}$ (Myr)",
         r"$\Delta\nu_{\mathrm{fit}}$"]

fig, ax = plt.subplots(5,1, figsize=(6,10))
for i, (dat, lab) in enumerate(zip(datas, labs)):
    c, b = np.histogram(dat, bins="scott")
    w = b[1] - b[0]
    b = b[:-1] + w/2
    ax[i].bar(b, c, width=w*0.98)
    ax[i].set_xlabel(lab)

fig.tight_layout()
fig.savefig("histograms.pdf")
