import logging

from requests.exceptions import HTTPError

from assigner.backends.base import RepoError
from assigner.backends.decorators import requires_config_and_backend
from assigner.backends.exceptions import UserInAssignerGroup
from assigner.roster_util import get_filtered_roster
from assigner import progress

help = "Grants students access to their repos"

logger = logging.getLogger(__name__)


def open_assignment(repo, student, access):
    try:
        logging.debug("Opening %s...", repo.name)
        repo.add_member(student["id"], access)
    except HTTPError as e:
        if e.response.status_code == 409:
            logging.warning("%s is already a member of %s.", student["username"], repo.name)
        else:
            raise


@requires_config_and_backend
def open_all_assignments(conf, backend, args):
    """Adds each student in the roster to their respective homework
    repositories as Developers so they can pull/commit/push their work.
    """
    hw_name = args.name
    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    count = 0
    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = backend.student_repo.build_name(semester, student_section,
                                                    hw_name, username)

        try:
            repo = backend.student_repo(backend_conf, namespace, full_name)
            if "id" not in student:
                student["id"] = backend.repo.get_user_id(username, backend_conf)

            open_assignment(repo, student, backend.access.developer)
            count += 1
        except UserInAssignerGroup:
            logging.info("%s already has access via group membership, skipping...", username)
        except RepoError:
            logging.warning("Could not add %s to %s.", username, full_name)

    print("Granted access to {} repositories.".format(count))


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to grant access to")
    parser.add_argument("--section", nargs="?",
                        help="Section to grant access to")
    parser.add_argument("--student", metavar="id",
                        help="ID of the student to assign to.")
    parser.set_defaults(run=open_all_assignments)
