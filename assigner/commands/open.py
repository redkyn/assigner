import logging

from requests.exceptions import HTTPError

from assigner.roster_util import get_filtered_roster
from assigner.baserepo import Access, Repo, RepoError, StudentRepo
from assigner.config import config_context
from assigner.progress import Progress

help = "Grants students access to their repos"

logger = logging.getLogger(__name__)

def open_assignment(repo, student):
    try:
        logging.debug("Opening %s...", repo.name)
        repo.add_member(student["id"], Access.developer)
    except HTTPError as e:
        if e.response.status_code == 409:
            logging.warning("%s is already a member of %s.", student["username"], repo.name)
        else:
            raise

@config_context
def open_all_assignments(conf, args):
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
        full_name = StudentRepo.build_name(semester, student_section,
                                           hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            if "id" not in student:
                student["id"] = Repo.get_user_id(username, host, token)

            open_assignment(repo, student)
            count += 1
        except RepoError:
            logging.warning("Could not add %s to %s.", username, full_name)

    progress.finish()

    print("Granted access to {} repositories.".format(count))


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to grant access to")
    parser.add_argument("--section", nargs="?",
                        help="Section to grant access to")
    parser.add_argument("--student", metavar="id",
                        help="ID of the student to assign to.")
    parser.set_defaults(run=open_all_assignments)
