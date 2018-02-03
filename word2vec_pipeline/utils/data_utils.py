"""
Utility file to assist in loading data saved as part of the pipeline, 
including .csv files, h5 files, amd gensim w2v models. There are also 
functions to extract specific data from these files.
"""

import h5py
import os
import pandas as pd
import numpy as np
import joblib

import simple_config
from os_utils import grab_files

def load_h5_file(f_h5, *args):
    '''
    Generically loads a h5 files top level data structures (assumes
    no nesting). If *args is specified, only the *args subset will be loaded.

    Args:
        f_h5: an h5 file
        *args: additional args

    Returns:
        data: data stored in h5 file
    '''
    data = {}

    with h5py.File(f_h5, 'r') as h5:
        if not args:
            args = h5.keys()

        for key in args:
            if key not in h5:
                raise ValueError("{} not found in {}".format(key, f_h5))

        for key in args:
            data[key] = h5[key][:]

    return data


def touch_h5(f_db):
    '''
    Create the h5 file if it doesn't exist

    Args:
        f_db: string, filename of the h5 file

    Returns
        h5: an h5 file
    '''
    
    if not os.path.exists(f_db):
        h5 = h5py.File(f_db, 'w')
    else:
        h5 = h5py.File(f_db, 'r+')
    return h5


def get_h5save_object(f_db, method):
    # Returns a usable h5 object to store data
    h5 = touch_h5(f_db)
    g = h5.require_group(method)
    return g


def save_h5(h5, col, data, compression="gzip"):
    # Saves (or overwrites) a column in an h5 object
    if col in h5:
        del h5[col]
    return h5.create_dataset(col, data=data, compression=compression)


def load_dispersion_data():
    '''
    Load the dispersion data of each cluster.

    Returns:
         Dispersion data found in file determined by the config file.
    '''
    print("Loading dispersion data")

    config_post = simple_config().load["postprocessing"]

    f_h5 = os.path.join(
        config_post["output_data_directory"],
        "cluster_dispersion.h5")

    return load_h5_file(f_h5)


def simple_CSV_read(f, cols):
    '''
    Open a .csv file as a pandas dataframe.

    Args:
        f(str): Input ilename
        cols (list): Columns to be read in

    Returns:
        Pandas dataframe containing data from file
    '''
    try:
        dfx = pd.read_csv(f, usecols=cols)
    except ValueError:
        csv_cols = pd.read_csv(f, nrows=0).columns
        msg = "Columns requested {}, do not match columns in input csv {}"
        raise ValueError(msg.format(cols, csv_cols))
    return dfx


def load_ORG_data(extra_columns=None):
    '''
    DOCUMENTATION_UNKNOWN
    '''
    print("Loading import data")

    cols = ["_ref", ]

    if extra_columns is not None:
        cols += extra_columns

    config = simple_config.load()
    config_import = config["import_data"]

    CORES = -1 if config["_PARALLEL"] else 1

    # Load the input columns
    F_CSV = grab_files("*.csv", config_import["output_data_directory"])

    with joblib.Parallel(CORES) as MP:
        func = joblib.delayed(simple_CSV_read)
        data = MP(func(x, cols) for x in F_CSV)

    # Require the _refs to be in order
    df = pd.concat(data).sort_values('_ref').set_index('_ref')

    # Use _ref as an index, but keep it as a row
    df['_ref'] = df.index

    return df


def load_metacluster_data(*args):
    '''
    Load information on metaclusters from where they're saved in the pipeline

    Args:
        *args: DOCUMENTATION_UNKNOWN

    Returns:
        load_h5_file(f_h5, *args): the data on each cluster found in the 
        h5 file
    '''

    config_metacluster = simple_config.load()["metacluster"]

    f_h5 = os.path.join(
        config_metacluster["output_data_directory"],
        config_metacluster["f_centroids"])

    return load_h5_file(f_h5, *args)


def get_score_methods():
    '''
    Determines which scoring methods to return for each document, 
    based on what's set in config file

    Returns:
         h5.keys(): DOCUMENTATION_UNKNOWN
    '''
    config_score = simple_config.load()["score"]

    f_h5 = os.path.join(
        config_score["output_data_directory"],
        config_score["f_db"],
    )

    with h5py.File(f_h5, 'r') as h5:
        return h5.keys()


def load_document_vectors(score_method, use_reduced=False):
    '''
    Load the word2vec document vectors for each document from the h5 file 
    saved in pipeline

    Args:
        score_method: string, score method to load
        use_reduced: boolean, flag to determine whether to use reduced 
        dimension vectors, or the orgiginal vectors

    Return:
        {"docv": X, "_refs": _refs}: dictionary, contains a list of document 
        vectors and corresponding references
    '''

    config_score = simple_config.load()["score"]

    f_h5 = os.path.join(
        config_score["output_data_directory"],
        config_score["f_db"],
    )

    with h5py.File(f_h5, 'r') as h5:

        assert(score_method in h5)
        g = h5[score_method]

        _refs = np.hstack([g[k]["_ref"][:] for k in g.keys()])

        vector_key = "VX" if use_reduced else "V"
        X = np.vstack([g[k][vector_key][:] for k in g.keys()])

        assert(X.shape[0] == _refs.size)

        # Sort to the proper order
        sort_idx = np.argsort(_refs)
        _refs = _refs[sort_idx]
        X = np.vstack(X)[sort_idx]

    return {
        "docv": X,
        "_refs": _refs
    }


def load_w2vec(config=None):
    '''
    Loads gensim word2vec model saved in pipeline.

    Args:
        config: config file to get parameters from

    Returns:
        W2V.Word2Vec.load(f_w2v): gensim word2vec model
    '''
    import gensim.models.word2vec as W2V

    if config is None:
        config = simple_config.load()

    config_embed = config["embed"]

    f_w2v = os.path.join(
        config_embed["output_data_directory"],
        config_embed["w2v_embedding"]["f_db"],
    )

    return W2V.Word2Vec.load(f_w2v)
