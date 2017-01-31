import logging

from prettytable import PrettyTable

from canvas import CanvasAPI
from config import config_context

help = "Show a list of current teacher's courses from Canvas via the API"

logger = logging.getLogger(__name__)

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
    parser.set_defaults(run=print_canvas_courses)
