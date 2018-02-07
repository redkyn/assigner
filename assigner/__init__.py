#!/usr/bin/env python3
import argparse
import importlib
import logging
import sys

from colorlog import ColoredFormatter
from requests.exceptions import HTTPError
from git.cmd import GitCommandNotFound

from assigner.baserepo import StudentRepo
from assigner.config import config_context
from assigner.roster_util import get_filtered_roster
from assigner.progress import Progress

from pkg_resources import get_distribution, DistributionNotFound


try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "Not installed"

logger = logging.getLogger(__name__)

description = "An automated tool for assigning programming homework."

subcommands = [
    "new",
    "assign",
    "open",
    "get",
    "lock",
    "unlock",
    "archive",
    "unarchive",
    "protect",
    "unprotect",
    "status",
    "import",
    "canvas",
    "set",
    "roster",
    "init",
]


@config_context
def manage_repos(conf, args, action):
    """Performs an action (lambda) on all student repos
    """
    hw_name = args.name
    dry_run = args.dry_run

    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.gitlab_token
    semester = conf.semester

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    count = 0
    progress = Progress()
    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        if "id" not in student:
            logging.warning(
                "Student %s does not have a gitlab account.", username
            )
            continue
        full_name = StudentRepo.build_name(semester, student_section,
                                           hw_name, username)

        try:
            repo = StudentRepo(host, namespace, full_name, token)
            if not dry_run:
                action(repo, student)
            count += 1
        except HTTPError:
            raise

    progress.finish()

    print("Changed {} repositories.".format(count))


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


def make_help_parser(parser, subparsers, help_text):
    def show_help(args):
        new_args = list(args.command)
        new_args.append("--help")
        parser.parse_args(new_args)

    help_parser = subparsers.add_parser("help", help=help_text)
    help_parser.add_argument("command", nargs="*",
                             help="Command to get help with")
    help_parser.set_defaults(run=show_help)


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
    parser.add_argument("--version", action="store_true",
                        help="Show version and exit")

    def default_run(args):
        if args.version:
            print("Assigner version {}".format(__version__))
        else:
            parser.print_usage()

    # If no arguments are provided, show the usage screen
    parser.set_defaults(run=default_run)

    # Set up subcommands for each package
    subparsers = parser.add_subparsers(title="commands")

    for name in subcommands:
        module = importlib.import_module("assigner.commands." + name)
        subparser = subparsers.add_parser(name, help=module.help)
        module.setup_parser(subparser)

    make_help_parser(parser, subparsers, "Show help for Assigner or one of its commands")

    return parser


#pylint: disable=dangerous-default-value
def main(args=sys.argv[1:]):
    """Entry point
    """
    # Configure logging
    configure_logging()

    # Parse CLI args
    parser = make_parser()
    args = parser.parse_args(args)

    # Set logging verbosity
    logging.getLogger().setLevel(args.verbosity)
    logging.getLogger("requests").setLevel(logging.WARNING)

    logging.debug("This is Assigner version %s", __version__)

    # Do it
    try:
        args.run(args)
    except Exception as e:
        if args.tracebacks:
            raise e
        if isinstance(e, KeyError):
            logger.error("%s is missing", e)
        elif isinstance(e, GitCommandNotFound):
            logger.error("git is not installed!")
        else:
            logger.error(str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
