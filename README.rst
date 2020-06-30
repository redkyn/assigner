Assigner |pypi| |travis|
========================

.. |pypi| image:: https://badge.fury.io/py/assigner.svg
    :target: https://badge.fury.io/py/assigner
    :alt: PyPi package

.. |travis| image:: https://travis-ci.org/redkyn/assigner.svg?branch=master
    :target: https://travis-ci.org/redkyn/assigner
    :alt: Build Status

*Assigner* automatically creates a number of repositories within a GitLab group (or user).
The repositories represent homework assignments being assigned to a list of students.

The repositories are created as private with the instructor (the one running *Assigner*) as owner and each student as a Developer.
By doing this, students do not need group permission (which would allow them to see other students' repos), but instead are given individual permissions on their repositories within the group.

The student repositories that are created receive some initial content from some base repo, a link to which must be provided to *Assigner* as an argument.

The list of students is retrieved from either a default YAML file or a specified one. See ``_config.example.yml`` for an example YAML configuration file.

Installation
------------

Assigner can be installed with ``pip``: ``pip install assigner``.

(You may need to run ``pip3 install assigner`` if your operating system uses python 2 as the default python.)

Commands
--------

Check out the `tutorial <https://github.com/redkyn/assigner/blob/master/TUTORIAL.md>`_ for a walkthrough of how to use Assigner's features!

- ``init`` Creates a new configuration file, interactively prompting for required values.
- ``help`` What it says on the tin.
- ``new <assignment>`` Creates a new base repository for an assignment so that you can add the instructions, sample code, etc.
- ``assign <assignment>`` Creates homework repositories for an assignment for each student in the roster.
- ``open <assignment>`` Adds each student in the roster to their respective homework repositories as Developers so they can pull/commit/push their work.
- ``get <assignment> [<path>]`` Creates a folder for the assignment in the CWD (or ``<path>``, if specified) and clones each students' repository into subfolders or fetches their changes if their repository is already cloned.
- ``lock <assignment>`` Sets each student to Reporter status on their homework repository so they cannot push changes, etc.
- ``unlock <assignment>`` Sets each student to Developer status on their homework repository.
- ``archive <assignment>`` Archives student repositories, disallowing pushes and hiding the repository from the project listing on GitLab.
- ``unarchive <assignment>`` Restores archived student repositories to their previous state.
- ``protect <branch>`` Protect a repo branch (prevent force pushes)
- ``unprotect <branch>`` Unprotect a repo branch
- ``status <assignment>`` Shows the status of student homework repositories, as well as the last commit author and timestamp for each repository.
- ``roster`` Manages the course roster.
- ``canvas`` Lists Canvas courses or imports students from a Canvas course to the roster.
- ``import <file> <section>`` Imports students from a CSV file to the roster.
- ``set <key> <value>`` Sets ``<key>`` to ``<value>`` in the config.

SSH
~~~

Your GitLab account must have an SSH key set up in order to push the assignment to the students' repos.

Configuration File
~~~~~~~~~~~~~~~~~~

*Assigner* will create a ``_config.yml`` file in the current directory that will persist your GitLab private token and other settings.
You can use a different config file by specifying the ``--config`` option.

*Assigner* needs you to set a few config keys before it will work.
The easiest way to do this is by running ``assigner init`` and entering the information it prompts you for.
Alternatively, you can create yor own, following the template in ``_config.example.yml``.

You can change configuration settings by either manually editing the config or through using the ``set`` subcommand.

Importing from Canvas via the Canvas API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Canvas API can be used to retrieve the list of students for each course section.
You can use the ``canvas list`` command to list your course sections, and make note of the ID of the course you would like to import students from. Then you can use the ``canvas import`` command with the appropriate course ID to import the students from the course section into your configuration file.

Importing from Joe'SS via CSV file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Joe'SS offers a button to download a table of all the students in a section.
For whatever reason, the developers at Oracle decided that this button should give you an HTML table in a file named ``pg.xls`` (or something like that).
You can download this file, open in LibreOffice (or some other piece of software that tramples your freedom), and save as a ``.csv`` file.
The ``import`` command can read the resulting ``.csv`` and import your students' data for you.

Extra Help
~~~~~~~~~~
If you are particularly baffled, you can pass the ``-h`` or ``--help`` flag to any *Assigner* command for more details on what it offers.
For example, ``get --help`` will get you help with ``get``.

Generating Access Tokens
------------------------

GitLab Token
~~~~~~~~~~~~

To generate an access token for GitLab, log onto the GitLab website (e.g. https://git-classes.mst.edu/), and go to your *Profile Settings*. Go to the *Access Token* tab, then add a personal access token using the form on the page. Leave the expiry date empty to create a token that never expires, and select the *api* checkbox to allow API access using your token. Make sure you copy the generated token, since you won't be able to retrieve it afterwards.

Canvas Token
~~~~~~~~~~~~

To generate an API token for Canvas, log onto your Canvas account (e.g. https://canvas.mst.edu/), and click on *Account* at the top left corner of the page, then go to *Settings*. From there scroll down to *Approved Integrations* and click the *New Access Token* button, then use the form to create a new API token. Make sure you copy the generated token, since you won't be able to retrieve it afterwards.

Reporting Bugs
--------------

See |CONTRIBUTING.md|_.

.. this is an awful hack; see http://docutils.sourceforge.net/FAQ.html#is-nested-inline-markup-possible
.. |CONTRIBUTING.md| replace:: ``CONTRIBUTING.md``
.. _CONTRIBUTING.md: https://github.com/redkyn/assigner/blob/master/CONTRIBUTING.md

Credits
-------

- Ty Morrow
- Mike Wisely
- Natasha Jarus
- Islam Elnabarawy
- Billy Rhoades
