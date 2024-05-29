"""
This updates a grid post the non-trivial update of 0.25 (removal of matN).
"""
import os
import h5py
import numpy as np
import argparse
import json
import shutil
import bottleneck as bn
from basta import sobol_numbers


parser = argparse.ArgumentParser()
parser.add_argument(
    "-g",
    "--gridfile",
    help="Path and name to the grid",
)
parser.add_argument(
    "-i",
    "--infofile",
    help="Path and name to the info file of the grid",
)


def main(gridfile: str, infofile: str | None):
    assert os.path.exists(gridfile)
    newgridfile = make_copy(gridfile)
    grid = h5py.File(newgridfile, "r+")
    print(
        f"Updating grid {gridfile} of version {str(np.array(grid['header/version']))}"
    )

    # Fix header
    if "pars_sampled" not in list(grid["header"]):
        assert infofile is not None
        assert os.path.exists(infofile)
        var, sam, const = make_pars(grid, infofile)
        grid["header/pars_constant"] = const
        grid["header/pars_sampled"] = sam
        grid["header/pars_variable"] = var

    if "dif" not in list(grid["header"]):
        assert infofile is not None
        assert os.path.exists(infofile)
        v = 1 if "dif" in var else 0
        difdata = np.ones(len(grid["header/yini"])) * v
        grid[f"header/dif"] = difdata

    basepath = "grid/"
    if "volume" in list(grid["header"]):
        del grid["header/volume"]
    IntStatus = np.ones(len(grid["header/yini"]))
    names = [name for name in list(grid["header/tracks"])]
    assert len(IntStatus) == len(names)

    # More or less from basta/interpolation_helpers.py
    index = np.ones(len(grid["header/yini"]))
    bpars = grid["header/pars_sampled"]
    print(list(bpars))

    # Collect basis parameters
    base = np.zeros((len(index), len(bpars)))
    gid = 0
    lid = 0
    ntracks = len(index)
    npoints = np.zeros(ntracks, dtype=int)
    for gname, group in grid[basepath].items():
        iter = zip(IntStatus[gid : gid + len(group)], group.items())
        for i, (ist, (_, libitem)) in enumerate(iter):
            if ist != 1:
                continue
            for j, par in enumerate(bpars):
                base[lid, j] = libitem[par][0]
            lid += 1
        gid += len(group)

    for i, par in enumerate(bpars):
        mm = [min(base[:, i]), max(base[:, i])]
        base[:, i] -= mm[0]
        base[:, i] /= mm[1] - mm[0]

    # Generate oversampled grid
    sobnums = base
    ntracks = len(base)
    ndim = len(bpars)

    iseed = 2
    osfactor = 100
    osntracks = osfactor * ntracks
    osbase = np.zeros((osntracks, ndim))
    for i in range(osntracks):
        iseed, osbase[i, :] = sobol_numbers.i8_sobol(ndim, iseed)

    # For every track in the grid, gather all the points from the
    # oversampled grid which are closest to the track at hand
    npoints = np.zeros(ntracks, dtype=int)
    for i in range(osntracks):
        diff = osbase[i, :] - sobnums
        distance = bn.nansum(diff**2, axis=-1)
        nclosest = bn.nanargmin(distance)
        npoints[nclosest] += 1

    # Transform to volume weight per track
    weights = npoints / bn.nansum(npoints)

    # Write the weights
    for i, name in enumerate(names):
        weight_path = f"{basepath}tracks/{name.decode().split('/')[0]}/volume_weight"
        try:
            grid[weight_path] = weights[i]
        except:
            del grid[weight_path]
            grid[weight_path] = weights[i]

    # Write the active weights as only volume
    del grid["header/active_weights"]
    grid["header/active_weights"] = ["volume"]
    grid["header/volume"] = weights

    rename = {
        "alphaFeini": "alphaFe",
        "alphaMLTini": "alphaMLT",
        "etaini": "eta",
        "ovini": "ove",
    }
    for key in rename.keys():
        if key in list(grid["header"]):
            grid[f"header/{rename[key]}"] = grid[f"header/{key}"]
            del grid[f"header/{key}"]

    for h in list(grid["header"]):
        if h.startswith("w"):
            print(h)
            del grid[f"header/{h}"]

    print(list(grid["header"]))
    # TODO: grid is missing 'MeHini' and 'gcut' in header.
    # TODO: maybe the version number should be bumped (but it should be
    # noted that it was bumped using this script.


def make_copy(gridname: str) -> str:
    newgridname = "".join(gridname.split(".hdf5")[:-1]) + "_updated.hdf5"
    print(f"Makes {newgridname}")
    shutil.copy2(gridname, newgridname)
    assert os.path.exists(newgridname)
    return newgridname


def make_pars(grid, infofile: str):
    # Make pars_{something} in header
    a = json.load(open(infofile))

    # Make the interp lists
    variablenames = {
        "eta": "eta",
        "FeHini": "FeHini",
        "fehi": "FeHini",
        "mass": "massini",
        "massini": "massini",
        "alphaFeini": "alphaFe",
        "alphaFe": "alphaFe",
        "diff": "dif",
        "gcut": "gcut",
        "ml": "alphaMLT",
        "alphaMLTini": "alphaMLT",
        "ov": "ove",
        "ovini": "ove",
        "yi": "yini",
        "yini": "yini",
    }

    # This one contains dimensions that are not varied
    varyflags = [str(key)[5:] for key in a.keys() if "vary_" in key]
    raw_pars_constant = [vf for vf in varyflags if a["vary_" + vf] == False]
    pars_constant = []
    for raw_par in raw_pars_constant:
        assert raw_par in variablenames.keys(), raw_par
        pars_constant.append(variablenames[raw_par])

    # These one vary but are not sampled across (dependent variables?)
    raw_pars_sampled = [vf for vf in varyflags if a["vary_" + vf] == True]
    pars_sampled = []
    for raw_par in raw_pars_sampled:
        assert raw_par in variablenames.keys()
        pars_sampled.append(variablenames[raw_par])

    # This one are the ones that are sampled (sobol)
    pars_variable = []
    if "FeHini" in pars_sampled:
        pars_variable.append("MeHini")
    if "yini" not in pars_sampled:
        pars_variable.append("yini")

    assert not (set(pars_variable) & set(pars_constant))
    assert not (set(pars_variable) & set(pars_sampled))

    return pars_variable, pars_sampled, pars_constant


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.gridfile, args.infofile)
