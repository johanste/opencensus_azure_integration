from distutils.core import setup

setup(
    name='opencensus-azure-integration',
    version='0.0.1-dev',
    packages=['oc_azure', 'oc_azure.msrest' ],
    license='MIT',
    long_description=open('README.txt').read(),
    install_requires=[ 'opencensus', 'wrapt' ],
)