#!/usr/bin/python

"""
Setup for API Tackle
"""

# https://packaging.python.org/tutorials/packaging-projects/
# https://packaging.python.org/en/latest/distributing.html
# https://github.com/pypa/sampleproject

import re
from codecs import open

import setuptools


def get_version(fname):
    """
    Extracts __version__ from {fname}
    """
    verstrline = open(fname, "rt").read()
    mob = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)
    if mob:
        return mob.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (fname,))


def get_requirements(fname):
    """
    Extracts requirements from requirements-file <fname>
    """
    reqs = open(fname, "rt").read().strip("\r").split("\n")
    requirements = [
        req for req in reqs
        if req and not req.startswith("#") and not req.startswith("--")
    ]
    return requirements


with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='api_tackle',

    version=get_version('tackle/__init__.py'),
    description='API Tackle - Simple Python REST API Framework',

    long_description=long_description,

    url='https://github.com/???/api-tackle',

    author='bernardt@preakelt.com',
    author_email='bernardt@preakelt.com',

    license='BSD 3-Clause License',

    keywords='REST API framework',

    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=get_requirements('requirements_ref.txt'),
    scripts=[],

    # package_data={'': ['data/???',
    #                    'rest_api/flask_server/swagger/swagger.yaml']},
    # include_package_data=True,

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
)
