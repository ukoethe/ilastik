#$ python setup.py build_ext --inplace

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [
                    Extension("libfilter", ["src/libfilter.pyx"],language='c++'),
                    Extension("libui", ["src/libui.pyx"],language='c++'),
                    Extension("libimproc", ["src/libimproc.pyx"],language='c++'),
                    Extension("libinterpolation", ["src/libinterpolation.pyx"],language='c++')
                  ]
)
