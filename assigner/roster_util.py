from assigner.config import DuplicateUserError
from assigner.baserepo import Repo, RepoError

import logging
logger = logging.getLogger(__name__)

def get_filtered_roster(roster, section, target):
    if target:
        roster = [s for s in roster if s["username"] == target]
    elif section:
        roster = [s for s in roster if s["section"] == section]
    if not roster:
        raise ValueError("No matching students found in roster.")
    return roster

def add_to_roster(conf, roster, name, username, section, force=False):
    student = {
        "name": name,
        "username": username,
        "section": section
    }

    logger.debug("{}".format(roster))

    if not force and any([s['username'] == username for s in roster]):
      raise DuplicateUserError("Student already exists in roster!")

    try:
        student["id"] = Repo.get_user_id(
            username, conf.gitlab_host, conf.gitlab_token
        )
    except RepoError:
        logger.warning(
            "Student {} does not have a Gitlab account.".format(name)
        )

    roster.append(student)

