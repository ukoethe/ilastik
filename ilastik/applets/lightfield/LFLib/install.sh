#!/bin/bash
echo "*************************************************"
echo "INSTALLING SYSTEM PACKAGES                       "
echo "*************************************************"
sudo apt-get install libqt4-dev cython libopenexr-dev python-sphinx python-numpy python-scipy python-matplotlib python-h5py libhdf5-serial-dev libfftw3-dev doxygen libboost-all-dev cmake libblas-dev liblapack-dev gfortran python-qt4 python-qt4-gl python-qt4-dev python-setuptools pyqt4-dev-tools gtk2-engines-pixbuf libpng12-dev libjpeg-dev libtiff4-dev

echo "*************************************************"
echo "INSTALLING VIGRA                                 "
echo "*************************************************"
# vigra installation
cd vigra
mkdir build
cd build
cmake ../
make
sudo make install
cd ..
cd ..


echo "*************************************************"
echo "INSTALLING PYTHON MODULES                        "
echo "*************************************************"
sudo easy_install qimage2ndarray OpenEXR greenlet psutils

#lazyflow installation
cd lazyflow
python setup.py build
sudo python setup.py install
cd ..

echo "*************************************************"
echo "PREREQUISITES INSTALLED, BUILDING Viewer"
echo "*************************************************"
sudo sh ./setup.sh


echo "*************************************************"
echo "DONE, created executable 'viewLF'       "
echo "*************************************************"

