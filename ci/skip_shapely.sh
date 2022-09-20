#!/bin/bash
pyver=$(python3 -c "import sys; print(sys.version)" | awk -F \. {'print $1$2'})
if [[ "${pyver}" != "311" ]] ; then
	python -m pip install shapely~=1.8.4 || echo "Shapely install failed"
fi
