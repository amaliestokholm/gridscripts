import h5py
import corner
import numpy as np
import matplotlib.pyplot as plt

# Specify the path to your HDF5 file
file_path = 'Garstec_AS09_chiara.hdf5'

# List of quantities to include in the corner plot
quantities = [
    'FeHini', 'MeHini', 
    'alphaFe', 'alphaMLT',
    #'dif',
    'eta',
    #'gcut',
    'massini',
    #'ove',
    #'tracks',
    'volume',
    'yini'
]
dynquantities = ['numax', 'dnuscal']

# Dictionary to hold the data
data_dict = {}
dyndata_dict = {}

# Open the HDF5 file and read the data
with h5py.File(file_path, 'r') as hdf:
    for quantity in quantities:
        data_path = f'header/{quantity}'
        if data_path in hdf:
            data_dict[quantity] = hdf[data_path][()]
        else:
            print(f'Path {data_path} not found in the HDF5 file')
    # Now get dnu and numax, which is not stored in the header
    for quantity in dynquantities:
        tracks = hdf['header/tracks'][()]
        if quantity == 'numax':
            rescal = 3090
        else:
            rescal = 135.1
        ls = []
        meanls = []
        for track in tracks:
            track = track.decode("utf-8").split('/')[0]
            dynamic_data_path = f"grid/tracks/{track}/{quantity}"
            if dynamic_data_path in hdf:
                l = hdf[dynamic_data_path][()] * rescal
                if len(l) < 1:
                    print(quantity, track)
                    l = [0, 0,]
                ls.append(l[-1])
                meanls.append(np.mean(l))
            else:
                print(dynamic_data_path)
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
plt.savefig('check_finalgrid.png')

# Make smaller corner
lengths = [len(data) for data in dyndata_dict.values()]
if len(set(lengths)) != 1:
    raise ValueError("Not all quantities have the same number of entries.")

data_matrix = np.vstack([dyndata_dict[quantity] for quantity in dynquantities]).T

# Create labels for the corner plot
labels = dynquantities

# Generate the corner plot
fig = corner.corner(data_matrix, labels=labels)

# Show the plot
plt.savefig('check_finalgrid_dynamic_final.png')
