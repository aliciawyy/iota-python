#! /bin/bash

cd ~
git clone https://github.com/facebook/rocksdb.git
cd rocksdb
mkdir build && cd build
cmake ..
make
export CPLUS_INCLUDE_PATH=${CPLUS_INCLUDE_PATH}:`pwd`/../include
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:`pwd`
export LIBRARY_PATH=${LIBRARY_PATH}:`pwd`