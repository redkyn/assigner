from assigner.backends import GitlabBackend, MockBackend
from assigner.config import config_context


def require_backend(func):
    """Provides a backend depending on configuration."""
    @config_context
    def wrapper(config, cmdargs, *args, **kwargs):
        if config.backend == "gitlab":
            return func(config, GitlabBackend, cmdargs, *args, **kwargs)
        if config.backend == "mock":
            return func(config, MockBackend, cmdargs, *args, **kwargs)

        return func(config, GitlabBackend, cmdargs, *args, **kwargs)
    return wrapper
