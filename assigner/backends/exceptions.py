from assigner.exceptions import AssignerException

class UserInAssignerGroup(AssignerException):
    """ A student is a member of the group/namespace assigner is creating assignments in. This may make some operatons, such as assigning homework, no-ops as they already have access. """

class UserNotAssigned(AssignerException):
    """ A student is not a member of their homework repository. """

class RetryableGitError(AssignerException):
    """ Git has encountered an error that may be spurious. """
