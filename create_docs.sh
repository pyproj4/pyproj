# svn propset svn:mime-type text/html docs/*html
epydoc -v --exclude=_geod --exclude=datadir --exclude=_proj --no-frames --no-private --introspect-only -o docs pyproj
