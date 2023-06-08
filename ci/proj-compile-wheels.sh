# INSTALL PROJ & DEPENDENCIES FOR WHEELS
# Test for macOS with [ -n "$IS_MACOS" ]
SQLITE_VERSION=3420000
LIBTIFF_VERSION=4.5.0
CURL_VERSION=8.1.2
NGHTTP2_VERSION=1.54.0


# ------------------------------------------
# From: https://github.com/multi-build/multibuild/
# ------------------------------------------
BUILD_PREFIX="${BUILD_PREFIX:-/usr/local}"
OPENSSL_ROOT=${OPENSSL_ROOT:-openssl-1.1.1l}
# Hash from https://www.openssl.org/source/openssl-1.1.1?.tar.gz.sha256
OPENSSL_HASH=${OPENSSL_HASH:-0b7a3e5e59c34827fe0c3a74b7ec8baef302b98fa80088d7f9153aa16fa76bd1}
OPENSSL_DOWNLOAD_URL=${OPENSSL_DOWNLOAD_URL:-https://www.openssl.org/source}

if [ $(uname) == "Darwin" ]; then
  IS_MACOS=1;
fi

if [ -z "$IS_MACOS" ]; then
    # Strip all binaries after compilation.
    STRIP_FLAGS=${STRIP_FLAGS:-"-Wl,-strip-all"}

    export CFLAGS="${CFLAGS:-$STRIP_FLAGS}"
    export CXXFLAGS="${CXXFLAGS:-$STRIP_FLAGS}"
    export FFLAGS="${FFLAGS:-$STRIP_FLAGS}"
fi

export CPPFLAGS_BACKUP="$CPPFLAGS"
export LIBRARY_PATH_BACKUP="$LIBRARY_PATH"
export PKG_CONFIG_PATH_BACKUP="$PKG_CONFIG_PATH"

function update_env_for_build_prefix {
  # Promote BUILD_PREFIX on search path to any newly built libs
  export CPPFLAGS="-I$BUILD_PREFIX/include $CPPFLAGS_BACKUP"
  export LIBRARY_PATH="$BUILD_PREFIX/lib:$LIBRARY_PATH_BACKUP"
  export PKG_CONFIG_PATH="$BUILD_PREFIX/lib/pkgconfig/:$PKG_CONFIG_PATH_BACKUP"
  # Add binary path for configure utils etc
  export PATH="$BUILD_PREFIX/bin:$PATH"
}

function rm_mkdir {
    # Remove directory if present, then make directory
    local path=$1
    if [ -z "$path" ]; then echo "Need not-empty path"; exit 1; fi
    if [ -d "$path" ]; then rm -rf $path; fi
    mkdir $path
}

function untar {
    local in_fname=$1
    if [ -z "$in_fname" ];then echo "in_fname not defined"; exit 1; fi
    local extension=${in_fname##*.}
    case $extension in
        tar) tar -xf $in_fname ;;
        gz|tgz) tar -zxf $in_fname ;;
        bz2) tar -jxf $in_fname ;;
        zip) unzip -qq $in_fname ;;
        xz) if [ -n "$IS_MACOS" ]; then
              tar -xf $in_fname
            else
              if [[ ! $(type -P "unxz") ]]; then
                echo xz must be installed to uncompress file; exit 1
              fi
              unxz -c $in_fname | tar -xf -
            fi ;;
        *) echo Did not recognize extension $extension; exit 1 ;;
    esac
}

function suppress {
    # Run a command, show output only if return code not 0.
    # Takes into account state of -e option.
    # Compare
    # https://unix.stackexchange.com/questions/256120/how-can-i-suppress-output-only-if-the-command-succeeds#256122
    # Set -e stuff agonized over in
    # https://unix.stackexchange.com/questions/296526/set-e-in-a-subshell
    local tmp=$(mktemp tmp.XXXXXXXXX) || return
    local errexit_set
    echo "Running $@"
    if [[ $- = *e* ]]; then errexit_set=true; fi
    set +e
    ( if [[ -n $errexit_set ]]; then set -e; fi; "$@"  > "$tmp" 2>&1 ) ; ret=$?
    [ "$ret" -eq 0 ] || cat "$tmp"
    rm -f "$tmp"
    if [[ -n $errexit_set ]]; then set -e; fi
    return "$ret"
}

