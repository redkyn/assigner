from assigner.backends import GitlabBackend
from assigner.config import config_context


def require_backend(func):
    """Provides a backend depending on configuration."""
    @config_context
    def wrapper(config, cmdargs, *args, **kwargs):
        if config.backend == "gitlab":
            return func(config, GitlabBackend, cmdargs, *args, **kwargs)

        return func(config, GitlabBackend, cmdargs, *args, **kwargs)
    return wrapper
