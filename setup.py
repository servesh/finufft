# This defines the python module installation.
# Only for double-prec, multi-threaded for now.

# Barnett 3/1/18. Updates by Yu-Hsuan Shih, June 2018.
# win32 mingw patch by Vineet Bansal, Feb 2019.

# Max OSX users: please edit as per below comments, and docs/install.rst

__version__ = '1.1.2'

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools
import os

finufft_dir = os.environ.get('FINUFFT_DIR')
mkl_dir = os.environ.get('MKLROOT')

# Note: This will not work if run through pip install since setup.py is copied
# to a different location.
if finufft_dir == None or finufft_dir == '':
    current_path = os.path.abspath(__file__)
    finufft_dir = os.path.dirname(os.path.dirname(current_path))

# Set include and library paths relative to FINUFFT root directory.
inc_dir = os.path.join(finufft_dir, 'include')
lib_dir = os.path.join(finufft_dir, 'lib')

# We specifically link to the dynamic library here through its absolute path
# (that is not through -lfinufft) to ensure that the absolute path of the
# library is encoded in the DT_NEEDED tag. This way, we won't need to have
# libfinufft.so in the LD_LIBRARY_PATH at runtime. The risk with this is that
# if the libfinufft.so is deleted or moved, the Python module will break
# unless LD_LIBRARY_PATH is updated
finufft_dlib = ('finufft')

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

# choose compile flags for finufftpy.cpp (links to finufft lib)...
if sys.platform == "win32":
    libraries = ["lib-static/finufft","fftw3"]
    extra_compile_args=['-fopenmp']
    extra_link_args=[]

elif sys.platform == "linux" or sys.platform == "linux2":
    # changed from fftw3_threads, since a bit faster, 9/24/18:
    #libraries = ["lib-static/finufft","fftw3","fftw3_omp","gomp"]
    #extra_compile_args=['-fopenmp']
    #extra_link_args=[]
    #libraries = ["lib-static/finufft"]
    libraries = [finufft_dlib]
    library_dirs = [lib_dir]
    include_dirs = [inc_dir]
    extra_compile_args=["-Wunknown-pragmas", "-Wno-implicit-const-int-float-conversion", "-DMKL_ILP64", "-qmkl", "-I"+mkl_dir+"/include/fftw", "-I"+mkl_dir+"/include/fftw/offload", "-O2", "-g", "-fiopenmp", "-fopenmp-targets=spir64", "-fsycl", "-D__GPU_TDV_OFFLOAD__", "-Iinclude", "-std=c++14", "-fPIC"]
    extra_link_args=["-pthread", "-shared", "-B", "-Wunknown-pragmas", "-Wno-implicit-const-int-float-conversion", "-DMKL_ILP64", "-qmkl", "-I"+mkl_dir+"/include/fftw", "-I"+mkl_dir+"/include/fftw/offload", "-O2", "-g", "-fiopenmp", "-fopenmp-targets=spir64", "-fsycl", "-D__GPU_TDV_OFFLOAD__", "-Iinclude", "-std=c++14", "-fPIC", "-L"+lib_dir, "-Wl,-rpath="+lib_dir ]

elif sys.platform == "darwin":
    # Mac OSX
    libraries = ["lib-static/finufft","fftw3","fftw3_threads","gomp"]
    extra_compile_args=['-fopenmp']
    if os.environ["CXX"] == "g++":
        # clang
        extra_link_args=['-fPIC']
    else:
        # GCC-8
        extra_link_args=['-fPIC']
        #extra_link_args=['-static -fPIC']

ext_modules = [Extension(
        'finufftpy_cpp',
        ['finufftpy/finufftpy.cpp'],
        include_dirs=[
            # Path to pybind11 headers
            get_pybind_include(),
            get_pybind_include(user=True),
            'src',
            inc_dir
        ],
        libraries=libraries,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        language='c++'
    ) ]

# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True

# Note C++11 is needed by pybind11, not by the project:
def cpp_flag(compiler):
    """Return the -std=c++[11/14] compiler flag.

    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
        'mingw32': ['-D_hypot=hypot']
    }

    # Mac OSX w/ GCC (not clang) you may need to comment out the next two lines:
    if sys.platform == 'darwin' and os.environ["CXX"] == "g++":
        # (note the test for g++ means clang, confusingly...)
        c_opts['unix'] += ['-stdlib=libc++', '-mmacosx-version-min=10.7']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        #if ct == 'unix':
        #    opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
        #    opts.append(cpp_flag(self.compiler))   # AHB: C++11 not used now, but David Stein says needed.
        #    if has_flag(self.compiler, '-fvisibility=hidden'):
        #        opts.append('-fvisibility=hidden')
        #elif ct == 'msvc':
        #    opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
        #for ext in self.extensions:
        #    ext.extra_compile_args = opts
        build_ext.build_extensions(self)


########## SETUP ###########
setup(
    name='finufftpy',
    version=__version__,
    author='python interfaces by: Jeremy Magland, Daniel Foreman-Mackey, Alex Barnett',
    author_email='abarnett@flatironinstitute.org',
    url='http://github.com/ahbarnett/finufft',
    description='python interface to FINUFFT',
    long_description='python interface to FINUFFT (Flatiron Institute Nonuniform Fast Fourier Transform) library.',
    license="Apache 2",
    ext_modules=ext_modules,
    packages=['finufftpy'],
    install_requires=['numpy','pybind11>=2.2'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False
)

