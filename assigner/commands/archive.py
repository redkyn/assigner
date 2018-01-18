import logging

from assigner import manage_repos

help = "Archive repos"

logger = logging.getLogger(__name__)


def archive(args):
    """Archive each student repository so it won't show up in the project list.
    """
    #pylint: disable=no-value-for-parameter
    return manage_repos(args, lambda repo, _: repo.archive())


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to archive.")
    parser.add_argument("--section", nargs="?",
                        help="Section to archive")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment to archive.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=archive)
