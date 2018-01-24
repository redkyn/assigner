#pylint: disable=dangerous-default-value
from unittest.mock import MagicMock
import logging
import os
import re

from enum import Enum
from requests.exceptions import HTTPError
from urllib.parse import urlsplit, urlunsplit, urljoin, quote

from assigner.backends.base import (
    BackendBase,
    RepoBase,
    RepoError,
    StudentRepoBase,
    TemplateRepoBase
)


class Visibility(Enum):
    """Mock API values for repo visibility"""
    private = 0
    internal = 10
    public = 20


class Access(Enum):
    guest = 10
    reporter = 20
    developer = 30
    master = 40
    owner = 50


class MockRepo(RepoBase):
    """Mock repo; manages API requests and various metadata"""

    PATH_RE = re.compile(
        r"^/(?P<namespace>[\w\-\.]+)/(?P<name>[\w\-\.]+)\.git$"
    )

    @classmethod
    def build_url(cls, url_base, namespace, name):
        """ Build a url for a repository """
        return url_base + "/" + namespace + "/" + name + ".git"

    @classmethod
    def from_url(cls, url, token):
        parts = urlsplit(url)
        if not parts.scheme:
            raise RepoError("{} is missing a scheme.".format(url))
        if not parts.netloc:
            raise RepoError("{} is missing a domain.".format(url))

        if parts.scheme != "https":
            logging.warning("Using scheme %s instead of https.", parts.scheme)

        return cls("https://basemock.com/api4/", "namespace", "name", "token")

    def __init__(self, url_base, namespace, name, token, url=None):
        self.url_base = url_base
        self.namespace = namespace
        self.name = name
        self.token = token

        if url is None:
            self.url = MockRepo.build_url(url_base, namespace, name)
        else:
            self.url = url

    @property
    def name_with_namespace(self):
        return "{}/{}".format(self.namespace, self.name)

    @property
    def namespace_id(self):
        if not self.already_exists():
            raise RepoError("Repo {} does not exist on Mock".format(self.name))

        return self.info["namespace"]["id"]

    @property
    def id(self):
        if not self.already_exists():
            raise RepoError("Repo {} does not exist on Mock".format(self.name))

        return self.info["id"]

    @property
    def info(self):
        if not hasattr(self, "_info"):
            quoted = quote(self.name_with_namespace, safe="")
            url = "/projects/{}".format(quoted)
            try:
                self._info = MagicMock()
            except HTTPError as e:
                if e.response.status_code == 404:
                    logging.debug("Could not find repo with url %s/api/v4%s.",
                                  self.url_base, url)
                    self._info = None
                else:
                    raise
        return self._info

    @property
    def repo(self):
        if hasattr(self, "_repo"):
            return self._repo
        logging.debug("Repo not cloned yet!")
        return None

    @property
    def ssh_url(self):
        if not self.already_exists():
            raise RepoError("Repo {} does not exist on Mock".format(self.name))

        return self.info["ssh_url_to_repo"]

    def already_exists(self):
        if self.info:
            return True
        return False

    def get_head(self, branch):
        if self.repo is None:
            raise RepoError("No repo to get head from")

        for head in self.repo.heads:
            if head.name == branch:
                return head

        return self.repo.create_head(branch, "origin/{}".format(branch))

    def checkout(self, branch):
        return self.get_head(branch).checkout()

    def pull(self, branch):
        if self.repo is None:
            raise RepoError("No repo to pull to")

    def clone_to(self, dir_name, branch=None):
        logging.debug("Cloning %s...", self.ssh_url)
        if branch:
            self._repo = MagicMock().Repo.clone_from(self.ssh_url, dir_name,
                                                        branch=branch)
            for b in branch:
                self._repo.create_head(b, "origin/{}".format(b))

            logging.debug(self._repo.heads)
        else:
            self._repo = MagicMock().Repo.clone_from(self.ssh_url, dir_name)

        logging.debug("Cloned %s.", self.name)
        return self._repo

    def add_local_copy(self, dir_name):
        if self.repo is not None:
            logging.warning("You already have a local copy associated with this repo")
            return

        logging.debug("Using %s for the local repo...", dir_name)
        self._repo = MagicMock().Repo(dir_name)

    def delete(self):
        logging.debug("Deleted %s.", self.name)

    @classmethod
    def get_user_id(cls, username, url_base, token):
        data = MagicMock()

        if not data:
            logging.warning(
                "Did not find any users matching %s.", username
            )
            raise RepoError("No user {}.".format(username))

        for result in data:
            if result["username"] == username:
                logging.info(
                    "Got id %s for user %s.", data[0]["id"], username
                )
                return result["id"]

        # Fall back to first result if all else fails
        logging.warning("Got %s users for %s.", len(data), username)
        logging.warning("Failed to find an exact match for %s.", username)
        logging.info(
            "Got id %s for user %s.", data[0]["id"], data[0]["username"]
        )
        return data[0]["id"]

    def list_members(self):
        return [MagicMock(), MagicMock(), MagicMock()]

    def get_member(self, user_id):
        return MagicMock()

    def add_member(self, user_id, level):
        return MagicMock()

    def edit_member(self, user_id, level):
        return MagicMock()

    def delete_member(self, user_id):
        return MagicMock()

    def list_commits(self, ref_name="master"):
        return MagicMock()

    def list_pushes(self):
        return MagicMock()

    def get_last_HEAD_commit(self, ref="master"):
        return MagicMock()

    def list_branches(self):
        return MagicMock()

    def get_branch(self, branch):
        return "branch"

    def archive(self):
        return MagicMock()

    def unarchive(self):
        return MagicMock()

    # NOTE: these are not the same defaults that Mock uses
    def protect(self, branch="master", developer_push=True, developer_merge=True):
        return MagicMock()

    def unprotect(self, branch="master"):
        return MagicMock()


class MockTemplateRepo(MockRepo, TemplateRepoBase):

    @classmethod
    def new(cls, name, namespace, url_base, token):
        return MockRepo()

    def push_to(self, student_repo, branch="master"):
        logging.debug("Pushed %s to %s.", self.name, student_repo.name)


class MockStudentRepo(MockRepo, StudentRepoBase):
    """Repository for a student's solution to a homework assignment"""

    @classmethod
    def new(cls, base_repo, semester, section, username, token):
        """Create a new repository on GitLab"""
        return cls.from_url("http://mockhub.com/", "token")

    @classmethod
    def build_name(cls, semester, section, assignment, user):
        fmt = {
            "semester": semester,
            "section": section,
            "assignment": assignment,
            # Replace .s with -s
            "user": user.translate(str.maketrans(".", "-"))
        }

        return "{semester}-{section}-{assignment}-{user}".format(**fmt)

    def push(self, base_repo, branch="master"):
        """Push base_repo code to this repo"""
        base_repo.push_to(self, branch)


#pylint: disable=too-few-public-methods
class MockBackend(BackendBase):
    """
    Common abstract base backend for all assigner backends (gitlab or mock).
    """
    repo: RepoBase = MockRepo
    template_repo: TemplateRepoBase = MockTemplateRepo
    student_repo: StudentRepoBase = MockStudentRepo
