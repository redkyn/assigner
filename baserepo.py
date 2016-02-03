import git
import json
import logging
import os
import re
import requests
import tempfile

from enum import Enum
from urllib.parse import urlsplit, urlunsplit, urljoin, quote


class RepoError(Exception):
    pass


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


class Repo(object):
    """Gitlab repo; manages API requests and various metadata"""

    PATH_RE = re.compile(r'^/(?P<namespace>[\w\-\.]+)/(?P<name>[\w\-\.]+)\.git$')

    @classmethod
    def build_url(cls, url_base, namespace, name):
        """ Build a url for a repository """
        return url_base + '/' + namespace + '/' + name + '.git'

    @classmethod
    def from_url(cls, url, token):
        parts = urlsplit(url)
        if not parts.scheme:
            raise RepoError("{} is missing a scheme.".format(url))
        if not parts.netloc:
            raise RepoError("{} is missing a domain.".format(url))

        if parts.scheme != "https":
            logging.warning("Using scheme {} instead of https.", parts.scheme)

        match = cls.PATH_RE.match(parts.path)
        if not match:
            raise RepoError(
                "Bad path. Can't separate namespace from "
                "repo name {}".format(parts.path)
            )

        namespace = match.group("namespace")
        name = match.group("name")

        self = cls(urlunsplit((parts.scheme, parts.netloc, '', '', '')), namespace, name, token, url)

        logging.debug(json.dumps(self.info))
        logging.info("Found %s", self.name_with_namespace)

        return self

    @classmethod
    def _cls_gl_get(cls, url_base, path, token, params={}):
        """Make a Gitlab GET request"""
        params.update({'private_token': token})
        url = urljoin(url_base, '/api/v3' + path)
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

    @classmethod
    def _cls_gl_post(cls, url_base, path, token, payload={}, params={}):
        """Make a Gitlab POST request"""
        params.update({'private_token': token})
        url = urljoin(url_base, '/api/v3' + path)
        r = requests.post(url, params=params, data=payload)
        r.raise_for_status()
        return r.json()

    @classmethod
    def _cls_gl_put(cls, url_base, path, token, payload={}, params={}):
        """Make a Gitlab PUT request"""
        params.update({'private_token': token})
        url = urljoin(url_base, '/api/v3' + path)
        r = requests.put(url, params=params, data=payload)
        r.raise_for_status()
        return r.json()

    @classmethod
    def _cls_gl_delete(cls, url_base, path, token, params={}):
        """Make a Gitlab DELETE request"""
        params.update({'private_token': token})
        url = urljoin(url_base, '/api/v3' + path)
        r = requests.delete(url, params=params)
        r.raise_for_status()
        return r.json()

    def __init__(self, url_base, namespace, name, token, url=None):
        self.url_base = url_base
        self.namespace = namespace
        self.name = name
        self.token = token

        if url is None:
            self.url = Repo.build_url(url_base, namespace, name)
        else:
            self.url = url

    @property
    def name_with_namespace(self):
        return "{}/{}".format(self.namespace, self.name)

    @property
    def namespace_id(self):
        return self.info['namespace']['id']

    @property
    def id(self):
        return self.info['id']

    @property
    def info(self):
        if not hasattr(self, "_info"):
            quoted = quote(self.name_with_namespace, safe='')
            url = "/projects/{}".format(quoted)
            self._info = self._gl_get(url)
        return self._info

    @property
    def repo(self):
        if hasattr(self, "_repo"):
            return self._repo
        logging.debug("Repo not cloned yet!")
        return None

    @property
    def ssh_url(self):
        return self.info['ssh_url_to_repo']

    def clone_to(self, dir_name, branch=None):
        if branch:
            self._repo = git.Repo.clone_from(self.ssh_url, dir_name, branch=branch)
        else:
            self._repo = git.Repo.clone_from(self.ssh_url, dir_name)
        logging.info("Cloned %s", self.name)
        return self._repo

    def delete(self):
        self._gl_delete("/projects/{}".format(self.id))
        logging.info("Deleted %s", self.name)

    # TODO: this should really go elsewhere
    @classmethod
    def get_user_id(cls, username, url_base, token):
        data = cls._cls_gl_get(url_base, "/users", token, params={'search': username})

        if len(data) == 0:
            logging.warn("Did not find any users matching %s", username)
            raise RepoError("No user {}".format(username))

        if len(data) > 1:
            logging.warn("Got %d users for %s", len(data), username)

        logging.info("Got id %d for user %s", data[0]['id'], username)
        return data[0]['id']

    def add_member(self, user_id, level):
        payload = {'id': self.id, 'user_id': user_id, 'access_level': level.value}
        return self._gl_post("/projects/{}/members".format(self.id), payload)

    def edit_member(self, user_id, level):
        payload = {'id': self.id, 'user_id': user_id, 'access_level': level.value}
        return self._gl_put("/projects/{}/members/{}".format(self.id, user_id), payload)

    def delete_member(self, user_id):
        return self._gl_delete("/projects/{}/members/{}".format(self.id, user_id))

    def _gl_get(self, path, params={}):
        return self.__class__._cls_gl_get(
            self.url_base, path, self.token, params
        )

    def _gl_post(self, path, payload={}, params={}):
        return self.__class__._cls_gl_post(
            self.url_base, path, self.token, payload
        )

    def _gl_put(self, path, payload={}, params={}):
        return self.__class__._cls_gl_put(
            self.url_base, path, self.token, payload
        )

    def _gl_delete(self, path, params={}):
        return self.__class__._cls_gl_delete(
            self.url_base, path, self.token, params
        )


