from setuptools import setup, find_packages
from glob import glob
import os

filenames = list(glob('isaaq/data/**/*.*', recursive=True))
data_files = dict()
for filename in filenames:
    dirname = "dst"
    if(dirname not in data_files): data_files[dirname] = [filename]
    else: data_files[dirname].append(filename)

setup(
    name='isaaq',
    version='0.1',
    description='Ising Machine-Assisted Quantum Compiler',
    author='Soshun Naito',
    author_email='soshun1005hamburg@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    data_files=sorted(list(data_files.items())),
)