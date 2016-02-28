#!/usr/bin/env python3
import argparse
import logging
import os
import re
import csv
import tempfile
import sys
import traceback

from requests.exceptions import HTTPError
from colorlog import ColoredFormatter

from config import config

from baserepo import Access, RepoError, Repo, BaseRepo, StudentRepo


logger = logging.getLogger(__name__)

description = "An automated grading tool for programming assignments."


def new(args):
    """Creates a new base repository for an assignment so that you can add the
    instructions, sample code, etc.
    """
    hw_name = args.name
    dry_run = args.dry_run

    with config(args.config) as conf:
        host = conf['gitlab-host']
        namespace = conf['namespace']
        token = conf['token']

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


def assign(args):
    """Creates homework repositories for an assignment for each student
    in the roster.
    """
    hw_name = args.name
    branch = args.branch
    section = args.section
    dry_run = args.dry_run
    force = args.force
    target = args.student  # used if assigning to a single student

    if target:
        raise NotImplementedError("'--student' is not implemented")

    with config(args.config) as conf, tempfile.TemporaryDirectory() as tmpdirname:
        host = conf['gitlab-host']
        namespace = conf['namespace']
        token = conf['token']
        semester = conf['semester']
        if section:
            roster = [s for s in conf['roster'] if s['section'] == section]
        else:
            roster = conf['roster']

        base = BaseRepo(host, namespace, hw_name, token)
        if not dry_run:
            base.clone_to(tmpdirname, branch)

        count = 0
        s_count = len(roster)
        logging.info("Assigning {} to {} student{} in {}.".format(
            hw_name, s_count,
            "s" if s_count != 1 else "",
            "section " + section if section else "any section")
        )
        for student in roster:
            username = student['username']
            s_section = student['section']
            full_name = StudentRepo.name(semester, s_section, hw_name, username)
            repo = StudentRepo(host, namespace, full_name, token)

            logging.warning("Student repository {} already exists.".format(repo.name))
            try:
                if force:
                    logging.warning("Deleting...")
                    if not dry_run:
                        repo.delete()
                        repo = StudentRepo.new(base, semester, s_section, username, token)
                        repo.push(base, args.branch)
                    count += 1
                else:
                    # If we have an explicit branch, push anyways
                    if branch:
                        if not dry_run:
                            repo.push(base, args.branch)
                        count += 1
                    else:
                        logging.warning("Skipping...")

            except HTTPError as e:
                if e.response.status_code == 404:
                    if not dry_run:
                        repo = StudentRepo.new(base, semester, s_section, username, token)
                        repo.push(base, branch)
                    count += 1
                else:
                    raise

    print("Assigned homework {} to {} students.".format(hw_name, count))


def open_assignment(args):
    """Adds each student in the roster to their respective homework
    repositories as Developers so they can pull/commit/push their work.
    """
    hw_name = args.name
    section = args.section

    with config(args.config) as conf:
        host = conf['gitlab-host']
        namespace = conf['namespace']
        token = conf['token']
        roster = conf['roster']
        semester = conf['semester']

        count = 0
        for student in roster:
            username = student['username']
            s_section = student['section']

            if section and s_section != section:
                continue

            full_name = StudentRepo.name(semester, s_section, hw_name, username)

            try:
                repo = StudentRepo(host, namespace, full_name, token)
                if 'id' not in student:
                    student['id'] = Repo.get_user_id(username, host, token)

                repo.add_member(student['id'], Access.developer)
                count += 1
            except RepoError:
                logging.warn("Could not add {} to {}.".format(username, full_name))
            except HTTPError as e:
                raise
                if e.response.status_code == 404:
                    logging.warn("Repository {} does not exist.".format(full_name))
                else:
                    raise

    print("Granted access to {} repositories.".format(count))


