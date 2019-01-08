#!/usr/bin/env bash
export PATH=/HWNAS12/RAD/luyang/SOFTWARE/miniconda3/bin:$PATH

basepath=$(cd `dirname $0`; pwd)
python3 /HWNAS12/RAD/luyang/PIPELINE/tigmint/bin/main.py $basepath
