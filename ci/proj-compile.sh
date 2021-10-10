#!/bin/bash
pushd .
echo "Building PROJ ($1) from source..."
BUILD_PROJ_DIR=proj-${1:0:5}
# Download PROJ
if [[ $1 == "git" ]]; then
  git clone https://github.com/OSGeo/PROJ.git ${BUILD_PROJ_DIR}
else
  curl https://download.osgeo.org/proj/proj-$1.tar.gz > ${BUILD_PROJ_DIR}.tar.gz
  tar zxf ${BUILD_PROJ_DIR}.tar.gz
  rm ${BUILD_PROJ_DIR}.tar.gz
fi
cd ${BUILD_PROJ_DIR}
mkdir build
cd build
# build using cmake
cmake .. \
    -DCMAKE_INSTALL_PREFIX=$PROJ_DIR \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_IPO=ON \
    -DBUILD_CCT:BOOL=OFF \
    -DBUILD_CS2CS:BOOL=OFF \
    -DBUILD_GEOD:BOOL=OFF \
    -DBUILD_GIE:BOOL=OFF \
    -DBUILD_GMOCK:BOOL=OFF \
    -DBUILD_PROJINFO:BOOL=OFF \
    -DBUILD_TESTING:BOOL=OFF
cmake --build . -j$(nproc)
cmake --install .
# cleanup
cd ../..
rm -rf ${BUILD_PROJ_DIR}
popd
