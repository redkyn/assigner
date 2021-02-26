import logging
import os
import subprocess

from requests.exceptions import HTTPError
from git.exc import NoSuchPathError

from assigner.roster_util import get_filtered_roster
from assigner.backends import RepoError
from assigner.backends.decorators import requires_config_and_backend
from assigner import progress

help = "Add and commit changes to student repos"

logger = logging.getLogger(__name__)


@requires_config_and_backend
def push(conf, backend, args):
    _push(conf, backend, args)

def _push(conf, backend, args):
    backend_conf = conf.backend
    namespace = conf.namespace
    semester = conf.semester

    hw_name = args.name
    hw_path = args.path
    message = args.message
    branch = args.branch
    add = args.add
    remove = args.remove
    update = args.update
    allow_empty = args.allow_empty
    gpg_sign = args.gpg_sign

    # Default behavior: commit changes to all tracked files
    if (add == []) and (remove == []):
        logging.debug("Nothing explicitly added or removed; defaulting to git add --update")
        update = True

    path = os.path.join(hw_path, hw_name)

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = backend.student_repo.build_name(semester, student_section,
                                                    hw_name, username)

        has_changes = False

        try:
            repo = backend.student_repo(backend_conf, namespace, full_name)
            repo_dir = os.path.join(path, username)
            repo.add_local_copy(repo_dir)

            logging.debug("%s: checking out branch %s", full_name, branch)
            repo.get_head(branch).checkout()
            index = repo.get_index()

            if update:
                # Stage modified and deleted files for commit
                # This exactly mimics the behavior of git add --update
                # (or the effect of doing git commit -a)
                for change in index.diff(None):
                    has_changes = True
                    if change.deleted_file:
                        logging.debug("%s: git rm %s", full_name, change.b_path)
                        index.remove([change.b_path])
                    else:
                        logging.debug("%s: git add %s", full_name, change.b_path)
                        index.add([change.b_path])

            if add:
                has_changes = True
                logging.debug("%s: adding %s", full_name, add)
                index.add(add)
            if remove:
                has_changes = True
                logging.debug("%s: removing %s", full_name, remove)
                index.remove(remove)

            if has_changes or allow_empty:
                logging.debug("%s: committing changes with message %s", full_name, message)
                if gpg_sign:
                    # The GitPython interface does not support signed commits, and
                    # launching via repo.git.commit will launch an inaccessible
                    # interactive prompt in the background
                    index.write(ignore_extension_data=True)
                    subprocess.check_call(["git", "commit", "-S", "-m", '"{}"'.format(message)],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                          cwd=repo_dir)
                else:
                    index.commit(message)
            else:
                logging.warning("%s: No changes in repo; skipping commit.", full_name)

        except NoSuchPathError:
            logging.warning("Local repo for %s does not exist; skipping...", username)
        except RepoError as e:
            logging.warning(e)
        except HTTPError as e:
            if e.response.status_code == 404:
                logging.warning("Repository %s does not exist.", full_name)
            else:
                raise

def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to commit to.")
    parser.add_argument("message",
                        help="Commit message")
    parser.add_argument("path", default=".", nargs="?",
                        help="Path of student repositories to commit to")
    parser.add_argument("--branch", nargs="?", default="master",
                        help="Local branch to commit to")
    parser.add_argument("-a", "--add", nargs="+", dest="add", default=[],
                        help="Files to add before committing")
    parser.add_argument("-r", "--remove", nargs="+", dest="remove", default=[],
                        help="Files to remove before committing")
    parser.add_argument("-u", "--update", action="store_true", dest="update",
                        help="Include all changed files (i.e., git add -u or git commit -a)")
    parser.add_argument("-e", "--allow-empty", action="store_true", dest="allow_empty",
                        help="Commit even if there are no changes to commit")
    parser.add_argument("-S", "--gpg-sign", action="store_true", dest="gpg_sign",
                        help="GPG-sign the commits using the committer identity")
    parser.add_argument("--section", nargs="?",
                        help="Section to commit to")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment is to be committed to.")
    parser.set_defaults(run=push)
