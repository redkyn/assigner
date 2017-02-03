import logging

from baserepo import Repo, RepoError
from canvas import CanvasAPI
from config import config_context

help = "Import students from Canvas via the API"

logger = logging.getLogger(__name__)


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


def setup_parser(parser):
    parser.add_argument("id", help="Canvas ID for course to import from")
    parser.add_argument("section", help="Section being imported")
    parser.set_defaults(run=import_from_canvas)
