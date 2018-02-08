from git.exc import GitCommandError

from assigner.backends.exceptions import (
    RetryableGitError,
)

def raiseRetryableGitError(err: GitCommandError):
    """
    Intended to catch git errors that might be able to be recovered from,
    such as 'Connection reset by peer' when cloning.

    We may need to make the criteria more specific but that will be left for a future bug report!
    """

    try:
        status = int(err.status)
    except (ValueError, TypeError):
        return

    if status != 128:
        return

    raise RetryableGitError(err)
