from assigner.backends.base import BackendBase, RepoError
from assigner.backends.gitlab import GitlabBackend

pyflakes = [BackendBase, RepoError, GitlabBackend]
