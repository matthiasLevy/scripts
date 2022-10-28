folder=$1  #~/EMS_dev/EMS_framework
pattern=$2  # _YP90
replace=$3  # _SPP95
echo "Looking into $folder for files with pattern $pattern and replacing with $replace"
find $folder -name *$pattern* | while read name;
do
	new=$(echo $name | sed "s/$pattern/$replace/g")
	echo "$name -> $new"
	mv $name $new
done

