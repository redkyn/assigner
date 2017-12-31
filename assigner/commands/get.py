import logging
import os

from requests.exceptions import HTTPError

from roster_util import get_filtered_roster
from baserepo import RepoError, StudentRepo
from config import config_context

help="Clone student repos"

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
    token = conf.token
    semester = conf.semester

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    path = os.path.join(hw_path, hw_name)
    os.makedirs(path, mode=0o700, exist_ok=True)

    count = 0
    for student in roster:
        username = student["username"]
        student_section = student["section"]
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            repo.clone_to(os.path.join(path, username))
            count += 1
        except RepoError as e:
            logging.warn(str(e))
        except HTTPError as e:
            if e.response.status_code == 404:
                logging.warn("Repository {} does not exist.".format(full_name))
            else:
                raise

    print("Cloned {} repositories.".format(count))


def setup_parser(parser):
    parser.add_argument("name",
                           help="Name of the assignment to retrieve.")
    parser.add_argument("path", default=".", nargs="?",
                           help="Path to clone student repositories to")
    parser.add_argument("--section", nargs="?",
                           help="Section to retrieve")
    parser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment needs " +
                                "retrieving.")
    parser.set_defaults(run=get)
