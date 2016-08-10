# Assigner

*Assigner* automatically creates a number of repositories within a GitLab group (or user).
The repositories represent homework assignments being assigned to a list of students.

The repositories are created as private with the instructor (the one running *Assigner*) as owner and each student as a Developer.
By doing this, students do not need group permission (which would allow them to see other students' repos), but instead are given individual permissions on their repositories within the group.

The student repositories that are created receive some initial content from some base repo, a link to which must be provided to *Assigner* as an argument.

The list of students is retrieved from either a default YAML file or a specified one.

## Installation

Just clone the repo somewhere and run the `assigner` script.
It will fetch all necessary dependencies the first time it is run.

You can place a symlink to `assigner` in a folder in your `$PATH` if you desire.
For instance, `ln -s $(pwd)/assigner ~/bin/assigner`.

## Commands

- `new <assignment>` Creates a new base repository for an assignment so that you can add the instructions, sample code, etc.
- `assign <assignment>` Creates homework repositories for an assignment for each student in the roster.
- `open <assignment>` Adds each student in the roster to their respective homework repositories as Developers so they can pull/commit/push their work.
- `get <assignment> [<path>]` Creates a folder for the assignment in the CWD (or `<path>`, if specified) and clones each students' repository into subfolders.
- `lock <assignment>` Sets each student to Reporter status on their homework repository so they cannot push changes, etc.
- `unlock <assignment>` Sets each student to Developer status on their homework repository.
- `import <file> <section>` Imports students from a CSV file to the roster.
- `config <key> <value>` Sets `<key>` to `<value>` in the config.
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

You can set these keys by either manually adding them to the config or through using the `config` subcommand.

#### Importing
Joe'SS offers a button to download a table of all the students in a section.
For whatever reason, the developers at Oracle decided that this button should give you an HTML table in a file named `pg.xls` (or something like that).
You can download this file, open in LibreOffice (or some other piece of software that tramples your freedom), and save as a `.csv` file.
The `import` command can read the resulting `.csv` and import your students' data for you.

#### Extra Help
If you are particularly baffled, you can pass the `-h` or `--help` flag to any *Assigner* command for more details on what it offers.
For example, `get --help` will get you help with `get`.

## Developing

It is recommended that you use `virtualenv`.
`requirements.txt` contains all of the needed packages which you can pass to `pip` once you've activated `virtualenv`.

## Credits

- Ty Morrow
- Mike Wisely
- Nate Jarus
