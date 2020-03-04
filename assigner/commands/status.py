import logging
from datetime import datetime

from prettytable import PrettyTable

from assigner import progress
from assigner.backends.base import RepoError
from assigner.backends.decorators import requires_config_and_backend
from assigner.roster_util import get_filtered_roster

help = "Retrieve status of repos"

logger = logging.getLogger(__name__)


@requires_config_and_backend
def status(conf, backend, args):
    """Retrieves and prints the status of repos"""
    hw_name = args.name

    if not hw_name:
        raise ValueError("Missing assignment name.")

    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend

    roster = get_filtered_roster(conf.roster, args.section, args.student)
    sort_key = args.sort

    if sort_key:
        roster.sort(key=lambda s: s[sort_key])

    output = PrettyTable([
        "#", "Sec", "SID", "Name", "Status", "Branches",
        "HEAD", "Last Commit Author", "Last Push Time"])
    output.align["Name"] = "l"
    output.align["Last Commit Author"] = "l"

    for i, student in progress.enumerate(roster):

        name = student["name"]
        username = student["username"]
        student_section = student["section"]
        full_name = backend.student_repo.build_name(semester, student_section,
                                                    hw_name, username)

        row = [i+1, student_section, username, name, "", "", "", "", ""]

        repo = backend.student_repo(backend_conf, namespace, full_name)

        if not repo.already_exists():
            row[4] = "Not Assigned"
            output.add_row(row)
            continue

        if "id" not in student:
            try:
                student["id"] = backend.repo.get_user_id(username, backend_conf)
            except RepoError:
                row[4] = "No Gitlab user"
                output.add_row(row)
                continue

        members = repo.list_members()
        if student["id"] not in [s["id"] for s in members]:
            row[4] = "Not Opened"
            output.add_row(row)
            continue
        if repo.info["archived"]:
            row[4] = 'Archived'
        else:
            level = backend.access(
                [s["access_level"] for s in members if s["id"] == student["id"]][0]
            )
            row[4] = "Open" if level is backend.access.developer else "Locked"

        branches = repo.list_branches()

        if branches:
            row[5] = "\n".join([b["name"] for b in branches])

        head = repo.get_last_HEAD_commit()

        if head:
            row[6] = head["short_id"]
            row[7] = head["author_name"]
            created_at = head["created_at"]
            # Fix UTC offset format in GitLab's datetime: prior to py3.7, UTC offsets could not contain colons
            created_at = created_at[:-7] + created_at[-7:].replace(':', '')
            # Remove odd postfix and add missing 0 to UTC offset
            if created_at.endswith('-0000'):
                created_at = created_at[:-5] + '0'
            row[8] = datetime.strptime(
                created_at, "%Y-%m-%dT%H:%M:%S.%f%z"
            ).astimezone().strftime("%c")

        output.add_row(row)

    print(output)


def setup_parser(parser):
    parser.add_argument("--section", nargs="?",
                        help="Section to get status of")
    parser.add_argument("--student", metavar="id",
                        help="ID of student.")
    parser.add_argument("--sort", nargs="?", default="name",
                        choices=["name", "username"],
                        help="Key to sort users by.")
    parser.add_argument("name", nargs="?",
                        help="Name of the assignment to look up.")
    parser.set_defaults(run=status)
