#!/bin/bash

set -e

ls -1d  */Data/Forecast/Steadysun/*/*|while read item;
do
	dir=$(dirname $item)
	base=$(basename $item)
	echo "Compressing $dir/$base.gz $item"
#	tar cvxf "$dir/$base.tgz" $item
done
