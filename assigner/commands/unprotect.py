import logging

from assigner import manage_repos

help="Unprotect a repo branch"

logger = logging.getLogger(__name__)

def unprotect(args):
    """Unprotect a branch in each student's repository so they can force push to it."""
    branch = args.branch if args.branch else "master"
    return manage_repos(args, lambda repo, _: repo.unprotect(branch))

def setup_parser(parser):
    parser.add_argument("name",
                           help="Name of the assignment to unprotect.")
    parser.add_argument("--branch",
                           help="Branch to unprotect (default: master).")
    parser.add_argument("--section", nargs="?",
                           help="Section to unprotect")
    parser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment to unprotect.")
    parser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    parser.set_defaults(run=unprotect)

