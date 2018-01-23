import logging
import os

from requests.exceptions import HTTPError
from git.exc import NoSuchPathError, GitCommandError

from assigner.roster_util import get_filtered_roster
from assigner.baserepo import RepoError, StudentRepo
from assigner.config import config_context
from assigner.progress import Progress

from prettytable import PrettyTable

help = "Clone or fetch student repos"

logger = logging.getLogger(__name__)


@config_context
def get(conf, args):
    """Creates a folder for the assignment in the CWD (or <path>, if specified)
    and clones each students' repository into subfolders.
    """
    hw_name = args.name
    hw_path = args.path
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.gitlab_token
    semester = conf.semester
    branch = args.branch
    force = args.force

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    path = os.path.join(hw_path, hw_name)
    os.makedirs(path, mode=0o700, exist_ok=True)

    output = PrettyTable(["#", "Sec", "SID", "Name", "Change"], print_empty=False)
    output.align["Name"] = "l"
    output.align["Change"] = "l"

    progress = Progress()

    for i, student in progress.enumerate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = StudentRepo.build_name(semester, student_section,
                                           hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            repo_dir = os.path.join(path, username)

            row = str(i + 1)
            sec = student["section"]
            sid = student["username"]
            name = student["name"]

            try:
                logging.debug("Attempting to use local repo %s...", repo_dir)
                repo.add_local_copy(repo_dir)

                logging.debug("Local repo exists, fetching...")
                results = repo.repo.remote().fetch()
                for result in results:
                    logging.debug(
                        "fetch result: name: %s flags: %s note: %s",
                        result.ref.name,
                        result.flags,
                        result.note
                    )

                    # see:
                    # http://gitpython.readthedocs.io/en/stable/reference.html#git.remote.FetchInfo
                    if result.flags & result.NEW_HEAD:
                        output.add_row([
                            row, sec, sid, name, "{}: new branch at {}".format(
                                result.ref.name, str(result.ref.commit)[:8]
                            )
                        ])
                        row = sec = sid = name = "" # don't print user info more than once

                    elif result.old_commit is not None:
                        output.add_row([
                            row, sec, sid, name, "{}: {} -> {}".format(
                                result.ref.name, str(result.old_commit)[:8],
                                str(result.ref.commit)[:8]
                            )
                        ])
                        row = sec = sid = name = ""

                logging.debug("Pulling specified branches...")
                for b in branch:
                    try:
                        repo.get_head(b).checkout(force=force)
                        repo.pull(b)
                    except GitCommandError as e:
                        logging.debug(e)
                        logging.warning("Local changes to %s/%s would be overwritten by pull",
                                        username, b)
                        logging.warning("  (use --force to overwrite)")

                # Check out first branch specified; this is probably what people expect
                # If there's just one branch, it's already checked out by the loop above
                if len(branch) > 1:
                    repo.get_head(branch[0]).checkout()

            except NoSuchPathError:
                logging.debug("Local repo does not exist; cloning...")
                repo.clone_to(repo_dir, branch)
                output.add_row([row, sec, sid, name, "Cloned a new copy"])

        except RepoError as e:
            logging.warning(e)
        except HTTPError as e:
            if e.response.status_code == 404:
                logging.warning("Repository %s does not exist.", full_name)
            else:
                raise

    progress.finish()

    out_str = output.get_string()
    if out_str != "":
        print(out_str)
    else:
        print("No changes since last call to get")


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to clone or fetch.")
    parser.add_argument("path", default=".", nargs="?",
                        help="Path to clone student repositories to")
    parser.add_argument("--branch", "--branches", nargs="+", default=["master"],
                        help="Local branch or branches to pull when fetching")
    parser.add_argument("-f", "--force", action="store_true", dest="force",
                        help="Discard local changes to student repositories when fetching")
    parser.add_argument("--section", nargs="?",
                        help="Section to retrieve")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment needs retrieving.")
    parser.set_defaults(run=get)
