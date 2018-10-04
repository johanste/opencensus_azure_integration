from setuptools import find_packages, setup

setup(
    name='opencensus-azure-integration',
    version='0.0.1-dev',
    packages=find_packages(),
    namespace_packages=['opencensus'],
    license='MIT',
    long_description=open('README.txt').read(),
    install_requires=[ 'opencensus', 'wrapt' ],
)