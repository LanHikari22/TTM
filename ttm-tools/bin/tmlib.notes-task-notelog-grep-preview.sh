#!/bin/bash


#echo 1: $1
#echo 2: $2

# We remove the quote which to fzf indicdates exact-match
filtered_query=$(echo "$2" | sed "s/'//g")
# echo filtered_query: "$filtered_query"

echo "$1" | grep --color=always "$filtered_query\|"
