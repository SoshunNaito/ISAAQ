from setuptools import setup, find_packages
# from glob import glob
# import os

# filenames = list(glob('isaaq/data/**/*.*', recursive=True))
# files = dict()
# for filename in filenames:
#     dirname = os.path.dirname(filename)
#     if(dirname not in files): files[dirname] = [filename]
#     else: files[dirname].append(filename)

setup(
    name='isaaq',
    version='0.1',
    description='Ising Machine-Assisted Quantum Compiler',
    author='Soshun Naito',
    author_email='soshun1005hamburg@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    # data_files=sorted(list(files.items())),
)