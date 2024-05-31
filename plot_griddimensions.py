"""
This makes plots of the dimensions inside a grid.
"""
import os
import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse
import matplotlib.figure
import arviz as az

import basta.constants as bc
import basta.plot_corner as bcorner
import corner


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
        # "MeHini",
        "alphaFe",
        "alphaMLT",
        #'dif',
        "eta",
        #'gcut',
        "massini",
        #'ove',
        # "volume",
        "yini",
    ],
    dynamicquantities: list = ["numax", "dnuscal"],
    points: int = 8,
    zoom: int = 2,
):
    assert os.path.exists(gridfile)
    assert gridfile.endswith(".hdf5")
    gridid = gridfile.split("/")[-1].split(".hdf5")[-2]

    plotdir = f"./{gridid}_plots/"
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)

    data_dict = {}
    dyndata_dict = {i: {q: [] for q in dynamicquantities} for i in np.arange(points)}

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
            for track in tracks:
                track = track.decode("utf-8").split("/")[0]
                dynamic_data_path = f"grid/tracks/{track}/{quantity}"
                if dynamic_data_path in hdf:
                    l = hdf[dynamic_data_path][()] * rescal
                    if len(l) < 1:
                        print(f"This is empty {quantity} in {track}")
                        l = np.ones(points) * 0.1
                    # TODO: get a normalised n instead.
                    for i, n in enumerate(
                        np.linspace(0, len(l) - 1, points, dtype=int)
                    ):
                        dyndata_dict[i][quantity].append(l[n])
                else:
                    print(f"This path {dynamic_data_path} does not exist in grid")
                    raise SystemExit

    def _make_corner(
        data_dict: dict,
        quantities: list,
        figname: str | None = None,
        plotdir: str | None = None,
    ):
        lengths = [len(data) for data in data_dict.values()]
        if len(set(lengths)) != 1:
            raise ValueError("Not all quantities have the same number of entries.")

        a = bc.parameters.get_keys(quantities)
        labels = a[1]
        colors = a[3]

        data_matrix = np.vstack([data_dict[quantity] for quantity in quantities]).T
        fig = bcorner.corner(data_matrix, labels=labels, truth_color=colors)
        if figname is not None:
            plt.savefig(os.path.join(plotdir, figname))

    def _make_overlaid_corner(
        data_dict: dict,
        quantities: list,
        points: int,
        zoom: int = 1,
        figname: str | None = None,
        plotdir: str | None = None,
        cmapname: str = "Blues",
    ):
        if zoom != 1:
            sfn = figname.split(".")
            figname = f"{sfn[0]}_{zoom}.{sfn[-1]}"
            print(figname)
        cmap = mpl.colormaps[cmapname].resampled(points)
        colors = [cmap(n) for n in np.arange(points)]

        max_len = [
            max(len(data_dict[s][q]) for s in data_dict.keys())
            for q in data_dict[0].keys()
        ]
        assert len(max_len) == len(quantities)

        plot_range = []
        for dim in quantities:
            plot_range.append(
                [
                    min([min(data_dict[n][dim]) for n in range(points)]),
                    max([max(data_dict[n][dim]) / zoom for n in range(points)]),
                ]
            )
        # TODO: get ordering!
        plot_range = list(reversed(plot_range))

        fig = None
        labels = bc.parameters.get_keys(quantities)[1]
        for n in np.arange(points):
            fig = corner.corner(
                data=az.from_dict(data_dict[n]),
                labels=labels,
                color=colors[n],
                range=plot_range,
                plot_datapoints=True,
                plot_density=False,
                plot_contours=False,
                hist_bin_factor=10,
                smooth1d=1,
                levels=(1 - np.exp(-0.5), 1 - np.exp(-2), 1 - np.exp(-9 / 2.0)),
                fig=fig,
            )
        if figname is not None:
            plt.savefig(os.path.join(plotdir, figname))

    _make_corner(
        data_dict=data_dict,
        quantities=quantities,
        figname=f"initialdimensions_{gridid}.png",
        plotdir=plotdir,
    )

    _make_overlaid_corner(
        data_dict=dyndata_dict,
        quantities=dynamicquantities,
        points=points,
        figname=f"temporaldimensions_{gridid}.png",
        plotdir=plotdir,
    )

    _make_overlaid_corner(
        data_dict=dyndata_dict,
        quantities=dynamicquantities,
        points=points,
        figname=f"temporaldimensions_{gridid}.png",
        plotdir=plotdir,
        zoom=zoom,
    )


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.gridfile, args.infofile)
