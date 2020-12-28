from assigner.backends.base import BackendBase, RepoError
from assigner.backends.gitlab import GitlabBackend
from assigner.backends.mock import MockBackend

pyflakes = [BackendBase, RepoError, GitlabBackend, MockBackend]

backend_names = {
    "gitlab": GitlabBackend,
    "mock": MockBackend,
    }

class NoSuchBackend(Exception):
    pass

def from_name(name: str):
    try:
        return backend_names[name]
    except KeyError:
        raise NoSuchBackend("Cannot find backend with name {}".format(name)) from None
