import git
import re
from typing import Optional, Type, TypeVar


class RepoError(Exception):
    pass


T = TypeVar('T', bound='RepoBase')
class RepoBase:
    """Generic Repo base"""

    PATH_RE = re.compile(
        r"^/(?P<namespace>[\w\-\.]+)/(?P<name>[\w\-\.]+)\.git$"
    )

    def __init__(self, url_base: str, namespace: str, name: str, token: str, url: Optional[str] = None):
        raise NotImplementedError

    @classmethod
    def build_url(cls, config, namespace: str, name: str) -> str:
        """ Builds a url for a repository """
        raise NotImplementedError

    @classmethod
    def from_url(cls: Type[T], url: str, token: str) -> T:
        raise NotImplementedError

    @property
    def name_with_namespace(self) -> str:
        raise NotImplementedError

    @property
    def namespace_id(self) -> str:
        raise NotImplementedError

    @property
    def id(self) -> str:
        raise NotImplementedError

    @property
    def info(self) -> Optional[str]:
        raise NotImplementedError

    @property
    def repo(self) -> Optional[git.Repo]:
        raise NotImplementedError

    @property
    def ssh_url(self) -> str:
        raise NotImplementedError

    def already_exists(self) -> bool:
        raise NotImplementedError

    def get_head(self, branch: str) -> git.refs.head.Head:
        raise NotImplementedError

    def checkout(self, branch: str) -> git.refs.head.Head:
        raise NotImplementedError

    def pull(self, branch: str) -> None:
        raise NotImplementedError

    def clone_to(self, dir_name: str, branch: Optional[str], attempts: Optional[int]) -> None:
        raise NotImplementedError

    def add_local_copy(self, dir_name: str) -> None:
        raise NotImplementedError

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def get_user_id(cls, username: str, config) -> str:
        raise NotImplementedError

    def list_members(self) -> str:
        raise NotImplementedError

    def get_member(self, user_id: str) -> str:
        raise NotImplementedError

    def add_member(self, user_id: str, level: str) -> str:
        raise NotImplementedError

    def edit_member(self, user_id: str, level: str) -> str:
        raise NotImplementedError

    def delete_member(self, user_id: str) -> str:
        raise NotImplementedError

    def list_commits(self, ref_name: str = "master") -> str:
        raise NotImplementedError

    def list_pushes(self) -> str:
        raise NotImplementedError

    def get_last_HEAD_commit(self, ref: str = "master") -> str:
        raise NotImplementedError

    def list_branches(self) -> str:
        raise NotImplementedError

    def get_branch(self, branch: str) -> str:
        raise NotImplementedError

    def archive(self) -> str:
        raise NotImplementedError

    def unarchive(self) -> str:
        raise NotImplementedError

    def protect(self, branch: str = "master", developer_push: bool = True, developer_merge: bool = True) -> str:
        raise NotImplementedError

    def unprotect(self, branch: str = "master") -> str:
        raise NotImplementedError

    def unlock(self, student_id: str) -> None:
        raise NotImplementedError

    def lock(self, student_id: str) -> None:
        raise NotImplementedError


T = TypeVar('T', bound='StudentRepoBase')
class StudentRepoBase(RepoBase):
    """Repository for a student's solution to a homework assignment"""

    @classmethod
    def new(cls, base_repo: str, semester: str, section: str, username: str) -> T:
        raise NotImplementedError

    @classmethod
    def build_name(cls, semester: str, section: str, assignment: str, user: str) -> str:
        raise NotImplementedError

    def push(self, base_repo, branch: str = "master") -> None:
        """Push base_repo code to this repo"""
        raise NotImplementedError


T = TypeVar('T', bound='StudentRepoBase')
class TemplateRepoBase(RepoBase):
    """A repo from which StudentRepos are cloned from (Homework Repo)."""
    @classmethod
    def new(cls, name: str, namespace: str, config) -> T:
        raise NotImplementedError

    def push_to(self, student_repo: StudentRepoBase, branch: str = "master") -> None:
        raise NotImplementedError


class BackendBase:
    """
    Common abstract base backend for all assigner backends (gitlab or mock).
    """
    repo = RepoBase # type: RepoBase
    template_repo = TemplateRepoBase # type: TemplateRepoBase
    student_repo = StudentRepoBase # type: StudentRepoBase
    access = None
