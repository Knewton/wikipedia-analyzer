# example: get_tuples.sh 3 7 10 math-topics.download.edit.dat math-topics.tuples.dat math-topics.tuples.srt
# create all words tuples from 3 to 7 words
# sort and count the tuples
# eliminate all tuples that appear less than 10 times
get_tuples.py $1 $2 $4 | sort | awk -f count.awk -v MIN=$3 > $5
sort -g $5 > $6

