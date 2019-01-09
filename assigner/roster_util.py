from assigner.backends.base import RepoError
from assigner.config import DuplicateUserError

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


def add_to_roster(conf, backend, roster, name, username, section, force=False):
    student = {
        "name": name,
        "username": username,
        "section": section
    }

    logger.debug("%s", roster)

    if not force and any(filter(lambda s: s['username'] == username, roster)):
        raise DuplicateUserError("Student already exists in roster!")

    try:
        student["id"] = backend.repo.get_user_id(
            username, conf.backend
        )
    except RepoError:
        logger.warning(
            "Student %s does not have a Gitlab account.", name
        )

    roster.append(student)
