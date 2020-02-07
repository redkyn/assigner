import logging

from requests.exceptions import HTTPError

from redkyn.canvas import CanvasAPI
from redkyn.canvas.exceptions import CourseNotFound, AssignmentNotFound

from assigner.backends.base import RepoError
from assigner.backends.decorators import requires_config_and_backend
from assigner.config import requires_config
from assigner.roster_util import get_filtered_roster
from assigner import progress

help = "Retrieves scores from CI artifacts and optionally uploads to Canvas"

logger = logging.getLogger(__name__)

def parse_assignment_name(name: str) -> str:
    """Removes the tail of a string starting with the
    character immediately following the first integer
    sequence - i.e. reduces "hw1-first-assignment" into
    "hw1"
    """
    idx = 0
    while idx < len(name) and not name[idx].isdigit():
        idx += 1
    while idx < len(name) and name[idx].isdigit():
        idx += 1
    return name[:idx]

def get_most_recent_score(repo, student) -> str:
    try:
        logger.info("Scoring %s...", repo.name)
        ci_jobs = repo.list_ci_jobs()
        most_recent_job_id = ci_jobs[0]["id"]
        score_file = repo.get_ci_artifact(most_recent_job_id, "grader/results.txt")
        if type(score_file) is str:
            score = score_file.split()[-1]
        else:
            score = str(score_file)
        return score
    except HTTPError as e:
        if e.response.status_code == 404:
            logger.warning("CI artifact does not exist for %s in repo %s.", student["username"], repo.name)
        else:
            raise

def lookup_canvas_ids(conf, canvas, hw_name):
    if 'canvas-courses' not in conf:
        logger.error(
            "canvas-course configuration is missing! Please set the "
            "Canvas course ID token before attempting to upload scores "
            "to Canvas"
        )
        print("Import from canvas failed: missing Canvas course ID.")
        raise CourseNotFound
    courses = conf["canvas-courses"]
    section_ids = {course["section"]: course["id"] for course in courses}
    min_name = parse_assignment_name(hw_name)
    assignment_ids = {}
    for section, course_id in section_ids.items():
        try:
            canvas_assignments = canvas.get_course_assignments(course_id, min_name)
        except:
            logger.error("Failed to pull assignment list from Canvas")
            raise AssignmentNotFound
        if len(canvas_assignments) != 1:
            logger.error("Could not uniquely identify Canvas assignment from name %s and section %s", min_name, section)
            raise AssignmentNotFound
        assignment_ids[section] = canvas_assignments[0]["id"]
    return (section_ids, assignment_ids)

@requires_config_and_backend
def score_assignments(conf, backend, args):
    """Goes through each student repository and grabs the most recent CI
    artifact, which contains their autograded score
    """
    hw_name = args.name
    do_upload = args.upload
    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend

    roster = get_filtered_roster(conf.roster, args.section, args.student)

    if do_upload:
        canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])
        try:
            section_ids, assignment_ids = lookup_canvas_ids(conf, canvas, hw_name)
        except:
            logging.error("Failed to lookup Canvas assignment IDs")
            return
    count = 0
    scores = []
    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = backend.student_repo.build_name(semester, student_section,
                                                    hw_name, username)

        try:
            repo = backend.student_repo(backend_conf, namespace, full_name)
            if "id" not in student:
                student["id"] = backend.repo.get_user_id(username, backend_conf)
            score = get_most_recent_score(repo, student)
            if score:
                scores.append(float(score))
            count += 1
            if do_upload:
                course_id = section_ids[student_section]
                assignment_id = assignment_ids[student_section]
                try:
                    student_id = canvas.get_student_from_username(course_id, username)["id"]
                except Exception as e:
                    logger.debug(e)
                    logger.warning("Unable to lookup Canvas account ID")
                    continue
                try:
                    canvas.put_assignment_submission(course_id, assignment_id, student_id, score + "%")
                except Exception as e:
                    print(e)
                    logger.debug(e)
                    logger.warning("Unable to update submission for Canvas assignment")
        except RepoError as e :
            logger.debug(e)
            logger.warning("Unable to find repo for %s with URL %s", username, full_name)

    print("Scored {} repositories.".format(count))
    print(scores)


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment to score")
    parser.add_argument("--section", nargs="?",
                        help="Section to score")
    parser.add_argument("--student", metavar="id",
                        help="ID of student to score")
    parser.add_argument("--all", action="store_true",
                        help="Check out all students")
    parser.add_argument("--upload", action="store_true",
                        help="Upload grades to Canvas")
    parser.set_defaults(run=score_assignments)
