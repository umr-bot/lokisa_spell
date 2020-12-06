#!/bin/bash

. /home/lokisa/miniconda3/etc/profile.d/conda.sh

cd /home/lokisa/lokisa_spell

conda activate $(pwd)/conda_env

python lokisa.py --mandatory_wordlist_fn conf/bam_mandatory_wordlist.txt

conda deactivate
