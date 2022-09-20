from setuptools import setup, find_packages
from glob import glob

setup(
    name='isaaq',
    version='0.1',
    description='Ising Machine-Assisted Quantum Compiler',
    author='Soshun Naito',
    author_email='soshun1005hamburg@gmail.com',
    data_files=[
        ('data', glob('data/**/*', recursive=True))
    ],
)