def get(args):
    """Creates a folder for the assignment in the CWD (or <path>, if specified)
    and clones each students' repository into subfolders.
    """
    hw_name = args.name
    hw_path = args.path
    section = args.section
    target = args.student  # used if assigning to a single student

    if target:
        raise NotImplementedError("'--student' is not implemented")

    with config(args.config) as conf:
        host = conf['gitlab-host']
        namespace = conf['namespace']
        token = conf['token']
        roster = conf['roster']
        semester = conf['semester']
        path = os.path.join(hw_path, hw_name)
        os.makedirs(path, mode=0o700, exist_ok=True)

        count = 0
        for student in roster:
            username = student['username']
            s_section = student['section']

            if section and s_section != section:
                continue

            full_name = StudentRepo.name(semester, s_section, args.name, username)

            try:
                repo = StudentRepo(host, namespace, full_name, token)
                repo.clone_to(os.path.join(path, username))
                count += 1
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


def manage_users(args, level):
    """Creates a folder for the assignment in the CWD (or <path>, if specified)
    and clones each students' repository into subfolders.
    """
    hw_name = args.name
    dry_run = args.dry_run
    section = args.section
    target = args.student  # used if assigning to a single student

    if dry_run:
        raise NotImplementedError("'--dry-run' is not implemented")
    if target:
        raise NotImplementedError("'--student' is not implemented")

    with config(args.config) as conf:
        host = conf['gitlab-host']
        namespace = conf['namespace']
        token = conf['token']
        roster = conf['roster']
        semester = conf['semester']

        count = 0
        for student in roster:
            username = student['username']
            s_section = student['section']

            if section and s_section != section:
                continue
            if 'id' not in student:
                logging.warning("Student {} does not have a gitlab account.".format(username))
                continue

            full_name = StudentRepo.name(semester, s_section, hw_name, username)
            try:
                repo = StudentRepo(host, namespace, full_name, token)
                repo.edit_member(student['id'], level)
                count += 1
            except HTTPError as e:
                raise
                if e.response.status_code == 404:
                    logging.warning("Repository {} does not exist.".format(full_name))
                else:
                    raise

    print("Changed {} repositories.".format(count))


def status(args):
    raise NotImplementedError("'status' command is not available")


def import_students(args):
    """Imports students from a CSV file to the roster.
    """
    section = args.section

    # TODO: This should probably move to another file
    email_re = re.compile(r'^(?P<user>[^@]+)')
    with open(args.file) as fh, config(args.config) as conf:
        reader = csv.reader(fh)

        if 'roster' not in conf:
            conf['roster'] = []

        # Note: This is incredibly hardcoded.
        # However, peoplesoft never updates anything, so we're probably good.
        reader.__next__()  # Skip the header
        count = 0
        for row in reader:
            count += 1
            match = email_re.match(row[4])
            conf['roster'].append({
                'name': row[3],
                'username': match.group("user"),
                'section': section
            })

            try:
                conf['roster'][-1]['id'] = Repo.get_user_id(match.group("user"), conf['gitlab-host'], conf['token'])
            except RepoError:
                logger.warning("Student {} does not have a Gitlab account.".format(row[3]))

    print("Imported {} students.".format(count))


def set_conf(args):
    """Sets <key> to <value> in the config.
    """
    with config(args.config) as conf:
        conf[args.key] = args.value


def configure_logging():
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create console handler. It'll write everything that's DEBUG or
    # better. However, it's only going to write what the logger passes
    # to it.
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    # Create a colorized formatter
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # Add the formatter to the console handler, and the console
    # handler to the root logger.
    console.setFormatter(formatter)
    root_logger.addHandler(console)


