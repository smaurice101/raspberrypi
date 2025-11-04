import setuptools
import os
from setuptools import setup

from os import path
with open("README.md", "r") as f:
    long_description = f.read()
	

with open("requirements.txt","r") as f:
    required = f.read().splitlines()
    
setuptools.setup(
    name='studenttestpackage',
    version='1.0',
    description='Test python packae for students',
    license='MIT License',
    packages=['studenttestpackage'],
    author='Sebastian Maurice',
    author_email='sebastian.maurice@otics.ca',
    keywords=['python, data science, machine learning ,artificial intelligence', 'predictive analytics', 'advanced analytics'],
    long_description=long_description,
    install_requires=required,
    long_description_content_type='text/markdown',
    url='https://github.com/smaurice101/transactionalmachinelearning'
)

