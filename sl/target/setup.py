from setuptools import setup, find_packages

setup(
    name='slpy',
    version='5.02',
    description='Steam locomotive running across terminal in pure Python',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'slpy=slpy.command_line:main',
        ],
    },
)
