import logging
import tempfile
import time

from roster_util import get_filtered_roster
from baserepo import BaseRepo, StudentRepo
from config import config_context

help="Assign a base repo to students"

logger = logging.getLogger(__name__)


@config_context
def assign(conf, args):
    """Creates homework repositories for an assignment for each student
    in the roster.
    """
    hw_name = args.name
    if args.branch:
        branch = args.branch
    else:
        branch = "master"
    dry_run = args.dry_run
    force = args.force
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token
    semester = conf.semester

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    actual_count = 0  # Represents the number of repos actually pushed to
    student_count = len(roster)

    with tempfile.TemporaryDirectory() as tmpdirname:
        print("Assigning '{}' to {} student{} in {}.".format(
            hw_name, student_count,
            "s" if student_count != 1 else "",
            "section " + args.section if args.section else "all sections")
        )
        base = BaseRepo(host, namespace, hw_name, token)
        if not dry_run:
            base.clone_to(tmpdirname, branch)
        if force:
            logging.warning("Repos will be overwritten.")
        for i, student in enumerate(roster):
            username = student["username"]
            student_section = student["section"]
            full_name = StudentRepo.name(semester, student_section,
                                         hw_name, username)
            repo = StudentRepo(host, namespace, full_name, token)

            print("{}/{} - {}".format(i+1, student_count, full_name))
            if not repo.already_exists():
                if not dry_run:
                    repo = StudentRepo.new(base, semester, student_section,
                                           username, token)
                    repo.push(base, branch)
                    repo.unprotect(branch)
                actual_count += 1
                logging.debug("Assigned.")
            elif force:
                logging.info("{}: Already exists.".format(full_name))
                logging.info("{}: Deleting...".format(full_name))
                if not dry_run:
                    repo.delete()
                    # HACK: Gitlab will throw a 400 if you delete and immediately recreate a repo.
                    # A bit more than half a second was experimentally determined to prevent this issue.
                    time.sleep(0.55)
                    repo = StudentRepo.new(base, semester, student_section,
                                           username, token)
                    repo.push(base, branch)
                    repo.unprotect(branch)
                actual_count += 1
                logging.debug("Assigned.")
            elif args.branch:
                logging.info("{}: Already exists.".format(full_name))
                # If we have an explicit branch, push anyways
                if not dry_run:
                    repo.push(base, branch)
                    repo.unprotect(branch)
                actual_count += 1
                logging.debug("Assigned.")
            else:
                logging.warning("Skipping...")
            i += 1

    print("Assigned '{}' to {} student{}.".format(
        hw_name,
        actual_count,
        "s" if actual_count != 1 else ""
    ))
    if actual_count == 0:
        logging.warning(
            "Consider using --force if you want to override existing repos."
        )


def setup_parser(parser):
    parser.add_argument("name",
                           help="Name of the assignment to assign.")
    parser.add_argument("--branch", nargs="?",
                           help="Branch to push")
    parser.add_argument("--section", nargs="?",
                           help="Section to assign homework to")
    parser.add_argument("--student", metavar="id",
                           help="ID of the student to assign to.")
    parser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    parser.add_argument("-f", "--force", action="store_true", dest="force",
                           help="Delete and recreate already existing " +
                                "student repos.")
    parser.set_defaults(run=assign)
