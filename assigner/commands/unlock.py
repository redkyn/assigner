import logging

from assigner import manage_repos
from assigner.backends.exceptions import (
        UserInAssignerGroup,
        UserNotAssigned,
    )

help = "Unlock student's repo"

logger = logging.getLogger(__name__)


def unlock(args):
    """Sets each student to Developer status on their homework repository.
    """
    #pylint: disable=no-value-for-parameter
    return manage_repos(args, _unlock)

def _unlock(repo, student):
    try:
        repo.unlock(student["id"])
        return True
    except UserInAssignerGroup:
        logging.info("%s cannot be locked out because they are a member of the group, skipping...", student["username"])
        return False
    except UserNotAssigned:
        logging.info("%s has not been assigned for %s", repo.name, student["username"])
        return False

def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to unlock.")
    parser.add_argument("--section", nargs="?",
                        help="Section to unlock")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment needs unlocking.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=unlock)
