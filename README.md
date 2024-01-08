# pyForeFire

pyForeFire is a Python library for dealing with C++ library ForeFire.
It provide numerous ForeFire bindings, written with pybind11 python library.

## Building pyForeFire

### Prerequisite

- NetCDF and NetCDF-Cxx libraries installed (can be installed with homebrew on Mac) [`https://www.unidata.ucar.edu/software/netcdf/`]
- ForeFire C++ library and Headers [`https://github.com/forefireAPI/firefront`]

```bash
cmake . -DFOREFIRE_LIB=path/to/libforefireL.dylib -DFOREFIRE_SRC_DIR=path/to/firefront/src -DNETCDF_INCLUDE_DIR=path/to/netcdf/include -DNETCDFCXX_INCLUDE_DIR=path/to/netcdf-cxx/include/

make
```

## Usage

```python
import pyforefire as forefire

ff = forefire.ForeFire()

sizeX = 300
sizeY = 200
myCmd = "FireDomain[sw=(0.,0.,0.);ne=(%f,%f,0.);t=0.]" % (sizeX, sizeY)
ff.execute(myCmd)
...
```