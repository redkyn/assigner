from assigner.exceptions import AssignerException
from assigner.backends.base import RepoError

class UserInAssignerGroup(AssignerException):
    """ A student is a member of the group/namespace assigner is creating assignments in. This may make some operatons, such as assigning homework, no-ops as they already have access. """

class UserAlreadyAssigned(AssignerException):
    """ A student is already a member of their homework repository. """

class UserNotAssigned(AssignerException):
    """ A student is not a member of their homework repository. """

class RetryableGitError(AssignerException):
    """ Git has encountered an error that may be spurious. """

class AssignerGroupNotFound(AssignerException):
    """ The group where assignments will be created does not exist. """

class RepositoryAlreadyExists(AssignerException):
    """ The repository has already been created. """

class BranchNotFound(RepoError):
    """ The branch cannot be found in the repository. """

class CIArtifactNotFound(AssignerException):
    """ CI Artifact not found. """
