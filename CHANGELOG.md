## Devel

- Removed remaining lint as specified by pylint.
- Removed old baserepo standalone code.
- Added Travis CI config for pylint and pyflakes.
- Warn when an assignment is already open for a student when running `open`

## 1.0.0

- Rename `token` to `gitlab-token` in the configuration file
- Display push time, rather than commit time, in `status` output
- Show push time in human-readable format in the current locale's timezone
- Display an informative error message when attempting to push an empty base repo
- Allow users to assign multiple branches in one call to `assign`
- Print help for the subcommand when `assigner help <command>` is run
- Fetch and pull branches when `get` is run if student repositories have already been cloned

## 0.1.0

This is the """"initial release""" that's been in use for a couple years now.
If you want to know what happened prior to this, sorry, you're going to have to read the commit log.