def make_parser():
    """Construct and return a CLI argument parser.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--config', default="_config.yml",
                        help='Path a config file')
    parser.add_argument('--tracebacks', action='store_true',
                        help='Show full tracebacks')
    parser.add_argument('--verbosity', default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help='Desired log level')

    # If no arguments are provided, show the usage screen
    parser.set_defaults(run=lambda x: parser.print_usage())

    # Set up subcommands for each package
    subparsers = parser.add_subparsers(title="subcommands")

    # 'new' command
    subparser = subparsers.add_parser("new",
                                      help="Create a new base repo")
    subparser.add_argument('name',
                           help='Name of the assignment.')
    subparser.add_argument('--dry-run', action='store_true',
                           help="Don't actually do it.")
    subparser.set_defaults(run=new)

    # 'assign' command
    subparser = subparsers.add_parser("assign",
                                      help="Assign a base repo to students")
    subparser.add_argument('name',
                           help='Name of the assignment to assign.')
    subparser.add_argument('--branch', nargs='?',
                           help='Branch to push')
    subparser.add_argument('--section', nargs='?',
                           help='Section to assign homework to')
    subparser.add_argument('--student', metavar="id",
                           help='ID of the student to assign to.')
    subparser.add_argument('--dry-run', action='store_true',
                           help="Don't actually do it.")
    subparser.add_argument('-f, --force', action='store_true', dest='force',
                           help="Delete and recreate already existing student repos.")
    subparser.set_defaults(run=assign)

    # 'open' command
    subparser = subparsers.add_parser("open", help="Grant students access to their repos")
    subparser.add_argument('name', help='Name of the assignment to grant access to')
    subparser.add_argument('--section', nargs='?',
                           help='Section to grant access to')
    subparser.set_defaults(run=open_assignment)

    # 'get' command
    subparser = subparsers.add_parser("get",
                                      help="Clone student repos")
    subparser.add_argument('name',
                           help='Name of the assignment to retrieve.')
    subparser.add_argument('path', default=".", nargs='?',
                           help='Path to clone student repositories to')
    subparser.add_argument('--section', nargs='?',
                           help='Section to retrieve')
    subparser.add_argument('--student', metavar="id",
                           help='ID of student whose assignment needs retrieving.')
    subparser.set_defaults(run=get)

    # 'lock' command
    subparser = subparsers.add_parser("lock",
                                      help="Lock students out of repos")
    subparser.add_argument('name',
                           help='Name of the assignment to lock.')
    subparser.add_argument('--section', nargs='?',
                           help='Section to lock')
    subparser.add_argument('--student', metavar="id",
                           help='ID of student whose assignment needs locking.')
    subparser.add_argument('--dry-run', action='store_true',
                           help="Don't actually do it.")
    subparser.set_defaults(run=lock)

    # 'unlock' command
    subparser = subparsers.add_parser("unlock",
                                      help="unlock students from repos")
    subparser.add_argument('name',
                           help='Name of the assignment to unlock.')
    subparser.add_argument('--section', nargs='?',
                           help='Section to unlock')
    subparser.add_argument('--student', metavar="id",
                           help='ID of student whose assignment needs unlocking.')
    subparser.add_argument('--dry-run', action='store_true',
                           help="Don't actually do it.")
    subparser.set_defaults(run=unlock)

    # 'status' command
    subparser = subparsers.add_parser("status",
                                      help="Retrieve status of repos")
    subparser.add_argument('--section', nargs='?',
                           help='Section to get status of')
    subparser.add_argument('--student', metavar="id",
                           help='ID of student.')
    subparser.add_argument('name', nargs='?',
                           help='Name of the assignment to look up.')
    subparser.set_defaults(run=status)

    # 'import' command
    subparser = subparsers.add_parser("import",
                                      help="Import students from a csv")
    subparser.add_argument('file', help='CSV file to import from')
    subparser.add_argument('section', help='Section being imported')
    subparser.set_defaults(run=import_students)

    # 'set' command
    subparser = subparsers.add_parser("config",
                                      help="Set configuration values")
    subparser.add_argument("key", help="Key to set")
    subparser.add_argument("value", help="Value to set")
    subparser.set_defaults(run=set_conf)

    # The 'help' command shows the help screen
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

    # Do it
    try:
        args.run(args)
    except Exception as e:
        if args.tracebacks:
            raise e
        logger.error(str(e))
        raise SystemExit(1) from e


if __name__ == '__main__':
    main()
