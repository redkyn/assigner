import logging

from prettytable import PrettyTable

from redkyn.canvas import CanvasAPI
from redkyn.canvas.exceptions import AuthenticationFailed, CourseNotFound

from assigner import make_help_parser
from assigner.backends.decorators import requires_config_and_backend
from assigner.config import requires_config, DuplicateUserError
from assigner.roster_util import add_to_roster

help = "Get Canvas course information"

logger = logging.getLogger(__name__)


def add_to_courses(courses, course_id: int, section: str) -> None:
    course_obj = {
        "section": section,
        "id": course_id,
    }

    if any(filter(lambda c: c['id'] == course_id, courses)):
        logger.warning("Course %s already exists, not modifying", course_id)
    else:
        courses.append(course_obj)

@requires_config_and_backend
def import_from_canvas(conf, backend, args):
    """Imports students from a Canvas course to the roster.
    """
    if 'canvas-token' not in conf:
        logger.error(
            "canvas-token configuration is missing! Please set the Canvas API access "
            "token before attempting to import users from Canvas"
        )
        print("Import from canvas failed: missing Canvas API access token.")
        return

    course_id = args.id
    section = args.section
    force = args.force

    canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])

    try:
        students = canvas.get_course_students(course_id)
        if "canvas-courses" not in conf:
            conf["canvas-courses"] = []
        add_to_courses(conf["canvas-courses"], int(course_id), section)

    except AuthenticationFailed as e:
        logger.debug(e)
        logger.error("Canvas authentication failed. Is your token missing or expired?")
        return
    except CourseNotFound as e:
        logger.debug(e)
        logger.error("Course ID %s not found. Make sure to use the ID, not the row number.", course_id)
        return

    for s in students:
        if 'sis_user_id' not in s or not s['sis_user_id']:
            logger.error("Could not get username for %s", s['sortable_name'])

        try:
            add_to_roster(
                conf, backend, conf.roster, s['sortable_name'], s['sis_user_id'], section, force, s['id']
            )
        except DuplicateUserError:
            logger.warning("User %s is already in the roster, skipping", s['sis_user_id'])

    print("Imported {} students.".format(len(students)))


@requires_config
def print_canvas_courses(conf, _):
    """Show a list of current teacher's courses from Canvas via the API.
    """
    if 'canvas-token' not in conf:
        logger.error("canvas-token configuration is missing! Please set the Canvas API access "
                     "token before attempting to use Canvas API functionality")
        print("Canvas course listing failed: missing Canvas API access token.")
        return

    canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])

    try:
        courses = canvas.get_instructor_courses()
    except AuthenticationFailed as e:
        logger.debug(e)
        logger.error("Canvas authentication failed. Is your token missing or expired?")
        return

    if not courses:
        print("No courses found where current user is a teacher.")
        return

    output = PrettyTable(["#", "ID", "Name"])
    output.align["Name"] = "l"

    for ix, c in enumerate(sorted(courses, key=lambda c: c['id'], reverse=True)):
        output.add_row((ix+1, c['id'], c['name']))

    print(output)


def setup_parser(parser):
    subparsers = parser.add_subparsers(title='Canvas commands')

    list_parser = subparsers.add_parser(
        "list", help="List published Canvas courses where you are a teacher, TA, or grader"
    )
    list_parser.set_defaults(run=print_canvas_courses)

    import_parser = subparsers.add_parser(
        "import", help="Import the roster from a specific Canvas course"
    )
    import_parser.add_argument("id", help="Canvas ID for course to import from")
    import_parser.add_argument("section", help="Section being imported")
    import_parser.add_argument(
        "--force", action="store_true", help="Import duplicate students anyway"
    )
    import_parser.set_defaults(run=import_from_canvas)

    make_help_parser(
        parser, subparsers, "Show help for roster or one of its commands"
    )
