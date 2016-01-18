import argparse
import importlib
import logging
import os
import re
import csv
import tempfile

from requests.exceptions import HTTPError
from collections import OrderedDict
from colorlog import ColoredFormatter

from config import config

from baserepo import Access, RepoError, Repo, BaseRepo, StudentRepo


logger = logging.getLogger(__name__)

description = "An automated grading tool for programming assignments."


def new(args):
    with config(args.config) as conf:
        if args.dry_run:
            url = Repo.build_url(conf['gitlab-host'], conf['namespace'], args.name)
            print("Created repo at ", url)
        else:
            try:
                repo = BaseRepo.new(args.name, conf['namespace'], conf['gitlab-host'],
                    conf['token'])
                print("Created repo at ", repo.url)
            except HTTPError as e:
                if e.response.status_code == 400:
                    logger.warning("Repository %s already exists!", args.name)
                else:
                    raise


def assign(args):
    if args.dry_run:
        raise NotImplementedError("'--dry-run' is not implemented")
    if args.student:
        raise NotImplementedError("'--student' is not implemented")

    with config(args.config) as conf, tempfile.TemporaryDirectory() as tmpdirname:
        base = BaseRepo(conf['gitlab-host'], conf['namespace'], args.name, conf['token'])
        base.clone_to(tmpdirname)

        count = 0
        for student in conf['roster']:
            try:
                name = StudentRepo.name(
                            conf['semester'],
                            student['section'],
                            args.name,
                            student['username']
                        )

                repo = StudentRepo(conf['gitlab-host'], conf['namespace'], name, conf['token'])
                repo.info

                logging.warning("Student repository %s already exists.", repo.name)

                if args.force:
                    logging.warning("Deleting...")
                    repo.delete()
                    repo = StudentRepo.new(base, conf['semester'], student['section'], student['username'], conf['token'])
                    repo.push(base)
                    count += 1
                else:
                    logging.warning("Skipping...")

            except HTTPError as e:
                if e.response.status_code == 404:
                    repo = StudentRepo.new(base, conf['semester'], student['section'], student['username'], conf['token'])
                    repo.push(base)
                    count += 1
                else:
                    raise

    print("Assigned homework ", args.name, " to ", count, " students")

def open_assignment(args):
    with config(args.config) as conf:
        count = 0
        for student in conf['roster']:
            name = StudentRepo.name(
                        conf['semester'],
                        student['section'],
                        args.name,
                        student['username']
                    )

            try:
                repo = StudentRepo(conf['gitlab-host'], conf['namespace'], name, conf['token'])
                if 'id' not in student:
                    student['id'] = Repo.get_user_id(student['username'], conf['gitlab-host'], conf['token'])

                repo.add_member(student['id'], Access.developer)
                count += 1
            except RepoError:
                logging.warn("Could not add %s to %s", student['username'], name)
            except HTTPError as e:
                raise
                if e.response.status_code == 404:
                    logging.warn("Repository %s does not exist.", name)
                else:
                    raise

    print("Granted access to ", count, " repositories")


def get(args):
    if args.student:
        raise NotImplementedError("'--student' is not implemented")

    with config(args.config) as conf:
        path = os.path.join(args.path, args.name)
        os.makedirs(path, mode=0o700, exist_ok=True)

        count = 0
        for student in conf['roster']:
            name = StudentRepo.name(
                        conf['semester'],
                        student['section'],
                        args.name,
                        student['username']
                    )

            try:
                repo = StudentRepo(conf['gitlab-host'], conf['namespace'], name, conf['token'])
                repo.clone_to(os.path.join(path, student['username']))
                count += 1
            except HTTPError as e:
                if e.response.status_code == 404:
                    logging.warn("Repository %s does not exist.", name)
                else:
                    raise

    print("Cloned ", count, " repositories")


def lock(args):
    return manage_users(args, Access.reporter)


def unlock(args):
    return manage_users(args, Access.developer)


def manage_users(args, level):
    if args.dry_run:
        raise NotImplementedError("'--dry-run' is not implemented")
    if args.student:
        raise NotImplementedError("'--student' is not implemented")

    with config(args.config) as conf:
        count = 0
        for student in conf['roster']:
            name = StudentRepo.name(
                        conf['semester'],
                        student['section'],
                        args.name,
                        student['username']
                    )

            if 'id' in student:
                try:
                    repo = StudentRepo(conf['gitlab-host'], conf['namespace'], name, conf['token'])
                    repo.edit_member(student['id'], level)
                    count += 1
                except HTTPError as e:
                    raise
                    if e.response.status_code == 404:
                        logging.warning("Repository %s does not exist.", name)
                    else:
                        raise
            else:
                logging.warning("Student %s does not have a gitlab account.", student['username'])

    print("Changed ", count, " repositories.")


def status(args):
    raise NotImplementedError("'status' command is not available")


def import_students(args):
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
                'section': args.section
            })

            try:
                conf['roster'][-1]['id'] = Repo.get_user_id(match.group("user"), conf['gitlab-host'], conf['token'])
            except RepoError:
                logger.warning("Student %s does not have a Gitlab account.", row[3])

    print("Imported ", count, " students.")


def set_conf(args):
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
    subparser.set_defaults(run=open_assignment)

    # 'get' command
    subparser = subparsers.add_parser("get",
                                      help="Clone student repos")
    subparser.add_argument('name',
                           help='Name of the assignment to retrieve.')
    subparser.add_argument('path', default=".", nargs='?',
            help='Path to clone student repositories to')
    subparser.add_argument('--student', metavar="id",
                           help='ID of student whose assignment needs retrieving.')
    subparser.set_defaults(run=get)

    # 'lock' command
    subparser = subparsers.add_parser("lock",
                                      help="Lock students out of repos")
    subparser.add_argument('name',
                           help='Name of the assignment to lock.')
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
    subparser.add_argument('--student', metavar="id",
                           help='ID of student whose assignment needs unlocking.')
    subparser.add_argument('--dry-run', action='store_true',
                           help="Don't actually do it.")
    subparser.set_defaults(run=unlock)

    # 'status' command
    subparser = subparsers.add_parser("status",
                                      help="Retrieve status of repos")
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
