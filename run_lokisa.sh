#!/bin/bash

cd /home/ewaldvdw/lokisa_spell

conda activate $(pwd)/conda_env

python lokisa.py

conda deactivate