function yum_install {
    # CentOS 5 yum doesn't fail in some cases, e.g. if package is not found
    # https://serverfault.com/questions/694942/yum-should-error-when-a-package-is-not-available
    yum install -y "$1" && rpm -q "$1"
}

function install_rsync {
    # install rsync via package manager
    if [ -n "$IS_MACOS" ]; then
        # macOS. The colon in the next line is the null command
        :
    elif [[ $MB_ML_VER == "_2_24" ]]; then
        # debian:9 based distro
        [[ $(type -P rsync) ]] || apt-get install -y rsync
    else
        # centos based distro
        [[ $(type -P rsync) ]] || yum_install rsync
    fi
}

function fetch_unpack {
    # Fetch input archive name from input URL
    # Parameters
    #    url - URL from which to fetch archive
    #    archive_fname (optional) archive name
    #
    # Echos unpacked directory and file names.
    #
    # If `archive_fname` not specified then use basename from `url`
    # If `archive_fname` already present at download location, use that instead.
    local url=$1
    if [ -z "$url" ];then echo "url not defined"; exit 1; fi
    local archive_fname=${2:-$(basename $url)}
    local arch_sdir="${ARCHIVE_SDIR:-archives}"
    if [ -z "$IS_MACOS" ]; then
        local extension=${archive_fname##*.}
        if [ "$extension" == "xz" ]; then
            ensure_xz
        fi
    fi
    # Make the archive directory in case it doesn't exist
    mkdir -p $arch_sdir
    local out_archive="${arch_sdir}/${archive_fname}"
    # If the archive is not already in the archives directory, get it.
    if [ ! -f "$out_archive" ]; then
        # Source it from multibuild archives if available.
        local our_archive="${MULTIBUILD_DIR}/archives/${archive_fname}"
        if [ -f "$our_archive" ]; then
            ln -s $our_archive $out_archive
        else
            # Otherwise download it.
            curl -L $url > $out_archive
        fi
    fi
    # Unpack archive, refreshing contents, echoing dir and file
    # names.
    rm_mkdir arch_tmp
    install_rsync
    (cd arch_tmp && \
        untar ../$out_archive && \
        ls -1d * &&
        rsync --delete -ah * ..)
}

function build_simple {
    # Example: build_simple libpng $LIBPNG_VERSION \
    #               https://download.sourceforge.net/libpng tar.gz \
    #               --additional --configure --arguments
    local name=$1
    local version=$2
    local url=$3
    local ext=${4:-tar.gz}
    local configure_args=${@:5}
    if [ -e "${name}-stamp" ]; then
        return
    fi
    local name_version="${name}-${version}"
    local archive=${name_version}.${ext}
    fetch_unpack $url/$archive
    (cd $name_version \
        && ./configure --prefix=$BUILD_PREFIX $configure_args \
        && make -j4 \
        && make install)
    touch "${name}-stamp"
}

function get_modern_cmake {
    # Install cmake >= 2.8
    local cmake=cmake
    if [ -n "$IS_MACOS" ]; then
        brew install cmake > /dev/null
    elif [[ $MB_ML_VER == "_2_24" ]]; then
        # debian:9 based distro
        apt-get install -y cmake
    else
        if [ "`yum search cmake | grep ^cmake28\.`" ]; then
            cmake=cmake28
        fi
        # centos based distro
        yum_install $cmake > /dev/null
    fi
    echo $cmake
}

function build_zlib {
    # Gives an old but safe version
    if [ -n "$IS_MACOS" ]; then return; fi  # OSX has zlib already
    if [ -e zlib-stamp ]; then return; fi
    if [[ $MB_ML_VER == "_2_24" ]]; then
        # debian:9 based distro
        apt-get install -y zlib1g-dev
    else
        #centos based distro
        yum_install zlib-devel
    fi
    touch zlib-stamp
}

function build_openssl {
    if [ -e openssl-stamp ]; then return; fi
    fetch_unpack ${OPENSSL_DOWNLOAD_URL}/${OPENSSL_ROOT}.tar.gz
    check_sha256sum $ARCHIVE_SDIR/${OPENSSL_ROOT}.tar.gz ${OPENSSL_HASH}
    (cd ${OPENSSL_ROOT} \
        && ./config no-ssl2 no-shared -fPIC --prefix=$BUILD_PREFIX \
        && make -j4 \
        && make install)
    touch openssl-stamp
}
# ------------------------------------------


function build_nghttp2 {
    if [ -e nghttp2-stamp ]; then return; fi
    fetch_unpack https://github.com/nghttp2/nghttp2/releases/download/v${NGHTTP2_VERSION}/nghttp2-${NGHTTP2_VERSION}.tar.gz
    (cd nghttp2-${NGHTTP2_VERSION}  \
        && ./configure --enable-lib-only --prefix=$BUILD_PREFIX \
        && make -j4 \
        && make install)
    touch nghttp2-stamp
}

function build_curl_ssl {
    if [ -e curl-stamp ]; then return; fi
    CFLAGS="$CFLAGS -g -O2"
    CXXFLAGS="$CXXFLAGS -g -O2"
    suppress build_nghttp2
    local flags="--prefix=$BUILD_PREFIX --with-nghttp2=$BUILD_PREFIX --with-zlib=$BUILD_PREFIX"
    if [ -n "$IS_MACOS" ]; then
        flags="$flags --with-darwinssl"
    else  # manylinux
        suppress build_openssl
        flags="$flags --with-ssl"
        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BUILD_PREFIX/lib
    fi
    fetch_unpack https://curl.se/download/curl-${CURL_VERSION}.tar.gz
    (cd curl-${CURL_VERSION} \
        && if [ -z "$IS_MACOS" ]; then \
        LIBS=-ldl ./configure $flags; else \
        ./configure $flags; fi\
        && make -j4 \
        && make install)
    touch curl-stamp
}


function build_libtiff {
    if [ -e libtiff-stamp ]; then return; fi
    build_simple tiff $LIBTIFF_VERSION https://download.osgeo.org/libtiff
    touch libtiff-stamp
}

function build_sqlite {
    if [ -z "$IS_MACOS" ]; then
        CFLAGS="$CFLAGS -DHAVE_PREAD64 -DHAVE_PWRITE64"
    fi
    if [ -e sqlite-stamp ]; then return; fi
    build_simple sqlite-autoconf $SQLITE_VERSION https://www.sqlite.org/2023
    touch sqlite-stamp
}

function build_proj {
    if [ -e proj-stamp ]; then return; fi
    get_modern_cmake
    fetch_unpack https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz
    suppress build_curl_ssl
    (cd proj-${PROJ_VERSION:0:5} \
        && cmake . \
        -DCMAKE_INSTALL_PREFIX=$PROJ_DIR \
        -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_IPO=ON \
        -DBUILD_APPS:BOOL=OFF \
        -DBUILD_TESTING:BOOL=OFF \
        -DCMAKE_PREFIX_PATH=$BUILD_PREFIX \
        -DCMAKE_INSTALL_LIBDIR=lib \
        && cmake --build . -j$(nproc) \
        && cmake --install .)
    touch proj-stamp
}

# Run installation process
update_env_for_build_prefix
suppress build_zlib
suppress build_sqlite
suppress build_libtiff
build_proj
