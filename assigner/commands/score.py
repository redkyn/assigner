import logging
import argparse
from typing import Any, Dict, List, Optional, Tuple, Callable

from requests.exceptions import HTTPError

from redkyn.canvas import CanvasAPI
from redkyn.canvas.exceptions import CourseNotFound, AssignmentNotFound
from redkyn.canvas.utils import lookup_canvas_ids

from assigner import make_help_parser
from assigner.backends.base import RepoError, RepoBase, BackendBase
from assigner.backends.decorators import requires_config_and_backend
from assigner.roster_util import get_filtered_roster
from assigner import progress
from assigner.config import Config

help = "Retrieves scores from CI artifacts and optionally uploads to Canvas"

logger = logging.getLogger(__name__)


def requires_config_and_backend_and_canvas(
    func: Callable[[Config, BackendBase, argparse.Namespace, CanvasAPI], None]
) -> Callable[[Config, BackendBase, argparse.Namespace], None]:
    """Provides a Canvas API instance depending on configuration."""

    @requires_config_and_backend
    def wrapper(
        config: Config,
        backend: BackendBase,
        cmdargs: argparse.Namespace,
        *args: Any,
        **kwargs: Any
    ) -> None:

        canvas = CanvasAPI(config["canvas-token"], config["canvas-host"])

        return func(config, backend, cmdargs, canvas, *args, **kwargs)

    return wrapper


def get_most_recent_score(
    repo: RepoBase, student: Dict[str, Any], result_path: str
) -> float:
    try:
        logger.info("Scoring %s...", repo.name_with_namespace)
        ci_jobs = repo.list_ci_jobs()
        most_recent_job_id = ci_jobs[0]["id"]
        score_file = repo.get_ci_artifact(most_recent_job_id, result_path)
        if type(score_file) is str:
            score = score_file.split()[-1]
        else:
            score = str(score_file)
    except HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(
                "CI artifact does not exist for %s in repo %s.",
                student["username"],
                repo.name_with_namespace,
            )
        raise
    return float(score)


def get_unlock_time(conf: Config, canvas: CanvasAPI, hw_name: str) -> str:
    section_ids, assignment_ids = lookup_canvas_ids(
        conf["canvas-courses"], canvas, hw_name
    )
    unlock_times: List[str] = []
    for section, s_id in section_ids.items():
        assignment = canvas.get_assignment(s_id, assignment_ids[section])
        unlock_time = assignment["unlock_at"]
        unlock_times.append(unlock_time)
    return max(unlock_times)


def student_search(
    roster: List[Dict[str, Any]], query: str
) -> Optional[Dict[str, Any]]:
    candidate_students = []
    # Search through the entire class for a match
    for student in roster:
        if (
            query.lower() in student["name"].lower().replace(",", "")
            or query.lower() in student["username"]
        ):
            candidate_students.append(student)

    if not candidate_students:
        logger.error("No student found matching query %s", query)
        return None
    elif len(candidate_students) == 1:
        return candidate_students[0]
    else:
        ct = 0
        for cand_user in candidate_students:
            print("{}: {}, {}".format(ct, cand_user["name"], cand_user["username"]))
            ct += 1
        selected = -1
        while selected < 0 or selected >= len(candidate_students):
            selected = int(input("Enter the number of the correct student: "))
        return candidate_students[selected]


def handle_scoring(
    conf: Config,
    backend: BackendBase,
    args: argparse.Namespace,
    student: Dict[str, Any],
    canvas: CanvasAPI,
    section_ids: Dict[str, Any],
    assignment_ids: Dict[str, Any],
    upload: bool = True,
) -> Optional[float]:
    hw_name = args.name
    result_path = args.path
    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend
    username = student["username"]
    student_section = student["section"]
    full_name = backend.student_repo.build_name(
        semester, student_section, hw_name, username
    )
    try:
        repo = backend.student_repo(backend_conf, namespace, full_name)
        if "id" not in student:
            student["id"] = backend.repo.get_user_id(username, backend_conf)
        score = get_most_recent_score(repo, student, result_path)
        if upload:
            course_id = section_ids[student_section]
            assignment_id = assignment_ids[student_section]
            try:
                student_id = canvas.get_student_from_username(course_id, username)["id"]
            except Exception as e:
                logger.debug(e)
                logger.error("Unable to lookup Canvas account ID")
            try:
                canvas.put_assignment_submission(
                    course_id, assignment_id, student_id, str(score) + "%"
                )
            except Exception as e:
                print(e)
                logger.debug(e)
                logger.warning("Unable to update submission for Canvas assignment")
    except RepoError as e:
        logger.debug(e)
        logger.warning("Unable to find repo for %s with URL %s", username, full_name)
    return score


