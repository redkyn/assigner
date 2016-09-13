#!/usr/bin/env python3
import argparse
import logging
import os
import re
import csv
import tempfile

from requests.exceptions import HTTPError
from colorlog import ColoredFormatter

from canvas import CanvasAPI
from config import config_context
from baserepo import Access, RepoError, Repo, BaseRepo, StudentRepo

logger = logging.getLogger(__name__)
description = "An automated tool for assigning programming homework."


@config_context
def new(conf, args):
    """Creates a new base repository for an assignment so that you can add the
    instructions, sample code, etc.
    """
    hw_name = args.name
    dry_run = args.dry_run
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token

    if dry_run:
        url = Repo.build_url(host, namespace, hw_name)
        print("Created repo at {}.".format(url))
    else:
        try:
            repo = BaseRepo.new(hw_name, namespace, host, token)
            print("Created repo at {}.".format(repo.url))
        except HTTPError as e:
            if e.response.status_code == 400:
                logger.warning("Repository {} already exists!".format(hw_name))
            else:
                raise


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

    roster = get_selected_roster(args)

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
                actual_count += 1
                logging.debug("Assigned.")
            elif force:
                logging.info("{}: Already exists.".format(full_name))
                logging.info("{}: Deleting...".format(full_name))
                if not dry_run:
                    repo.delete()
                    repo = StudentRepo.new(base, semester, student_section,
                                           username, token)
                    repo.push(base, branch)
                actual_count += 1
                logging.debug("Assigned.")
            elif branch:
                logging.info("{}: Already exists.".format(full_name))
                # If we have an explicit branch, push anyways
                repo.push(base, branch) if not dry_run else None
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


@config_context
def open_assignment(conf, args):
    """Adds each student in the roster to their respective homework
    repositories as Developers so they can pull/commit/push their work.
    """
    hw_name = args.name
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token
    semester = conf.semester

    roster = get_selected_roster(args)

    count = 0
    for student in roster:
        username = student["username"]
        student_section = student["section"]
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            if "id" not in student:
                student["id"] = Repo.get_user_id(username, host, token)

            repo.add_member(student["id"], Access.developer)
            count += 1
        except RepoError:
            logging.warn("Could not add {} to {}.".format(username, full_name))
        except HTTPError:
            raise

    print("Granted access to {} repositories.".format(count))


@config_context
def get(conf, args):
    """Creates a folder for the assignment in the CWD (or <path>, if specified)
    and clones each students' repository into subfolders.
    """
    hw_name = args.name
    hw_path = args.path
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token
    semester = conf.semester

    roster = get_selected_roster(args)

    path = os.path.join(hw_path, hw_name)
    os.makedirs(path, mode=0o700, exist_ok=True)

    count = 0
    for student in roster:
        username = student["username"]
        student_section = student["section"]
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            repo.clone_to(os.path.join(path, username))
            count += 1
        except RepoError as e:
            logging.warn(str(e))
        except HTTPError as e:
            if e.response.status_code == 404:
                logging.warn("Repository {} does not exist.".format(full_name))
            else:
                raise

    print("Cloned {} repositories.".format(count))


def lock(args):
    """Sets each student to Reporter status on their homework repository so
    they cannot push changes, etc.
    """
    return manage_users(args, Access.reporter)


def unlock(args):
    """Sets each student to Developer status on their homework repository.
    """
    return manage_users(args, Access.developer)


def archive(args):
    """Archive each student repository so it won't show up in the project list.
    """
    return manage_repos(args, 'archive')


def unarchive(args):
    """Unarchive each student repository so it will show back up in the project list.
    """
    return manage_repos(args, 'unarchive')


@config_context
def manage_users(conf, args, level):
    """Creates a folder for the assignment in the CWD (or <path>, if specified)
    and clones each students' repository into subfolders.
    """
    hw_name = args.name
    dry_run = args.dry_run

    if dry_run:
        raise NotImplementedError("'--dry-run' is not implemented")

    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token
    semester = conf.semester

    roster = get_selected_roster(args)

    count = 0
    for student in roster:
        username = student["username"]
        student_section = student["section"]
        if "id" not in student:
            logging.warning(
                "Student {} does not have a gitlab account.".format(username)
            )
            continue
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            repo.edit_member(student["id"], level)
            count += 1
        except HTTPError:
            raise

    print("Changed {} repositories.".format(count))


def status(args):
    raise NotImplementedError("'status' command is not available")


