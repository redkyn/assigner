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

# Distribution

1. Update the version in `setup.py`
2. Update `CHANGELOG.md`
3. Commit
4. `git tag` the release commit
5. Create a source distribution: `python setup.py sdist`
6. Create a binary distribution: `python setup.py bdist_wheel`
7. Upload distributions to pypi
