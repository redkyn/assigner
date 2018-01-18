import logging

from assigner import manage_repos
from assigner.baserepo import Access

help = "Lock students out of repos"

logger = logging.getLogger(__name__)


def lock(args):
    """Sets each student to Reporter status on their homework repository so
    they cannot push changes, etc.
    """
    #pylint: disable=no-value-for-parameter
    return manage_repos(
        args,
        lambda repo, student: repo.edit_member(student["id"], Access.reporter)
    )


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to lock.")
    parser.add_argument("--section", nargs="?",
                        help="Section to lock")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment needs locking.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=lock)
