import logging

from requests.exceptions import HTTPError

from assigner.backends.base import RepoError
from assigner.backends.decorators import requires_config_and_backend
from assigner.backends.exceptions import UserInAssignerGroup
from assigner.roster_util import get_filtered_roster
from assigner import progress

help = "Retrieves scores from CI artifacts and optionally uploads to Canvas"

logger = logging.getLogger(__name__)


def get_most_recent_score(repo, student):
    try:
        logging.info("Scoring %s...", repo.name)
        ci_jobs = repo.list_ci_jobs()
        most_recent_job_id = ci_jobs[0]["id"]
        score_file = repo.get_ci_artifact(most_recent_job_id, "grader/results.txt")
        if type(score_file) is str:
            score = score_file.split()[-1]
        else:
            score = score_file
        return score
    except HTTPError as e:
        if e.response.status_code == 404:
            logging.warning("CI artifact does not exist for %s in repo %s.", student["username"], repo.name)
        else:
            raise


@requires_config_and_backend
def score_assignments(conf, backend, args):
    """Goes through each student repository and grabs the most recent CI
    artifact, which contains their autograded score
    """
    hw_name = args.name
    namespace = conf.namespace
    semester = conf.semester
    backend_conf = conf.backend

    roster = get_filtered_roster(conf.roster, args.section, args.student)

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
                scores.append(score)
            count += 1
        except RepoError as e :
            logging.warning(e)

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
