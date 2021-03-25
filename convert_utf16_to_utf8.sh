#!/bin/bash
# A script to change all TextGrid utf-16 files into utf-8
# The cd workingdir/textgrids/ line can be altered as to where 
# the user prefers the changes to recursively occur from
cd workingdir/textgrids/
for a in $(find . -name "*.TextGrid");
do
        filename=$(basename $a);
        echo $filename
        iconv -f utf-16 -t utf-8 "$a" -o "$a.utf8";
done

for converted_file in $(find . -name "*.utf8");
do
        echo "$converted_file"
	mv -- "$converted_file" "${converted_file%.utf8}"
done

