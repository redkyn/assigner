import git
import json
import logging
import os
import re
import requests
import tempfile

from enum import Enum
from urllib.parse import urlsplit, urlunsplit, urljoin, quote


class BaseRepoError(Exception):
    pass


class Visibility(Enum):
    """Gitlab API values for repo visibility"""
    private = 0
    internal = 10
    public = 20


class Repo(object):
    """Gitlab repo; manages API requests and various metadata"""

    PATH_RE = re.compile(r'^/(?P<namespace>[\w\-\.]+)/(?P<name>[\w\-\.]+)\.git$')

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

    def __init__(self, url, token):
        self.url = url
        self.token = token

        parts = urlsplit(url)
        if not parts.scheme:
            raise BaseRepoError("{} is missing a scheme.".format(url))
        if not parts.netloc:
            raise BaseRepoError("{} is missing a domain.".format(url))

        if parts.scheme != "https":
            logging.warning("Using scheme {} instead of https.", parts.scheme)

        match = self.__class__.PATH_RE.match(parts.path)
        if not match:
            raise BaseRepoError(
                "Bad path. Can't separate namespace from "
                "repo name {}".format(parts.path)
            )

        self.namespace = match.group("namespace")
        self.name = match.group("name")

        logging.debug(json.dumps(self.info))
        logging.info("Found %s", self.name_with_namespace)

    @property
    def name_with_namespace(self):
        return "{}/{}".format(self.namespace, self.name)

    @property
    def namespace_id(self):
        return self.info['namespace']['id']

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

    @property
    def url_base(self):
        """Return just the scheme and the netloc"""
        s, n, _, _, _ = urlsplit(self.url)
        return urlunsplit((s, n, '', '', ''))

    def _gl_get(self, path, params={}):
        return self.__class__._cls_gl_get(
            self.url_base, path, self.token, params
        )

    def _gl_post(self, path, payload={}, params={}):
        return self.__class__._cls_gl_post(
            self.url_base, path, self.token, payload
        )


class BaseRepo(Repo):

    def clone_to(self, dir_name):
        self._repo = git.Repo.clone_from(self.ssh_url, dir_name)
        logging.info("Cloned %s", self.name)
        return self._repo

    def push_to(self, student_repo):
        r = git.Remote.add(self.repo, student_repo.name, student_repo.ssh_url)
        r.push("master")
        logging.info("Pushed %s to %s", self.name, student_repo.name)


class StudentRepo(Repo):
    """Repository for a student's solution to a homework assignment"""

    @classmethod
    def new(cls, base_repo, semester, section, username, token):
        """Create a new repository on GitLab"""
        fmt = {
            'semester': semester,
            'section': section,
            'assignment': base_repo.name,
            'user': username
        }

        payload = {
            'name': "{semester}-{section}-{assignment}-{user}".format(**fmt),
            'namespace_id': base_repo.namespace_id,
            'issues_enabled': False,
            'merge_requests_enabled': False,
            'builds_enabled': False,
            'wiki_enabled': False,
            'snippets_enabled': True,  # Why not?
            'visibility_level': Visibility.private,
        }

        result = cls._cls_gl_post(base_repo.url_base, "/projects", token, payload)

        return cls(base_repo, result['http_url_to_repo'], token)
    
    def __init__(self, base_repo, url, token):
        super().__init__(url, token)
        self.base_repo = base_repo

    def push_base(self):
        """Push base repo code to this repo"""
        self.base_repo.push_to(self)


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
