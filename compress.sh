#!/bin/bash

set -e

find *_production/Data/Forecast/Steadysun/*/* -type d -mtime +10|grep -v "cs17"|while read item;
do
	dir=$(dirname $item)
	base=$(basename $item)

	echo "Compressing $dir/$base.tgz $item"
	tar czf "$dir/$base.tgz" $item && echo "Removing $item" && rm -rf "$item"
done
