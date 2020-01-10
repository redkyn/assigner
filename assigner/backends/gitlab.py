#pylint: disable=dangerous-default-value
import git
import json
import logging
import os
import re
import requests
from time import sleep

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

from assigner.backends.gitlab_exceptions import (
    raiseUserInAssignerGroup,
    raiseUserNotAssigned,
)

from assigner.backends.git_exceptions import (
    raiseRetryableGitError,
)
from assigner.backends.exceptions import RetryableGitError

# Transparently use a common TLS session for each request
requests = requests.Session()


class Visibility(Enum):
    """Gitlab API values for repo visibility"""
    private = 0
    internal = 10
    public = 20


class Access(Enum):
    guest = 10
    reporter = 20
    developer = 30
    master = 40
    owner = 50


class GitlabRepo(RepoBase):
    """Gitlab repo; manages API requests and various metadata"""

    PATH_RE = re.compile(
        r"^/(?P<namespace>[\w\-\.]+)/(?P<name>[\w\-\.]+)\.git$"
    )

    @classmethod
    def build_url(cls, config, namespace, name):
        """ Build a url for a repository """
        return config["host"] + "/" + namespace + "/" + name + ".git"

    @classmethod
    def from_url(cls, url, token):
        parts = urlsplit(url)
        if not parts.scheme:
            raise RepoError("{} is missing a scheme.".format(url))
        if not parts.netloc:
            raise RepoError("{} is missing a domain.".format(url))

        if parts.scheme != "https":
            logging.warning("Using scheme %s instead of https.", parts.scheme)

        match = cls.PATH_RE.match(parts.path)
        if not match:
            raise RepoError(
                "Bad path. Can't separate namespace " +
                "from repo name {}.".format(parts.path)
            )

        namespace = match.group("namespace")
        name = match.group("name")

        config = {
            "host": urlunsplit((parts.scheme, parts.netloc, "", "", "")),
            "token": token,
            "name": "gitlab",
        }

        self = cls(config, namespace, name, url)

        logging.debug(json.dumps(self.info))
        logging.debug("%s is valid.", self.name_with_namespace)

        return self

    @classmethod
    def _cls_gl_get(cls, config, path, params={}):
        """Make a Gitlab GET request"""
        headers = {"Private-Token": config["token"]}
        url = urljoin(config["host"], "/api/v4" + path)
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

    @classmethod
    def _cls_gl_post(cls, config, path, payload={}, params={}):
        """Make a Gitlab POST request"""
        headers = {"Private-Token": config["token"]}
        url = urljoin(config["host"], "/api/v4" + path)
        r = requests.post(url, params=params, data=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    @classmethod
    def _cls_gl_put(cls, config, path, payload={}, params={}):
        """Make a Gitlab PUT request"""
        headers = {"Private-Token": config["token"]}
        url = urljoin(config["host"], "/api/v4" + path)
        r = requests.put(url, params=params, data=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    @classmethod
    def _cls_gl_delete(cls, config, path, params={}):
        """Make a Gitlab DELETE request"""
        headers = {"Private-Token": config["token"]}
        url = urljoin(config["host"], "/api/v4" + path)
        r = requests.delete(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

    #pylint: disable=super-init-not-called
    def __init__(self, config, namespace, name, url=None):
        self.config = config
        self.namespace = namespace
        self.name = name

        if url is None:
            self.url = GitlabRepo.build_url(self.config, namespace, name)
        else:
            self.url = url

    @property
    def name_with_namespace(self):
        return "{}/{}".format(self.namespace, self.name)

    @property
    def namespace_id(self):
        if not self.already_exists():
            raise RepoError("Repo {} does not exist on Gitlab".format(self.name))

        return self.info["namespace"]["id"]

    @property
    def id(self):
        if not self.already_exists():
            raise RepoError("Repo {} does not exist on Gitlab".format(self.name))

        return self.info["id"]

    @property
    def info(self):
        if not hasattr(self, "_info"):
            quoted = quote(self.name_with_namespace, safe="")
            url = "/projects/{}".format(quoted)
            try:
                self._info = self._gl_get(url)
            except HTTPError as e:
                if e.response.status_code == 404:
                    logging.debug("Could not find repo with url %s/api/v4%s.",
                                  self.config["host"], url)
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
            raise RepoError("Repo {} does not exist on Gitlab".format(self.name))

        return self.info["ssh_url_to_repo"]

    def already_exists(self):
        if self.info:
            return True
        return False

    def get_index(self):
        if self.repo is None:
            raise RepoError("No repo to get index from")

        return self.repo.index

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

        self.repo.remote().pull(branch)

    def clone_to(self, dir_name, branch, attempts=1):
        logging.debug("Cloning %s...", self.ssh_url)
        for attempt in range(0, attempts):
            if attempts > 1:
                logging.debug("Attempt %d of %d...", attempt + 1, attempts)

            try: # for exp. backoff
                try:
                    if branch:
                        self._repo = git.Repo.clone_from(self.ssh_url, dir_name)
                        for b in branch:
                            self._repo.create_head(b, "origin/{}".format(b))

                        logging.debug(self._repo.heads)
                    else:
                        self._repo = git.Repo.clone_from(self.ssh_url, dir_name)
                    logging.debug("Cloned %s.", self.name)
                #pylint: disable=no-member
                except git.exc.GitCommandError as e:
                    # GitPython may delete this directory
                    # and the caller may have opinions about that,
                    # so go ahead and re-create it just to be safe.
                    os.makedirs(dir_name, exist_ok=True)
                    raiseRetryableGitError(e)
                    raise RepoError(e)

                # if we got this far, we succeeded!
                break

            except RetryableGitError as e:
                if attempt == (attempts - 1):
                    raise
                else:
                    logging.debug(e)

                    duration = 0.5 * 2 ** attempt
                    logging.debug("Retrying after %.1f seconds...", duration)
                    sleep(duration)

        return self._repo

    def add_local_copy(self, dir_name):
        if self.repo is not None:
            logging.warning("You already have a local copy associated with this repo")
            return

        logging.debug("Using %s for the local repo...", dir_name)
        self._repo = git.Repo(dir_name)

    def delete(self):
        self._gl_delete("/projects/{}".format(self.id))
        logging.debug("Deleted %s.", self.name)

    @classmethod
    def create_group(cls, group, config):
        payload = {
            "name": group,
            "path": group,
            "description": "Created by assigner",
            "visibility": "private",
            "request_access_enabled": False,
        }
        cls._cls_gl_post(config, "/groups", payload)

    @classmethod
    def get_user_id(cls, username, config):
        data = cls._cls_gl_get(config, "/users", params={"search": username})

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
        return self._gl_get(
            "/projects/{}/members".format(self.id)
        )

    def get_member(self, user_id):
        return self._gl_get(
            "/projects/{}/members/{}".format(self.id, user_id)
        )

    def add_member(self, user_id, level):
        payload = {
            "id": self.id,
            "user_id": user_id,
            "access_level": level.value
        }
        try:
            return self._gl_post("/projects/{}/members".format(self.id), payload)
        except HTTPError as e:
            raiseUserInAssignerGroup(e)
            raise e

    def edit_member(self, user_id, level):
        payload = {
            "id": self.id,
            "user_id": user_id,
            "access_level": level.value
        }
        try:
            return self._gl_put(
                "/projects/{}/members/{}".format(self.id, user_id), payload
            )
        except HTTPError as e:
            raiseUserInAssignerGroup(e)
            raiseUserNotAssigned(e)
            raise e

    def delete_member(self, user_id):
        return self._gl_delete(
            "/projects/{}/members/{}".format(self.id, user_id)
        )

    def is_locked(self):
        access = [Access(m["access_level"]) for m in self.list_members()]
        return all([a in (Access.guest, Access.reporter) for a in access])

    def list_commits(self, ref_name="master"):
        params = {
            "id": self.id,
            "ref_name": ref_name
        }
        return self._gl_get(
            "/projects/{}/repository/commits".format(self.id), params
        )

    def list_pushes(self):
        return self._gl_get(
            "/projects/{}/events?action=pushed".format(self.id)
        )

    def get_last_HEAD_commit(self, ref="master"):
        matching_pushes = list(filter(
            lambda push: push['push_data']['ref'] == ref, self.list_pushes()
        ))
        commits = self.list_commits(ref)

        if not commits:
            return None

        HEAD = commits[0]
        # Gitlab's commit created_at time uses the git metadata;
        # rather than trusting students, we get the time the commit was pushed at
        if matching_pushes and HEAD['id'] == matching_pushes[0]['push_data']['commit_to']:
            # For whatever reason, Gitlab uses a different time format here than for commits...
            unmangled_time = matching_pushes[0]['created_at'][:-1] + "-0000"
            HEAD['created_at'] = unmangled_time

        return HEAD

    def list_branches(self):
        return self._gl_get(
            "/projects/{}/repository/branches".format(self.id)
        )

    def get_branch(self, branch):
        return self._gl_get(
            "/projects/{}/repository/branches/{}".format(self.id, branch)
        )

    def archive(self):
        return self._gl_post("/projects/{}/archive".format(self.id))

    def unarchive(self):
        return self._gl_post("/projects/{}/unarchive".format(self.id))

    # NOTE: these are not the same defaults that Gitlab uses
    def protect(self, branch="master", developer_push=True, developer_merge=True):
        params = {
            "developers_can_push": developer_push,
            "developers_can_merge": developer_merge,
        }
        return self._gl_put("/projects/{}/repository/branches/{}/protect"
                            .format(self.id, branch), params)

    def unprotect(self, branch="master"):
        return self._gl_put("/projects/{}/repository/branches/{}/unprotect"
                            .format(self.id, branch))

    def unlock(self, student_id: str) -> None:
        self.edit_member(student_id, Access.developer)

    def lock(self, student_id: str) -> None:
        self.edit_member(student_id, Access.reporter)

    def _gl_get(self, path, params={}):
        return self.__class__._cls_gl_get(
            self.config, path, params
        )

    def _gl_post(self, path, payload={}, params={}):
        return self.__class__._cls_gl_post(
            self.config, path, payload, params
        )

    def _gl_put(self, path, payload={}, params={}):
        return self.__class__._cls_gl_put(
            self.config, path, payload, params
        )

    def _gl_delete(self, path, params={}):
        return self.__class__._cls_gl_delete(
            self.config, path, params
        )


class GitlabTemplateRepo(GitlabRepo, TemplateRepoBase):

    @classmethod
    def new(cls, name, namespace, config):
        namespaces = cls._cls_gl_get(config, "/namespaces", {"search": namespace})
        if len(namespaces) > 1:
            logging.warning(
                "%s namespaces match %s; defaulting to namespace %s.",
                len(namespaces), namespace, namespaces[0]["path"]
            )
            logging.warning(
                "(please update the configuration in your namespace to "
                "exactly match the namespace you want Assigner to use.)"
            )

        logging.debug(
            "Using namespace %s with ID %s.",
            namespaces[0]["path"],
            namespaces[0]["id"]
        )

        payload = {
            "name": name,
            "namespace_id": namespaces[0]["id"],
            "issues_enabled": False,
            "merge_requests_enabled": False,
            "builds_enabled": False,
            "wiki_enabled": False,
            "snippets_enabled": True,  # Why not?
            "visibility_level": Visibility.private.value,
        }

        result = cls._cls_gl_post(config, "/projects", payload)

        return cls.from_url(result["http_url_to_repo"], config["token"])

    def push_to(self, student_repo, branch="master"):
        r = git.Remote.add(self.repo, student_repo.name,
                           student_repo.ssh_url)
        r.push(branch)
        logging.debug("Pushed %s to %s.", self.name, student_repo.name)


class GitlabStudentRepo(GitlabRepo, StudentRepoBase):
    """Repository for a student's solution to a homework assignment"""

    @classmethod
    def new(cls, base_repo, semester, section, username):
        """Create a new repository on GitLab"""
        payload = {
            "name": cls.build_name(semester, section, base_repo.name, username),
            "namespace_id": base_repo.namespace_id,
            "issues_enabled": False,
            "merge_requests_enabled": False,
            "builds_enabled": False,
            "wiki_enabled": False,
            "snippets_enabled": True,  # Why not?
            "visibility_level": Visibility.private.value,
        }

        result = cls._cls_gl_post(base_repo.config, "/projects", payload)

        return cls.from_url(result["http_url_to_repo"], base_repo.config["token"])

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


class GitlabBackend(BackendBase):
    """
    Common abstract base backend for all assigner backends (gitlab or mock).
    """
    repo = GitlabRepo # type: RepoBase
    template_repo = GitlabTemplateRepo # type: TemplateRepoBase
    student_repo = GitlabStudentRepo # type: StudentRepoBase
    access = Access
