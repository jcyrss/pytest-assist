from setuptools import find_packages, setup
from os.path import join

from pytest_assist.version import VERSION

with open('README.md', encoding='utf8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name         = 'pytest-assist',
    version      = VERSION,
    author       = 'byhy',
    author_email = 'jcyrss@gmail.com',
    url          = 'https://jcyrss.github.io/pytest-assist',
    download_url = 'https://pypi.python.org/pypi/pytest-assist',
    license      = 'MIT',
    description  = 'load testing library',
    long_description = LONG_DESCRIPTION,
    long_description_content_type = 'text/markdown',
    keywords     = 'pytest automation testautomation',

    python_requires = '>=3.8',
    
    classifiers  = """
Intended Audience :: Developers
Topic :: Software Development :: Testing
License :: OSI Approved :: MIT License
""".strip().splitlines(),
  
    packages     = find_packages(
        include = ['pytest_assist']
    ),
    
    package_data = {'pytest_assist': ['**\*.html','**\*.js','**\*.css','**\*.png',]},
        
    install_requires=[   
        'pytest',
        'websockets>=11.0.3', 
    ],
)