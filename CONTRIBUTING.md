# Installation

You'll want to install an *editable* copy of Assigner using `pip`.
This allows you to make changes to the Assigner source while still having `pip` manage your dependencies.

1. Clone the repository somewhere and `cd` into the cloned repo.
2. Run `pip install --user -e .`

Alternatively, you can use `virtualenv`.
`requirements.txt` contains all of the needed packages which you can pass to `pip` once you've activated `virtualenv`.

# Making changes

Pull requests are welcome! If you have questions, feel free to [contact the authors](jarus@mst.edu) or open a WIP PR.

Before merging:

- Describe the change in `CHANGELOG.md`
- Make sure `pyflakes assigner` passes with no errors/warnings
- Check `pylint assigner` and make sure it's not too egregious. (Eventually we'll get the code to a point where there are no messages from `pylint`...)

# Design Philosophy

1. Make as few assumptions about how Assigner will be used as possible. This should be a tool that people can use for a variety of class styles.
1. Users should not be afraid of using Assigner. Commands should be idempotent and not run the risk of losing students' work to the fullest extent possible.
1. Hold as little metadata as possible. Currently we record nothing about assignments in `_config.yml`;
    someone could theoretically create a bunch of repos by hand and use `assigner` to manage them, provided they were named properly.

# Versioning

After version 1.0, Assigner's version (x.y.z) is incremented as follows:

- x: Major new feature; typically a new command
- y: Improvement to an existing command
- z: Bug fix or error handling improvement

# Distribution

1. Update the version in `setup.py`
2. Update `CHANGELOG.md`
3. Commit
4. `git tag` the release commit
5. Create a source distribution: `python setup.py sdist`
6. Create a binary distribution: `python setup.py bdist_wheel`
7. Upload distributions to pypi