@requires_config_and_backend_and_canvas
def score_assignments(
    conf: Config, backend: BackendBase, args: argparse.Namespace, canvas: CanvasAPI
) -> None:
    """Goes through each student repository and grabs the most recent CI
    artifact, which contains their autograded score
    """
    hw_name = args.name
    section = args.section
    student = args.student
    upload = args.upload

    roster = get_filtered_roster(conf.roster, section, student)
    # canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])
    try:
        section_ids, assignment_ids = lookup_canvas_ids(
            conf["canvas-courses"], canvas, hw_name
        )
    except:
        logger.error("Failed to lookup Canvas assignment")
        return
    count = 0
    scores = []
    for student in progress.iterate(roster):
        score = handle_scoring(
            conf, backend, args, student, canvas, section_ids, assignment_ids, upload
        )
        if score is not None:
            scores.append(score)

    print("Scored {} repositories.".format(count))
    print(scores)


@requires_config_and_backend_and_canvas
def checkout_students(
    conf: Config, backend: BackendBase, args: argparse.Namespace, canvas: CanvasAPI
) -> None:
    """Interactively prompts for student info and grabs the most recent CI
    artifact, which contains their autograded score
    """
    hw_name = args.name

    roster = get_filtered_roster(conf.roster, args.section, None)

    # canvas = CanvasAPI(conf["canvas-token"], conf["canvas-host"])
    try:
        section_ids, assignment_ids = lookup_canvas_ids(
            conf["canvas-courses"], canvas, hw_name
        )
    except:
        logger.error("Failed to lookup Canvas assignment")
        return

    while True:
        query = input("Enter student ID or name, or 'q' to quit: ")
        if query in "quit":
            break
        student = student_search(roster, query)
        if not student:
            continue

        score = handle_scoring(
            conf, backend, args, student, canvas, section_ids, assignment_ids
        )


@requires_config_and_backend_and_canvas
def integrity_check(
    conf: Config, backend: BackendBase, args: argparse.Namespace, canvas: CanvasAPI
) -> None:
    """Checks that none of the grading files were modified in the timeframe
    during which students could push to their repository
    """
    hw_name = args.name
    student = args.student
    files_to_check = args.files
    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend
    roster = get_filtered_roster(conf.roster, args.section, None)

    lock_time = get_unlock_time(conf, canvas, hw_name)

    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = backend.student_repo.build_name(
            semester, student_section, hw_name, username
        )

        try:
            repo = backend.student_repo(backend_conf, namespace, full_name)
            commits = repo.list_commits("master", {"since": lock_time})
            # Do some git stuff wit the commits
            # logger.warning("student %s modified a file", student['username'])
            for commit in commits:
                for file in repo.list_commit_files(commit["id"]):
                    if file in files_to_check:
                        logger.warning(
                            "student %s modified a file: %s", student["username"], file
                        )
        except RepoError as e:
            logger.debug(e)
            logger.warning(
                "Unable to find repo for %s with URL %s", username, full_name
            )


def setup_parser(parser: argparse.ArgumentParser):
    subparsers = parser.add_subparsers(title="Scoring commands")

    all_parser = subparsers.add_parser(
        "all",
        help="Get scores (using CI artifacts) for all students for a given assignment",
    )
    # all_parser.set_defaults(run=score_assignments)

    all_parser.add_argument("name", help="Name of the assignment to score")
    all_parser.add_argument("--section", nargs=1, help="Section to score")
    all_parser.add_argument("--student", nargs=1, help="ID of student to score")
    all_parser.add_argument(
        "--upload", action="store_true", help="Upload grades to Canvas"
    )
    all_parser.add_argument(
        "--path", default="results.txt", help="Path within repo to grader results file"
    )
    all_parser.set_defaults(run=score_assignments)

    checkout_parser = subparsers.add_parser(
        "checkout",
        help="Interactively checkout individual students and upload their grades to Canvas",
    )
    checkout_parser.add_argument("name", help="Name of the assignment to score")
    checkout_parser.add_argument("--section", nargs="?", help="Section to score")
    checkout_parser.add_argument(
        "--path", default="results.txt", help="Path within repo to grader results file"
    )
    checkout_parser.set_defaults(run=checkout_students)

    integrity_parser = subparsers.add_parser(
        "integrity",
        help="Check the integrity of desired files for a set of assignment respositories",
    )
    integrity_parser.add_argument("name", help="Name of the assignment to check")
    integrity_parser.add_argument("--section", nargs=1, help="Section to check")
    integrity_parser.add_argument("--student", nargs=1, help="ID of student to score")
    integrity_parser.add_argument(
        "-f",
        "--files",
        nargs="+",
        dest="files",
        default=[],
        help="Files to check for modification",
    )
    integrity_parser.set_defaults(run=integrity_check)

    make_help_parser(parser, subparsers, "Show help for score or one of its commands")