@config_context
def import_students(conf, args):
    """Imports students from a CSV file to the roster.
    """
    section = args.section

    # TODO: This should probably move to another file
    email_re = re.compile(r"^(?P<user>[^@]+)")
    with open(args.file) as fh:
        reader = csv.reader(fh)

        if "roster" not in conf:
            conf["roster"] = []

        # Note: This is incredibly hardcoded.
        # However, peoplesoft never updates anything, so we're probably good.
        reader.__next__()  # Skip the header
        count = 0
        for row in reader:
            count += 1
            match = email_re.match(row[4])
            conf.roster.append({
                "name": row[3],
                "username": match.group("user"),
                "section": section
            })

            try:
                conf.roster[-1]["id"] = Repo.get_user_id(
                    match.group("user"), conf.gitlab_host, conf.token
                )
            except RepoError:
                logger.warning(
                    "Student {} does not have a Gitlab account.".format(row[3])
                )

    print("Imported {} students.".format(count))


@config_context
def import_from_canvas(conf, args):
    """Imports students from a Canvas course to the roster.
    """
    if 'canvas-token' not in conf:
        logging.error("canvas-token configuration is missing! Please set the Canvas API access "
                      "token before attempting to import users from Canvas")
        print("Import from canvas failed: missing Canvas API access token.")
        return

    if "roster" not in conf:
        conf["roster"] = []

    course_id = args.id
    section = args.section

    canvas = CanvasAPI(conf["canvas-token"])

    students = canvas.get_course_students(course_id)

    for s in students:
        conf.roster.append({
            "name": s['sortable_name'],
            "username": s['sis_user_id'],
            "section": section
        })

        try:
            conf.roster[-1]["id"] = Repo.get_user_id(
                s['sis_user_id'], conf.gitlab_host, conf.token
            )
        except RepoError:
            logger.warning(
                "Student {} does not have a Gitlab account.".format(s['name'])
            )

    print("Imported {} students.".format(len(students)))


@config_context
def print_canvas_courses(conf, args):
    """Show a list of current teacher's courses from Canvas via the API.
    """
    if 'canvas-token' not in conf:
        logging.error("canvas-token configuration is missing! Please set the Canvas API access "
                      "token before attempting to use Canvas API functionality")
        print("Canvas course listing failed: missing Canvas API access token.")
        return

    canvas = CanvasAPI(conf["canvas-token"])

    courses = canvas.get_teacher_courses()

    if not courses:
        print("No courses found where current user is a teacher.")
        return

    print('-'*92)
    print("| # | %-6s | %-75s |" % ('ID', 'Course Title'))
    print('-'*92)
    for ix, c in enumerate(courses):
        print("| %s | %-6s | %-75s |" % (ix+1, c['id'], c['name']))
    print('-'*92)


@config_context
def manage_repos(conf, args, action):
    """Performs an action (archive|unarchive) on all student repos
    """
    hw_name = args.name
    dry_run = args.dry_run

    if dry_run:
        raise NotImplementedError("'--dry-run' is not implemented")
    if action not in ['archive', 'unarchive']:
        raise ValueError("Unexpected action '{}', accepted actions are 'archive' and 'unarchive'.".format(action))

    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token
    semester = conf.semester

    roster = get_selected_roster(args)

    count = 0
    for student in roster:
        username = student["username"]
        student_section = student["section"]
        if "id" not in student:
            logging.warning(
                "Student {} does not have a gitlab account.".format(username)
            )
            continue
        full_name = StudentRepo.name(semester, student_section,
                                     hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            if action == 'archive':
                repo.archive()
            else:
                repo.unarchive()
            count += 1
        except HTTPError:
            raise

    print("Changed {} repositories.".format(count))


@config_context
def get_selected_roster(conf, args):
    section = args.section
    target = args.student  # used if assigning to a single student
    if target:
        roster = [s for s in conf.roster if s["username"] == target]
    elif section:
        roster = [s for s in conf.roster if s["section"] == section]
    else:
        roster = conf.roster
    if not roster:
        raise ValueError("No matching students found in roster.")
    return roster


@config_context
def set_conf(conf, args):
    """Sets <key> to <value> in the config.
    """
    conf[args.key] = args.value


def configure_logging():
    root_logger = logging.getLogger()
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    # Create a colorized formatter
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%"
    )

    # Add the formatter to the console handler, and the console
    # handler to the root logger.
    console.setFormatter(formatter)
    root_logger.addHandler(console)


