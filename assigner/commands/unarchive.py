import logging

from assigner import manage_repos

help = "Unarchive repos"

logger = logging.getLogger(__name__)


def unarchive(args):
    """Unarchive each student repository so it will show back up in the project list.
    """
    #pylint: disable=no-value-for-parameter
    return manage_repos(args, lambda repo, _: repo.unarchive())


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to unarchive.")
    parser.add_argument("--section", nargs="?",
                        help="Section to unarchive")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment to unarchive.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=unarchive)
