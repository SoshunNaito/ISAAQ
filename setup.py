from setuptools import setup, find_packages
from glob import glob

data_files = [filename.replace('isaaq/data/','') for filename in glob('isaaq/data/**/*', recursive=True)]

setup(
    name='isaaq',
    version='0.1',
    description='Ising Machine-Assisted Quantum Compiler',
    author='Soshun Naito',
    author_email='soshun1005hamburg@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    data_files=[('data', data_files)],
)