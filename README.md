# Assigner

*Assigner* automatically creates a number of repositories within a GitLab group (or user).
The repositories represent homework assignments being assigned to a list of students.

The repositories are created as private with the instructor (the one running *Assigner*) as owner and each student as a Developer.
By doing this, students do not need group permission (which would allow them to see other students' repos), but instead are given individual permissions on their repositories within the group.

The student repositories that are created receive some initial content from some base repo, a link to which must be provided to *Assigner* as an argument.

The list of students is retrieved from a JSON file, the name of which must be provided to *Assigner* as an argument.

## Installation

It is recommended that you use `virtualenv`.
`requirements.txt` contains all of the needed packages which you can pass to `pip` once you've activated `virtualenv`.

## Usage

```

assigner.py [HW repo url] [Roster file name].json

```

#### SSH
Your GitLab account must have an SSH key set up in order to push the assignment to the students' repos.

#### Configuration File
*Assigner* will create a `_config.yml` file that

## Credits

- Ty Morrow
- Mike Wisely