def make_parser():
    """Construct and return a CLI argument parser.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", default="_config.yml",
                        help="Path a config file")
    parser.add_argument("--tracebacks", action="store_true",
                        help="Show full tracebacks")
    parser.add_argument("--verbosity", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Desired log level")

    # If no arguments are provided, show the usage screen
    parser.set_defaults(run=lambda x: parser.print_usage())

    # Set up subcommands for each package
    subparsers = parser.add_subparsers(title="subcommands")

    # "new" command
    subparser = subparsers.add_parser("new",
                                      help="Create a new base repo")
    subparser.add_argument("name",
                           help="Name of the assignment.")
    subparser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    subparser.set_defaults(run=new)

    # "assign" command
    subparser = subparsers.add_parser("assign",
                                      help="Assign a base repo to students")
    subparser.add_argument("name",
                           help="Name of the assignment to assign.")
    subparser.add_argument("--branch", nargs="?",
                           help="Branch to push")
    subparser.add_argument("--section", nargs="?",
                           help="Section to assign homework to")
    subparser.add_argument("--student", metavar="id",
                           help="ID of the student to assign to.")
    subparser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    subparser.add_argument("-f", "--force", action="store_true", dest="force",
                           help="Delete and recreate already existing " +
                                "student repos.")
    subparser.set_defaults(run=assign)

    # "open" command
    subparser = subparsers.add_parser("open", help="Grant students access " +
                                                   "to their repos")
    subparser.add_argument("name", help="Name of the assignment to grant " +
                                        "access to")
    subparser.add_argument("--section", nargs="?",
                           help="Section to grant access to")
    subparser.add_argument("--student", metavar="id",
                           help="ID of the student to assign to.")
    subparser.set_defaults(run=open_assignment)

    # "get" command
    subparser = subparsers.add_parser("get",
                                      help="Clone student repos")
    subparser.add_argument("name",
                           help="Name of the assignment to retrieve.")
    subparser.add_argument("path", default=".", nargs="?",
                           help="Path to clone student repositories to")
    subparser.add_argument("--section", nargs="?",
                           help="Section to retrieve")
    subparser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment needs " +
                                "retrieving.")
    subparser.set_defaults(run=get)

    # "lock" command
    subparser = subparsers.add_parser("lock",
                                      help="Lock students out of repos")
    subparser.add_argument("name",
                           help="Name of the assignment to lock.")
    subparser.add_argument("--section", nargs="?",
                           help="Section to lock")
    subparser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment needs " +
                                "locking.")
    subparser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    subparser.set_defaults(run=lock)

    # "unlock" command
    subparser = subparsers.add_parser("unlock",
                                      help="unlock students from repos")
    subparser.add_argument("name",
                           help="Name of the assignment to unlock.")
    subparser.add_argument("--section", nargs="?",
                           help="Section to unlock")
    subparser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment needs " +
                                "unlocking.")
    subparser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    subparser.set_defaults(run=unlock)

    # "archive" command
    subparser = subparsers.add_parser("archive",
                                      help="Archive students repos")
    subparser.add_argument("name",
                           help="Name of the assignment to archive.")
    subparser.add_argument("--section", nargs="?",
                           help="Section to archive")
    subparser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment to archive.")
    subparser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    subparser.set_defaults(run=archive)

    # "unarchive" command
    subparser = subparsers.add_parser("unarchive",
                                      help="Unarchive students repos")
    subparser.add_argument("name",
                           help="Name of the assignment to unarchive.")
    subparser.add_argument("--section", nargs="?",
                           help="Section to unarchive")
    subparser.add_argument("--student", metavar="id",
                           help="ID of student whose assignment to unarchive.")
    subparser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    subparser.set_defaults(run=unarchive)

    # "status" command
    subparser = subparsers.add_parser("status",
                                      help="Retrieve status of repos")
    subparser.add_argument("--section", nargs="?",
                           help="Section to get status of")
    subparser.add_argument("--student", metavar="id",
                           help="ID of student.")
    subparser.add_argument("name", nargs="?",
                           help="Name of the assignment to look up.")
    subparser.set_defaults(run=status)

    # "import" command
    subparser = subparsers.add_parser("import",
                                      help="Import students from a csv")
    subparser.add_argument("file", help="CSV file to import from")
    subparser.add_argument("section", help="Section being imported")
    subparser.set_defaults(run=import_students)

    # "canvas_import" command
    subparser = subparsers.add_parser("canvas_import",
                                      help="Import students from Canvas via the API")
    subparser.add_argument("id", help="Canvas ID for course to import from")
    subparser.add_argument("section", help="Section being imported")
    subparser.set_defaults(run=import_from_canvas)

    # "list_courses" command
    subparser = subparsers.add_parser("list_courses",
                                      help="Show a list of current teacher's courses from Canvas via the API")
    subparser.set_defaults(run=print_canvas_courses)

    # "set" command
    subparser = subparsers.add_parser("config",
                                      help="Set configuration values")
    subparser.add_argument("key", help="Key to set")
    subparser.add_argument("value", help="Value to set")
    subparser.set_defaults(run=set_conf)

    # The "help" command shows the help screen
    help_parser = subparsers.add_parser("help",
                                        help="Show this help screen and exit")
    help_parser.set_defaults(run=lambda x: parser.print_help())

    return parser


def main():
    """Entry point
    """
    # Configure logging
    configure_logging()

    # Parse CLI args
    parser = make_parser()
    args = parser.parse_args()

    # Set logging verbosity
    logging.getLogger().setLevel(args.verbosity)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # Do it
    try:
        args.run(args)
    except Exception as e:
        if args.tracebacks:
            raise e
        if isinstance(e, KeyError):
            logger.error(str(e) + " is missing")
        else:
            logger.error(str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
