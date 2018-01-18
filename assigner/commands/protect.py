import logging

from assigner import manage_repos

help = "Protect a repo branch"

logger = logging.getLogger(__name__)


def protect(args):
    """Protect a branch in each student's repository so they cannot force push to it."""
    for branch in args.branch:
        logging.info("Protecting %s...", branch)
        #pylint: disable=no-value-for-parameter, cell-var-from-loop
        manage_repos(args, lambda repo, _: repo.protect(branch))

def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to protect.")
    parser.add_argument("--branch", "--branches", nargs="+", default=["master"],
                        help="Branch to protect (default: master).")
    parser.add_argument("--section", nargs="?",
                        help="Section to protect")
    parser.add_argument("--student", metavar="id",
                        help="ID of student whose assignment to protect.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=protect)
