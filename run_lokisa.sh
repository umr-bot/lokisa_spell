#!/bin/bash

. /home/lokisa/miniconda3/etc/profile.d/conda.sh

cd /home/lokisa/lokisa_spell

conda activate $(pwd)/conda_env

python lokisa.py

conda deactivate
