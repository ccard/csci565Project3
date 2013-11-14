#! /bin/bash
v="thats what she said"
while read x; do
	if [[ "$x" != $v* && ${#x} -ne 0 ]]; then 
		echo "thats what she said "$x
	fi
done