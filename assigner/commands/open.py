import logging

from requests.exceptions import HTTPError

from assigner.roster_util import get_filtered_roster
from assigner.baserepo import Access, Repo, RepoError, StudentRepo
from assigner.config import config_context
from assigner.progress import Progress

help="Grants students access to their repos"

logger = logging.getLogger(__name__)


@config_context
def open_assignment(conf, args):
    """Adds each student in the roster to their respective homework
    repositories as Developers so they can pull/commit/push their work.
    """
    hw_name = args.name
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.gitlab_token
    semester = conf.semester

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    count = 0
    progress = Progress()
    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            if "id" not in student:
                student["id"] = Repo.get_user_id(username, host, token)

            repo.add_member(student["id"], Access.developer)
            count += 1
        except RepoError:
            logging.warn("Could not add {} to {}.".format(username, full_name))
        except HTTPError:
            raise

    progress.finish()

    print("Granted access to {} repositories.".format(count))


def setup_parser(parser):
    parser.add_argument("name", help="Name of the assignment to grant " +
                                        "access to")
    parser.add_argument("--section", nargs="?",
                           help="Section to grant access to")
    parser.add_argument("--student", metavar="id",
                           help="ID of the student to assign to.")
    parser.set_defaults(run=open_assignment)
