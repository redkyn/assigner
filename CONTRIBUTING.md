# Reporting Issues

If Assigner is misbehaving, please file an issue!
When you do so, please include the following information:

1. The version of Assigner you are running and what OS you're running it on
1. The steps you took that led to the error
1. What you expected
1. What Assigner did instead

If Assigner is reporting errors or exceptions, please also include the output of `assigner --tracebacks --verbosity=DEBUG <command you ran>`.
For example, if `assigner get the_homework` is giving you trouble, you'd run `assigner --tracebacks --verbosity=DEBUG get the_homework`.
(You may need to redact parts of the output to protect the privacy of your students.)

# Making changes

Pull requests are welcome! If you have questions, feel free to [contact the authors](mailto:jarus@mst.edu) or open a WIP PR.

Before merging:

- Describe the change in `CHANGELOG.md`
- Create supporting unit tests
- Verify new and existing unit tests pass with `python setup.py nosetests`
- Make sure `pyflakes assigner` passes with no errors/warnings
- Make sure `pylint assigner` passes with no errors/warnings
- Update `requirements.txt` and `setup.py` with any new dependencies or version bumps

## Installation for Developing

You'll want to install an *editable* copy of Assigner using `pip`.
This allows you to make changes to the Assigner source while still having `pip` manage your dependencies.

1. Clone the repository somewhere and `cd` into the cloned repo
1. Run `pip install --user -e .`

To run unit tests, `pyflakes`, and `pylint`, you'll want to set up a [virtualenv](https://virtualenv.pypa.io/):

1. `cd` into your cloned repo
1. Run `virtualenv -p python3 env` to create a new environment
1. Run `source env/bin/activate`
1. Run `pip install -r requirements.txt`

From here on, before running unit tests or the like, run `source env/bin/activate` and the software installed in your virtualenv will be used instead of the system defaults.

# Design Philosophy

1. Make as few assumptions about how Assigner will be used as possible. This should be a tool that people can use for a variety of class styles.
1. Users should not be afraid of using Assigner. Commands should be idempotent and not run the risk of losing students' work to the fullest extent possible.
1. Hold as little metadata as possible. Currently we record nothing about assignments in `_config.yml`;
    someone could theoretically create a bunch of repos by hand and use `assigner` to manage them, provided they were named properly.

# Distribution

## Versioning

After version 1.0, Assigner's version (x.y.z) is incremented as follows:

- x: Major new feature; typically a new command
- y: Improvement to an existing command
- z: Bug fix or error handling improvement

## Cutting a new release

1. Update `CHANGELOG.md`
1. Commit
1. `git tag` the release commit
1. Create a source distribution: `python setup.py sdist`
1. Create a binary distribution: `python setup.py bdist_wheel`
1. Upload distributions to pypi: `twine upload dist/*`
