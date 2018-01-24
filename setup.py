"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='assigner',

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    version='1.1.0',

    description='Automatically assign programming homework to students on GitLab',
    long_description=long_description,

    url='https://github.com/redkyn/assigner',

    author='N. Jarus, M. Wisely, & T. Morrow',

    author_email='jarus@mst.edu',

    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Education',
        'Topic :: Education',
        'Topic :: Software Development :: Version Control :: Git',
        'Environment :: Console',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4', # TODO what is the minimum py3 version we support?
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #keywords='sample setuptools development',

    packages=find_packages(),

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    install_requires=[
        'GitPython>=1',
        'PyYAML>=3.11',
        'colorlog>=2.6,<3', # TODO can we move to v3?
        'jsonschema>=2.5',
        'requests==2.9.1', # TODO can we upgrade?
        'PTable>=0.9',
        'tqdm>=4',
    ],

    tests_require=[
        'nose',
        'nose-parameterized',
    ],

    python_requires='>=3',

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    #extras_require={
    #    'dev': ['check-manifest'],
    #    'test': ['coverage'],
    #},

    test_suite='nose.collector',

    data_files=[
        ('share/assigner', ['TUTORIAL.md', '_config.example.yml'])
    ],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    entry_points={
        'console_scripts': [
            'assigner=assigner:main',
        ],
    },
)
