from setuptools import setup, find_packages

setup(
    name='isaaq',
    version='0.1',
    description='Ising Machine-Assisted Quantum Compiler',
    author='Soshun Naito',
    author_email='soshun1005hamburg@gmail.com',
    packages=find_packages(),
    package_data={'isaaq': ['internal_data/**/*']},
    include_package_data=True,
)
