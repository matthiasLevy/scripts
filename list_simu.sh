#!/bin/bash
echo $(date)
cd $1
for f in * ; do
    # echo $f
    # ls -1 $f/dump/* -rs | head -1 | grep -v -e "-12-31_23" ;
    ls -rt $f/dump/*2350.csv | tail -n 1 | sed 's/\/dump\//\t\t/'
done;
