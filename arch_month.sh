#!/bin/bash
set -e


ls -1d  */Data/Forecast/Steadysun/*/*/|while read item;
do
    dir=$(dirname $item)
    base=$(basename $item)

    # Excluding files for last 10 days
    for i in $(seq 0 9); do
        date_str=$(date +"%Y-%m-%d" -d $date "-$i days")
        # echo $date_str
        if [ "$base" = $date_str ]; then
            echo "Skipping $item"
            continue
	fi
    done

    # echo "Compressing $dir/$base.gz $item"
    # tar czf "$dir/$base.tgz" $item && echo "Removing $item"
done
