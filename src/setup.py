from setuptools import setup  # pragma: no cover

setup(  # pragma: no cover
    name="assigner",
    version="0.0.1",  # http://semver.org/spec/v2.0.0.html
    url='https://github.com/redkyn/assigner',
    description="A tool for managing student assignments in GitLab",
    packages=['assigner'],
    package_dir={'assigner': 'assigner'},
    install_requires=[
        'GitPython==1.0.1',
        'PyYAML==3.11',
        'colorlog==2.6.0',
        'flake8==2.5.1',
        'gitdb==0.6.4',
        'jsonschema==2.5.1',
        'mccabe==0.3.1',
        'pep8==1.5.7',
        'pyapi-gitlab==7.8.5',
        'pyflakes==1.0.0',
        'requests==2.9.1',
        'six==1.10.0',
        'smmap==0.9.0',
        'wheel==0.24.0',
        'PTable==0.9.2',
        'progressbar2==3.10.1'
    ],
    entry_points={
        'console_scripts': ['assigner = assigner:run'],
    },
)
