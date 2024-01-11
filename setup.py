import os
import sys
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext


NETCDF_DIR = os.environ.get('NETCDF_DIR')
NETCDF_CXX_DIR = os.environ.get('NETCDF_CXX_DIR')
FOREFIRE_DIR = os.environ.get('FOREFIRE_DIR')
FOREFIRE_LIB = os.environ.get('FOREFIRE_LIB', 'forefireL')

if not NETCDF_DIR or not NETCDF_CXX_DIR or not FOREFIRE_DIR:
    print('NETCDF_DIR, NETCDF_CXX_DIR and FOREFIRE_DIR env variables must all be set.')
    sys.exit(1)

libraries = [FOREFIRE_LIB]
library_dirs = [FOREFIRE_DIR + '/lib']

ext_modules = [
    Pybind11Extension(
        "pyforefire",
        ["src/pylibforefire/pylibforefire.cpp"],
        include_dirs=[
            FOREFIRE_DIR + '/src',
            FOREFIRE_DIR + '/src/include',
            NETCDF_DIR + '/include',
            NETCDF_CXX_DIR + '/include'
        ],
        libraries=libraries,
        library_dirs=library_dirs,
        runtime_library_dirs=library_dirs,
        extra_objects=[FOREFIRE_DIR + '/lib/lib' + FOREFIRE_LIB + '.dylib']
    ),
]

setup(
    name="pyforefire",
    version="0.1",
    requires=['pybind11', 'setuptools', 'wheel'],
    author="Filippi Jean-Baptiste",
    author_email="filippi_j@univ-corse.fr",
    description="Python version of ForeFire library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    package_dir={'': FOREFIRE_DIR + '/lib'},
    package_data={'': ['lib' + FOREFIRE_LIB + '.dylib']},
    include_package_data=True,
    zip_safe=False,
)