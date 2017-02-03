import csv
import logging
import re

from config import config_context
from baserepo import Repo, RepoError

help="Import users from a csv"

logger = logging.getLogger(__name__)


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

def setup_parser(parser):
    parser.add_argument("file", help="CSV file to import from")
    parser.add_argument("section", help="Section being imported")
    parser.set_defaults(run=import_students)
