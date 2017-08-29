# Assigner

*Assigner* automatically creates a number of repositories within a GitLab group (or user).
The repositories represent homework assignments being assigned to a list of students.

The repositories are created as private with the instructor (the one running *Assigner*) as owner and each student as a Developer.
By doing this, students do not need group permission (which would allow them to see other students' repos), but instead are given individual permissions on their repositories within the group.

The student repositories that are created receive some initial content from some base repo, a link to which must be provided to *Assigner* as an argument.

The list of students is retrieved from either a default YAML file or a specified one. See `_config.example.yml` for an example YAML configuration file.

## Installation

### Linux or macOS

Just clone the repo somewhere and run the `assigner` script.
It will fetch all necessary dependencies the first time it is run.
You need to have `virtualenv` installed for this to work.

On Linux (or things with `readlink -f`), you can place a symlink to `assigner` in a folder in your `$PATH` if you desire.
For instance, `ln -s $(pwd)/assigner ~/bin/assigner`.

For macOS, we recommend placing a small script that calls `assigner` in a folder in your `$PATH`.

Alternatively, you could add the folder containing the `assigner` source to your `$PATH`.

### Windows

We have not tested *Assigner* on Windows; however, we expect that it should work without much of a hitch.
To run *Assigner*, have a look at the steps the `assigner` script takes; you will need to do these manually or write a batch script that does them.

The gist is:

1. Initialize a new virtualenv with Python 3 support.
2. Install the dependencies listed in `requirements.txt` in the virtualenv.
3. Run `assigner.py` using your virtualenv's `python`.

## Commands

Check out the [tutorial](https://github.com/redkyn/assigner/blob/master/TUTORIAL.md) for a walkthrough of how to use Assigner's features!

- `new <assignment>` Creates a new base repository for an assignment so that you can add the instructions, sample code, etc.
- `assign <assignment>` Creates homework repositories for an assignment for each student in the roster.
- `open <assignment>` Adds each student in the roster to their respective homework repositories as Developers so they can pull/commit/push their work.
- `get <assignment> [<path>]` Creates a folder for the assignment in the CWD (or `<path>`, if specified) and clones each students' repository into subfolders.
- `lock <assignment>` Sets each student to Reporter status on their homework repository so they cannot push changes, etc.
- `unlock <assignment>` Sets each student to Developer status on their homework repository.
- `archive <assignment>` Archives student repositories, disallowing pushes and hiding the repository from the project listing on GitLab.
- `unarchive <assignment>` Restores archived student repositories to their previous state.
- `protect <branch>` Protect a repo branch (prevent force pushes)
- `unprotect <branch>` Unprotect a repo branch
- `status <assignment>` Shows the status of student homework repositories, as well as the last commit author and timestamp for each repository.
- `import <file> <section>` Imports students from a CSV file to the roster.
- `canvas` Lists Canvas courses or imports students from a Canvas course to the roster.
- `set <key> <value>` Sets `<key>` to `<value>` in the config.
- `roster` Manages the course roster.
- `init` Creates a new configuration file, interactively prompting for required values.
- `help` What it says on the tin.

#### SSH
Your GitLab account must have an SSH key set up in order to push the assignment to the students' repos.

#### Configuration File
*Assigner* will create a `_config.yml` file that will persist your GitLab private token and other settings.
You can use a different config file by specifying the `--config` option.

*Assigner* needs you to set a few config keys before it will work:
- `gitlab-host`: Hostname of your gitlab instance
- `namespace`: Group or user to create repositories in
- `semester`: The semester; recommended formatting: `2016SP`
- `token`: Your gitlab API token, retrievable from your gitlab settings page
- `canvas-token`: Your Canvas API token, retrievable from your Canvas settings page

You can set these keys by either manually adding them to the config or through using the `config` subcommand.

#### Importing from Joe'SS via CSV file
Joe'SS offers a button to download a table of all the students in a section.
For whatever reason, the developers at Oracle decided that this button should give you an HTML table in a file named `pg.xls` (or something like that).
You can download this file, open in LibreOffice (or some other piece of software that tramples your freedom), and save as a `.csv` file.
The `import` command can read the resulting `.csv` and import your students' data for you.

#### Importing from Canvas via the Canvas API
The Canvas API can be used to retrieve the list of students for each course section.
You can use the `canvas list` command to list your course sections, and make note of the ID of the course you would like to import students from. Then you can use the `canvas import` command with the appropriate course ID to import the students from the course section into your configuration file.

#### Extra Help
If you are particularly baffled, you can pass the `-h` or `--help` flag to any *Assigner* command for more details on what it offers.
For example, `get --help` will get you help with `get`.

## Generating Access Tokens

### GitLab Token:
To generate an access token for GitLab, log onto the GitLab website (e.g. https://git-classes.mst.edu/), and go to your *Profile Settings*. Go to the *Access Token* tab, then add a personal access token using the form on the page. Leave the expiry date empty to create a token that never expires, and select the **api** checkbox to allow API access using your token. Make sure you copy the generated token, since you won't be able to retrieve it afterwards.

### Canvas Token:
To generate an API token for Canvas, log onto your Canvas account (e.g. https://canvas.mst.edu/), and click on *Account* at the top left corner of the page, then go to *Settings*. From there scroll down to *Approved Integrations* and click the **New Access Token** button, then use the form to create a new API token. Make sure you copy the generated token, since you won't be able to retrieve it afterwards.

## Developing

It is recommended that you use `virtualenv`.
`requirements.txt` contains all of the needed packages which you can pass to `pip` once you've activated `virtualenv`.

## Credits

- Ty Morrow
- Mike Wisely
- Nate Jarus
