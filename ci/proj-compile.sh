#!/bin/bash
pushd .
echo "Building PROJ $1 version from source..."
if [[ $1 == "git" ]]; then
  git clone https://github.com/OSGeo/PROJ.git proj-git
else
  curl https://download.osgeo.org/proj/proj-$1.tar.gz > "proj-${1:0:5}.tar.gz"
  tar zxf "proj-${1:0:5}.tar.gz"
fi
cd "proj-${1:0:5}"
# build using autotools
sh autogen.sh
./configure --prefix=$PROJ_DIR
make
make install
# build using cmake
#cmake . -DCMAKE_INSTALL_PREFIX=$PROJ_DIR
#cmake --build .
#make install
popd
