from setuptools import setup  # pragma: no cover

setup(  # pragma: no cover
    name="assigner",
    version="0.0.1",  # http://semver.org/spec/v2.0.0.html
    url='https://github.com/redkyn/assigner',
    description="A tool for managing student assignments in GitLab",
    packages=['assigner'],
    package_dir={'assigner': 'assigner'},
    install_requires=[
        'requests==2.9.1',
        'colorlog==2.6.0',
        'PTable==0.9.2',
        'progressbar2==3.10.1',
        'jsonschema==2.5.1',
        'PyYAML==3.11',
        'GitPython==1.0.1'
    ],
    entry_points={
        'console_scripts': ['assigner = assigner:run'],
    },
)
