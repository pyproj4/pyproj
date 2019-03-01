#!/bin/bash
# Run this command to build the wheels:
# docker run --rm -v `pwd`:/io quay.io/pypa/manylinux1_x86_64 /io/build-wheels.sh 6.0.0
set -e -x

# install updated auditwheel
/opt/python/cp36-cp36m/bin/pip install git+https://github.com/daa/auditwheel.git@c4b6339 

# Install PROJ.4
yum install -y sqlite sqlite-devel zlib-devel
export PROJ_DIR=/io/pyproj/proj_dir
/io/ci/travis/proj-dl-and-compile $1

# Compile wheels
export PROJ_WHEEL=true
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install -r /io/requirements-dev.txt
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    "${PYBIN}/pip" install pyproj --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/python" -c "import pyproj; pyproj.Proj(init='epsg:4269')" )
done
