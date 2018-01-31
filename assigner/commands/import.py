import csv
import logging
import re

from assigner.backends.decorators import requires_config_and_backend
from assigner.config import DuplicateUserError
from assigner.roster_util import add_to_roster

help = "Import users from a csv"

logger = logging.getLogger(__name__)


@requires_config_and_backend
def import_students(conf, backend, args):
    """Imports students from a CSV file to the roster.
    """
    section = args.section

    email_re = re.compile(r"^(?P<user>[^@]+)")
    with open(args.file) as fh:
        reader = csv.reader(fh)

        # Note: This is incredibly hardcoded.
        # However, peoplesoft never updates anything, so we're probably good.
        reader.__next__()  # Skip the header
        count = 0
        for row in reader:
            count += 1
            match = email_re.match(row[4])

            try:
                add_to_roster(
                    conf, backend, conf.roster, row[3], match.group("user"), section, args.force
                )
            except DuplicateUserError:
                logger.warning("User %s is already in the roster, skipping", match.group("user"))

    print("Imported {} students.".format(count))


def setup_parser(parser):
    parser.add_argument("file", help="CSV file to import from")
    parser.add_argument("section", help="Section being imported")
    parser.add_argument("--force", action="store_true", help="Import duplicate students anyway")
    parser.set_defaults(run=import_students)
