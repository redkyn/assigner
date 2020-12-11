import logging
import argparse
from typing import Any, Dict, List, Optional, Tuple, Set
import re
import os

from requests.exceptions import HTTPError

from redkyn.canvas import CanvasAPI
from redkyn.canvas.exceptions import CourseNotFound, StudentNotFound

from assigner import make_help_parser
from assigner.backends.base import RepoError, RepoBase, BackendBase
from assigner.backends.decorators import requires_config_and_backend
from assigner.roster_util import get_filtered_roster
from assigner import progress
from assigner.config import Config

help = "Retrieves scores from CI artifacts and optionally uploads to Canvas"

logger = logging.getLogger(__name__)


class OptionalCanvas:
    """
    A class that wraps a single CanvasAPI instance and related API
    ID information that both caches the info and queries it only
    when needed
    """

    _api = None
    _section_ids = {}
    _assignment_ids = {}

    @staticmethod
    def lookup_canvas_ids(
        conf: Config, canvas: CanvasAPI, hw_name: str
    ) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Retrieves the list of internal Canvas IDs for a given assignment
        and the relevant sections
        :param hw_name: the name of the homework assignment to search for on Canvas
        :return: "section_ids", a map of section names/identifiers onto
        Canvas internal course IDs and "assignment_ids", a map of section
        names/identifiers onto the Canvas internal assignment IDs for a given assignment
        """
        if "canvas-courses" not in conf or not conf["canvas-courses"]:
            logger.error(
                'canvas-courses configuration is missing! Please use the "assigner canvas import"'
                "command to associate course IDs with section names"
            )
            print("Canvas course listing failed: missing section Canvas course IDs.")
            raise CourseNotFound
        courses = conf["canvas-courses"]
        section_ids = {course["section"]: course["id"] for course in courses}
        min_name = re.search(r"[A-Za-z]+\d+", hw_name).group(0)
        assignment_ids = {}
        for section, course_id in section_ids.items():
            try:
                canvas_assignments = canvas.get_course_assignments(course_id, min_name)
            except CourseNotFound:
                logger.error("Failed to pull assignment list from Canvas")
                raise
            if len(canvas_assignments) != 1:
                logger.warning(
                    "Could not uniquely identify Canvas assignment from name %s and section %s, using first assignment listed",
                    min_name,
                    section,
                )
            assignment_ids[section] = canvas_assignments[0]["id"]
        return (section_ids, assignment_ids)

    @classmethod
    def get_api(cls, conf: Config) -> CanvasAPI:
        if not cls._api:
            if "canvas-token" not in conf:
                logger.error(
                    "canvas-token configuration is missing! Please set the Canvas API access "
                    "token before attempting to use Canvas API functionality"
                )
                print("Canvas course listing failed: missing Canvas API access token.")
                raise KeyError
            cls._api = CanvasAPI(conf["canvas-token"], conf["canvas-host"])

        return cls._api

    @classmethod
    def get_section_ids(cls, conf: Config, hw_name: str) -> Dict[str, Any]:
        if not cls._section_ids:
            cls._section_ids, cls._assignment_ids = cls.lookup_canvas_ids(
                conf, cls.get_api(conf), hw_name
            )
        return cls._section_ids

    @classmethod
    def get_assigment_ids(cls, conf: Config, hw_name: str) -> Dict[str, Any]:
        if not cls._assignment_ids:
            cls._section_ids, cls._assignment_ids = cls.lookup_canvas_ids(
                conf, cls.get_api(conf), hw_name
            )
        return cls._assignment_ids


def get_most_recent_score(repo: RepoBase, result_path: str) -> float:
    """
    Queries the most recent CI job for an artifact containing the score
    :param repo: the repository whose CI jobs should be checked
    :param result_path: the absolute path to the artifact file within the repo
    :return: the score in the artifact file
    """
    try:
        ci_jobs = repo.list_ci_jobs()
        most_recent_job_id = ci_jobs[0]["id"]
        score_file = repo.get_ci_artifact(most_recent_job_id, result_path)
        last_token = score_file.split()[-1]
        score = float(last_token)
        if not 0.0 <= score <= 100.0:
            logger.warning("Unusual score retrieved: %f.", score)
        return score
    except HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(
                "CI artifact does not exist in repo %s.", repo.name_with_namespace,
            )
        raise


def student_search(
    roster: List[Dict[str, Any]], query: str
) -> Optional[Dict[str, Any]]:
    """
    Obtains the student object corresponding to the search query,
    prompting the user for input if disambiguation is necessary (>1 matches)
    :param roster: the part of the config structure containing
    the list of enrolled students
    :param query: the search query, could contain part of SIS username or
    full name
    :return: the roster entry matching the query
    """
    candidate_students = []
    result = None
    # Search through the entire class for a match
    for student in roster:
        if (
            query.lower() in student["name"].lower().replace(",", "")
            or query.lower() in student["username"]
            or query.lower() in " ".join(student["name"].lower().split(",")[::-1])
        ):
            candidate_students.append(student)

    if not candidate_students:
        logger.error("No student found matching query %s", query)
    elif len(candidate_students) == 1:
        result = candidate_students[0]
    else:
        for ct, cand_user in enumerate(candidate_students):
            print("{}: {}, {}".format(ct, cand_user["name"], cand_user["username"]))
        selected = -1
        while selected < 0 or selected >= len(candidate_students):
            selected = int(input("Enter the number of the correct student: "))
        result = candidate_students[selected]
    return result


def verify_commit(auth_emails: List[str], repo: RepoBase, commit_hash: str) -> bool:
    """
    Checks whether a commit has been made by an authorized user
    :param auth_emails: the list of emails authorized to modify the repository
    :param repo: the repository object to check
    :param commit_hash: the full SHA of the commit to check
    :return: whether the committer was authorized (True if authorized, False otherwise)
    """
    email = repo.get_commit_signature_email(commit_hash)
    if not email:
        return False
    return email in auth_emails


def check_repo_integrity(
    repo: RepoBase, files_to_check: Set[str], since: str = ""
) -> None:
    """
    Checks whether any "protected" files in a repository have been modified
    by an unauthorized user and logs any violations
    :param repo: the repository object to check
    :param files_to_check: the absolute paths (within the repo) of protected files
    :param since: the date after which to check, i.e., commits prior to this date are ignored
    """
    auth_emails = repo.list_authorized_emails()
    commits = repo.list_commit_hashes("master", since)
    for commit in commits:
        modified_files = files_to_check.intersection(repo.list_commit_files(commit))
        if modified_files and not verify_commit(auth_emails, repo, commit):
            logger.warning("commit %s modified files: %s", commit, str(modified_files))


def print_statistics(scores: List[float]) -> None:
    """
    Displays aggregate information (summary statistics)
    for a one-dimensional data set
    """
    print("---Assignment Statistics---")
    print("Mean: ", sum(scores) / len(scores))
    print("Number of zeroes:", len([score for score in scores if score < 0.1]))
    print("Number of hundreds:", len([score for score in scores if score > 99.9]))
    print_histogram(scores)


def print_histogram(scores: List[float]) -> None:
    """
    A utility function for printing an ASCII histogram
    for a one-dimensional data set
    """
    print("ASCII Histogram:")
    num_buckets = 10
    range_min = min(scores)
    range_max = max(scores)
    max_col = os.get_terminal_size()[0] - 15
    bucket_width = (range_max - range_min) / num_buckets
    buckets = [(i * bucket_width, (i + 1) * bucket_width) for i in range(num_buckets)]
    counts = {}

    # First count up each bucket
    for bucket in buckets:
        count = len([score for score in scores if bucket[0] <= score < bucket[1]])
        # If it's the last bucket we include the top (i.e. the range max)
        if bucket == buckets[-1]:
            count += scores.count(range_max)
        counts[bucket] = count

    # Then set up the scale factor to maximally utilize the terminal space
    mult_factor = max_col / max(counts.values())

    # Finally, print everything out
    for bucket in buckets:
        proportional_len = int(counts[bucket] * mult_factor)
        print(
            "[{:4}, {:5}{}: {}".format(
                bucket[0],
                bucket[1],
                (")", "]")[bucket == buckets[-1]],
                proportional_len * "=",
            )
        )


def handle_scoring(
    conf: Config,
    backend: BackendBase,
    args: argparse.Namespace,
    student: Dict[str, Any],
) -> Optional[float]:
    """
    Obtains the autograded score from a repository's CI jobs
    :param student: The part of the config structure with info
    on a student's username, ID, and section
    :return: The score obtained from the results file
    """
    hw_name = args.name
    upload = args.upload if "upload" in args else True
    files_to_check = set(args.files)
    backend_conf = conf.backend
    username = student["username"]
    student_section = student["section"]
    full_name = backend.student_repo.build_name(
        conf.semester, student_section, hw_name, username
    )
    try:
        repo = backend.student_repo(backend_conf, conf.namespace, full_name)
        logger.info("Scoring %s...", repo.name_with_namespace)
        if "id" not in student:
            student["id"] = backend.repo.get_user_id(username, backend_conf)
        if not args.noverify:
            unlock_time = repo.get_member_add_date(student["id"])
            check_repo_integrity(repo, files_to_check, unlock_time)
        score = get_most_recent_score(repo, args.path)
        if upload:
            canvas = OptionalCanvas.get_api(conf)
            section_ids = OptionalCanvas.get_section_ids(conf, hw_name)
            assignment_ids = OptionalCanvas.get_assigment_ids(conf, hw_name)
            course_id = section_ids[student_section]
            assignment_id = assignment_ids[student_section]
            try:
                if "canvas-id" not in student:
                    raise StudentNotFound(
                        "No Canvas ID for student.  Remove the student with `assigner roster remove {}`,"
                        " then run 'assigner canvas import {} {}`.".format(
                            username, course_id, student_section
                        )
                    )
                # Append a percent as provided scores are percentages and not number of pts
                canvas.put_assignment_submission(
                    course_id, assignment_id, student["canvas-id"], str(score) + "%",
                )
            except StudentNotFound as e:
                logger.debug(e)
                logger.warning("Unable to update submission for Canvas assignment")

    except RepoError as e:
        logger.debug(e)
        logger.warning("Unable to find repo for %s with URL %s", username, full_name)
        score = None
    return score


@requires_config_and_backend
def score_assignments(
    conf: Config, backend: BackendBase, args: argparse.Namespace
) -> None:
    """Goes through each student repository and grabs the most recent CI
    artifact, which contains their autograded score
    """
    student = args.student

    roster = get_filtered_roster(conf.roster, args.section, student)

    scores = []
    for student in progress.iterate(roster):
        score = handle_scoring(conf, backend, args, student)
        if score is not None:
            scores.append(score)

    print("Scored {} repositories.".format(len(scores)))
    print_statistics(scores)


@requires_config_and_backend
def checkout_students(
    conf: Config, backend: BackendBase, args: argparse.Namespace
) -> None:
    """Interactively prompts for student info and grabs the most recent CI
    artifact, which contains their autograded score
    """
    roster = get_filtered_roster(conf.roster, args.section, None)

    while True:
        query = input("Enter student ID or name, or 'q' to quit: ")
        if "quit".startswith(query):
            break
        student = student_search(roster, query)
        if not student:
            continue

        score = handle_scoring(conf, backend, args, student)
        logger.info("Uploaded score of %d", (score))


@requires_config_and_backend
def integrity_check(
    conf: Config, backend: BackendBase, args: argparse.Namespace
) -> None:
    """Checks that none of the grading files were modified in the timeframe
    during which students could push to their repository
    """
    student = args.student
    files_to_check = set(args.files)
    roster = get_filtered_roster(conf.roster, args.section, None)

    for student in progress.iterate(roster):
        username = student["username"]
        student_section = student["section"]
        full_name = backend.student_repo.build_name(
            conf.semester, student_section, args.name, username
        )

        try:
            repo = backend.student_repo(conf.backend, conf.namespace, full_name)
            check_repo_integrity(repo, files_to_check)
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

    all_parser.add_argument("--student", nargs=1, help="ID of student to score")
    all_parser.add_argument(
        "--upload", action="store_true", help="Upload grades to Canvas"
    )

    all_parser.set_defaults(run=score_assignments)

    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Interactively checkout individual students and upload their grades to Canvas",
    )
    interactive_parser.set_defaults(run=checkout_students)

    integrity_parser = subparsers.add_parser(
        "integrity",
        help="Check the integrity of desired files for a set of assignment respositories",
    )
    integrity_parser.add_argument("--student", nargs=1, help="ID of student to score")
    integrity_parser.set_defaults(run=integrity_check)

    # Flags common to all subcommands
    for subcmd_parser in [all_parser, interactive_parser, integrity_parser]:
        subcmd_parser.add_argument("name", help="Name of the assignment to check")
        subcmd_parser.add_argument("--section", nargs=1, help="Section to check")
        subcmd_parser.add_argument(
            "-f",
            "--files",
            nargs="+",
            dest="files",
            default=[".gitlab-ci.yml"],
            help="Files to check for modification",
        )

    # Flags common to the scoring subcommands
    for subcmd_parser in [all_parser, interactive_parser]:
        subcmd_parser.add_argument(
            "--noverify",
            action="store_true",
            help="Don't check whether a student has overwritten the grader files",
        )
        subcmd_parser.add_argument(
            "--path",
            default="results.txt",
            help="Path within repo to grader results file",
        )

    make_help_parser(parser, subparsers, "Show help for score or one of its commands")
