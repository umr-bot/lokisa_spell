# Lokisa spell -- A simple tool to help standardise the orthography of transcribed text data sets

This is still only a working demo and will change regularly in the coming day or weeks. 


## Requirements

The program has been developed and tested with Python version 3.7.8.

Python packages that are required to be installed are:
* python-levenshtein
* colorama
* tqdm
* TextGrid


## Conda and Linux

If you use `conda` to manage your Python environments in Linux, you can just run the `setup.sh` bash
script to perform the setup of the required Python environment and packages. This setup script creates
a python environment in the Lokisa project's root directory. Activate this environment by executing:

    conda activate <path_to_the_conda_environment>

If the environment loaded successfully, you can now start the program (see [usage](#usage)) .


## Windows and Mac

The setup of the Python environment on Windown and Mac has not been tested yet. This will follow soon.


## Usage

Once the Python environment and packages have been set up, you can start the Lokisa Spell program with:

    python lokisa.py

