"""
This makes plots of the dimensions inside a grid.
"""
import os
import h5py
import corner
import numpy as np
import matplotlib.pyplot as plt
import argparse


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


def main(
    gridfile: str,
    infofile: str | None,
    quantities: list = [
        "FeHini",
        "MeHini",
        "alphaFe",
        "alphaMLT",
        #'dif',
        "eta",
        #'gcut',
        "massini",
        #'ove',
        "volume",
        "yini",
    ],
    dynamicquantities: list = ["numax", "dnuscal"],
):
    assert os.path.exists(gridfile)
    assert gridfile.endswith(".hdf5")
    gridid = gridfile.split('/')[-1].split(".hdf5")[-2]
    print(gridid)

    plotdir = f'./{gridid}_plots/'
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)

    data_dict = {}
    dyndata_dict = {}

    with h5py.File(gridfile, "r") as hdf:
        for quantity in quantities:
            data_path = f"header/{quantity}"
            if data_path in hdf:
                data_dict[quantity] = hdf[data_path][()]
            else:
                print(f"Path {data_path} not found in the HDF5 file")

        # Now get dnu and numax, which is not stored in the header
        for quantity in dynamicquantities:
            tracks = hdf["header/tracks"][()]
            if quantity == "numax":
                rescal = 3090
            else:
                rescal = 135.1
            ls = []
            meanls = []
            for track in tracks:
                track = track.decode("utf-8").split("/")[0]
                dynamic_data_path = f"grid/tracks/{track}/{quantity}"
                if dynamic_data_path in hdf:
                    l = hdf[dynamic_data_path][()] * rescal
                    if len(l) < 1:
                        print(f"This is empty {quantity} in {track}")
                        l = [
                            0,
                            0,
                        ]
                    ls.append(l[-1])
                    meanls.append(np.mean(l))
                else:
                    print(f"This path {dynamic_data_path} does not exist in grid")
                    raise SystemExit
            data_dict[quantity] = meanls
            dyndata_dict[quantity] = ls
            quantities.append(quantity)

    # Check if all quantities have the same length
    lengths = [len(data) for data in data_dict.values()]
    if len(set(lengths)) != 1:
        raise ValueError("Not all quantities have the same number of entries.")

    # Stack the data into a single numpy array
    data_matrix = np.vstack([data_dict[quantity] for quantity in quantities]).T

    # Create labels for the corner plot
    labels = quantities

    # Generate the corner plot
    fig = corner.corner(data_matrix, labels=labels)

    # Show the plot
    plt.savefig(os.path.join(plotdir, f"initialdimensions_{gridid}.png"))

    # Make smaller corner
    lengths = [len(data) for data in dyndata_dict.values()]
    if len(set(lengths)) != 1:
        raise ValueError("Not all quantities have the same number of entries.")

    data_matrix = np.vstack(
        [dyndata_dict[quantity] for quantity in dynamicquantities]
    ).T

    # Create labels for the corner plot
    labels = dynamicquantities

    # Generate the corner plot
    fig = corner.corner(data_matrix, labels=labels)

    # Show the plot
    plt.savefig(os.path.join(plotdir, f"temporaldimensions_{gridid}.png"))


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.gridfile, args.infofile)
