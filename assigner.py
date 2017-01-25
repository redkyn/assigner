#!/usr/bin/env python3
import time
import argparse
import logging
import os
import re
import csv

from datetime import datetime

from requests.exceptions import HTTPError
from colorlog import ColoredFormatter
from prettytable import PrettyTable
from progressbar import ProgressBar

import commands
from canvas import CanvasAPI
from config import config_context
from baserepo import Access, RepoError, Repo, BaseRepo, StudentRepo

logger = logging.getLogger(__name__)

description = "An automated tool for assigning programming homework."

subcommands = OrderedDict([
    ("new", "assigner.commands.new"),
    ("assign", "assigner.commands.assign"),
    ("open", "assigner.commands.open"),
    ("get", "assigner.commands.get"),
    ("lock", "assigner.commands.lock"),
    ("unlock", "assigner.commands.unlock"),
    ("archive", "assigner.commands.archive"),
    ("unarchive", "assigner.commands.unarchive"),
    ("status", "assigner.commands.status"),
    ("import", "assigner.commands.import"),
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

    output = PrettyTable(["#", "ID", "Name"])
    output.align["Name"] = "l"

    for ix, c in enumerate(courses):
        output.add_row((ix+1, c['id'], c['name']))

    print(output)

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

    for name, path in subcommands.items():
        module = importlib.import_module(path)
        subparser = subparsers.add_parser(name, help=module.help)
        module.setup_parser(subparser)

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
