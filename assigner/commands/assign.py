import logging
import tempfile
import time

from assigner.backends.base import RepoError
from assigner.backends.decorators import requires_config_and_backend
from assigner.commands.open import open_assignment
from assigner import progress
from assigner.roster_util import get_filtered_roster

from requests.exceptions import HTTPError

help = "Assign a template repo to students"

logger = logging.getLogger(__name__)


@requires_config_and_backend
def assign(conf, backend, args):
    """Creates homework repositories for an assignment for each student
    in the roster.
    """
    hw_name = args.name
    if args.branch:
        branch = args.branch
    else:
        branch = ["master"]
    dry_run = args.dry_run
    force = args.force
    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    actual_count = 0  # Represents the number of repos actually pushed to
    student_count = len(roster)

    with tempfile.TemporaryDirectory() as tmpdirname:
        print("Assigning '{}' to {} student{} in {}.".format(
            hw_name, student_count,
            "s" if student_count != 1 else "",
            "section " + args.section if args.section else "all sections"
        ))
        template = backend.template_repo(backend_conf, namespace, hw_name)
        if not dry_run:
            try:
                template.clone_to(tmpdirname, branch)
            except RepoError as e:
                logging.error(
                    "Could not clone template repo (have you pushed at least one commit to it?)"
                )
                logging.debug(e)
                return

        if force:
            logging.warning("Repos will be overwritten.")

        for i, student in progress.enumerate(roster):
            username = student["username"]
            student_section = student["section"]
            full_name = backend.student_repo.build_name(semester, student_section,
                                                        hw_name, username)
            repo = backend.student_repo(backend_conf, namespace, full_name)

            if not repo.already_exists():
                if not dry_run:
                    repo = backend.student_repo.new(template, semester, student_section,
                                                    username)
                    repo.push(template, branch)
                    for b in branch:
                        repo.protect(b)
                actual_count += 1
                logging.debug("Assigned.")
            elif force:
                logging.info("%s: Already exists, deleting...", full_name)
                if not dry_run:
                    repo.delete()

                    # Gitlab will throw a 400 if you delete and immediately
                    # recreate a repo. We retry w/ exponential backoff up
                    # to 5 times
                    wait = 0.1
                    retries = 0
                    while True:
                        try:
                            repo = backend.student_repo.new(
                                template, semester, student_section, username
                            )
                            logger.debug("Success!")
                            break
                        except HTTPError as e:
                            if retries >= 5 or e.response.status_code != 400:
                                logger.debug("Critical Failure!")
                                raise
                            logger.debug("Failed, retrying...")

                        # Delay and try again
                        time.sleep(wait * 2**retries)
                        retries += 1

                    repo.push(template, branch)
                    for b in branch:
                        repo.protect(b)
                actual_count += 1
                logging.debug("Assigned.")
            elif args.branch:
                logging.info("%s: Already exists.", full_name)
                # If we have an explicit branch, push anyways
                if not dry_run:
                    repo.push(template, branch)
                    for b in branch:
                        repo.protect(b)
                actual_count += 1
                logging.debug("Assigned.")
            else:
                logging.info("%s: Already exists, skipping...", full_name)
            i += 1

            if args.open:
                open_assignment(repo, student, backend.access.developer)

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
    parser.add_argument("--branch", "--branches", nargs="+",
                        help="Branch or branches to push")
    parser.add_argument("--section", nargs="?",
                        help="Section to assign homework to")
    parser.add_argument("--student", metavar="id",
                        help="ID of the student to assign to.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.add_argument("-f", "--force", action="store_true", dest="force",
                        help="Delete and recreate already existing "
                        "student repos.")
    parser.add_argument("-o", "--open", action="store_true", dest="open",
                        help="Open assignment after assigning")
    parser.set_defaults(run=assign)
