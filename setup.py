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

    # Derive version from git tags
    use_scm_version=True,

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
        'Development Status :: 5 - Production/Stable',

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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #keywords='sample setuptools development',

    packages=find_packages(),

    setup_requires=['setuptools_scm>=1.15'],

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    install_requires=[
        'GitPython>=2.1.8',
        'PyYAML>=3.13',
        'colorlog>=2.6,<3', # TODO can we move to v3?
        'jsonschema>=2.5',
        'requests>=2.20.0',
        'PTable>=0.9',
        'enlighten>=1.5.0',
        'redkyn-common>=1.0.1',
    ],

    tests_require=[
        'nose',
        'nose-parameterized',
    ],

    python_requires='>=3.4',

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
