#!/usr/bin/env python3
import argparse
import importlib
import logging
from collections import OrderedDict

from colorlog import ColoredFormatter
from requests.exceptions import HTTPError

from baserepo import StudentRepo
from config import config_context

logger = logging.getLogger(__name__)

description = "An automated tool for assigning programming homework."

subcommands = OrderedDict([
    ("new", "commands.new"),
    ("assign", "commands.assign"),
    ("open", "commands.open"),
    ("get", "commands.get"),
    ("lock", "commands.lock"),
    ("unlock", "commands.unlock"),
    ("archive", "commands.archive"),
    ("unarchive", "commands.unarchive"),
    ("status", "commands.status"),
    ("import", "commands.import"),
    ("canvas", "commands.canvas"),
    ("set", "commands.set"),
])


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

    roster = get_filtered_roster(conf.roster, args.section, args.student)

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

    roster = get_filtered_roster(conf.roster, args.section, args.student)

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


def get_filtered_roster(roster, section, target):
    if target:
        roster = [s for s in roster if s["username"] == target]
    elif section:
        roster = [s for s in roster if s["section"] == section]
    if not roster:
        raise ValueError("No matching students found in roster.")
    return roster




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

    for name, path in subcommands.items():
        module = importlib.import_module(path)
        subparser = subparsers.add_parser(name, help=module.help)
        module.setup_parser(subparser)

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