class BaseRepo(Repo):

    @classmethod
    def new(cls, name, namespace, url_base, token):
        namespaces = cls._cls_gl_get(url_base, "/namespaces", token, {'search': namespace})
        logging.debug("Got %d namespaces matching %s", len(namespaces), namespace)
        logging.debug("Using namespace %s with ID %d", namespaces[0]["path"], namespaces[0]["id"])

        payload = {
            'name': name,
            'namespace_id': namespaces[0]["id"],
            'issues_enabled': False,
            'merge_requests_enabled': False,
            'builds_enabled': False,
            'wiki_enabled': False,
            'snippets_enabled': True,  # Why not?
            'visibility_level': Visibility.private,
        }

        result = cls._cls_gl_post(url_base, "/projects", token, payload)

        return cls.from_url(result['http_url_to_repo'], token)

    def push_to(self, student_repo, branch="master"):
        r = git.Remote.add(self.repo, student_repo.name, student_repo.ssh_url)
        r.push(branch)
        logging.info("Pushed %s to %s", self.name, student_repo.name)


class StudentRepo(Repo):
    """Repository for a student's solution to a homework assignment"""

    @classmethod
    def new(cls, base_repo, semester, section, username, token):
        """Create a new repository on GitLab"""
        payload = {
            'name': cls.name(semester, section, base_repo.name, username),
            'namespace_id': base_repo.namespace_id,
            'issues_enabled': False,
            'merge_requests_enabled': False,
            'builds_enabled': False,
            'wiki_enabled': False,
            'snippets_enabled': True,  # Why not?
            'visibility_level': Visibility.private,
        }

        result = cls._cls_gl_post(base_repo.url_base, "/projects", token, payload)

        return cls.from_url(result['http_url_to_repo'], token)

    @classmethod
    def name(cls, semester, section, assignment, user):
        fmt = {
            'semester': semester,
            'section': section,
            'assignment': assignment,
            'user': user
        }

        return "{semester}-{section}-{assignment}-{user}".format(**fmt)

    def push(self, base_repo, branch="master"):
        """Push base_repo code to this repo"""
        base_repo.push_to(self, branch)


if __name__ == '__main__':
    # Need to make this module if'n you're going to run this
    from secret import token

    logging.basicConfig(level=logging.INFO)

    b = BaseRepo("https://git.mst.edu/2016-Spring-CS-2001/hw01.git", token)
    print(json.dumps(b.info, indent=8))
    with tempfile.TemporaryDirectory() as tmpdirname:
        b.clone_to(tmpdirname)
        print(os.listdir(tmpdirname))

    StudentRepo.new(b, "2016SP", "A", "mwwcp2", token)
