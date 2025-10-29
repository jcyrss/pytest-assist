from setuptools import setup

with open('pytest_assist/version.py') as f:
    productInfo = f.read()

import re
Version = re.findall(r'VERSION\s*=\s*[\'"](.+?)[\'"]', productInfo)[0]
print(f'$$$$ Version: {Version}')

setup(
    version      = Version,
)