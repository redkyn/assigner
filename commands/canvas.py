import logging

from baserepo import Repo, RepoError
from canvas import CanvasAPI
from config import config_context

from prettytable import PrettyTable

help = "Get Canvas course information"

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

    canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])

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

    canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])

    courses = canvas.get_instructor_courses()

    if not courses:
        print("No courses found where current user is a teacher.")
        return

    output = PrettyTable(["#", "ID", "Name"])
    output.align["Name"] = "l"

    for ix, c in enumerate(courses):
        output.add_row((ix+1, c['id'], c['name']))

    print(output)

def setup_parser(parser):
    subparsers = parser.add_subparsers(title='Canvas commands')

    list_parser = subparsers.add_parser('list', help='List Canvas courses where you are a teacher, TA, or grader')
    list_parser.set_defaults(run=print_canvas_courses)

    import_parser = subparsers.add_parser('import', help='Import the roster from a specific Canvas course')
    import_parser.add_argument("id", help="Canvas ID for course to import from")
    import_parser.add_argument("section", help="Section being imported")
    import_parser.set_defaults(run=import_from_canvas)

    help_parser = subparsers.add_parser("help",
                                        help="Show this help screen and exit")
    help_parser.set_defaults(run=lambda x: parser.print_help())
