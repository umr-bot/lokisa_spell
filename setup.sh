#!/bin/bash

conda config --add channels conda-forge
conda create --prefix $(pwd)/conda_env python=3.7.8 python-levenshtein colorama tqdm nltk
conda activate $(pwd)/conda_env
pip install TextGrid
conda deactivate
