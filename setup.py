import os
import shutil
import sys
from platform import system
from subprocess import check_call

from setuptools import setup, find_namespace_packages, Extension
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir='', cmake_args=None):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)
        self.cmake_args = cmake_args


class CmdCMakeBuild(build_ext):
    def build_extension(self, ext):
        self.build_extension_pybind11(ext)
        super().build_extension(ext)

    def build_extension_pybind11(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable,
                      '-DBUILD_TESTING=OFF']

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']

        if os.path.exists(self.build_temp):
            shutil.rmtree(self.build_temp)
        os.makedirs(self.build_temp)

        _ext_name = ext.name.split('.')[-1]
        cmake_args.extend([f'-DOSQP_EXT_MODULE_NAME={_ext_name}'])
        if ext.cmake_args is not None:
            cmake_args.extend(ext.cmake_args)

        check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp)
        check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)


algebra = os.environ.get('OSQP_ALGEBRA', 'mkl')
assert algebra in ('default', 'mkl', 'cuda')
ext_name = f'osqp_{algebra}'
ext_module = CMakeExtension(ext_name, cmake_args=[f'-DALGEBRA={algebra}'])

setup(name=ext_name,
      author='Bartolomeo Stellato, Goran Banjac',
      author_email='bartolomeo.stellato@gmail.com',
      description='OSQP: The Operator Splitting QP Solver',
      long_description=open('README.rst').read(),
      package_dir={'': 'src'},
      include_package_data=True,  # Include package data from MANIFEST.in
      install_requires=['numpy>=1.7', 'scipy>=0.13.2', 'qdldl'],
      license='Apache 2.0',
      url="https://osqp.org/",
      cmdclass={'build_ext': CmdCMakeBuild},
      packages=find_namespace_packages(where='src'),
      ext_modules=[ext_module]
)
