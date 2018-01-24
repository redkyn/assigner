from assigner.backends.base import BackendBase, RepoError
from assigner.backends.gitlab import GitlabBackend
from assigner.backends.mock import MockBackend

pyflakes = [BackendBase, RepoError, GitlabBackend, MockBackend]
