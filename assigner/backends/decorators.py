from assigner.backends import GitlabBackend, MockBackend
from assigner.config import requires_config


def requires_backend_and_config(func):
    """Provides a backend depending on configuration."""
    @requires_config
    def wrapper(config, cmdargs, *args, **kwargs):
        if config.backend == "gitlab":
            return func(config, GitlabBackend, cmdargs, *args, **kwargs)
        if config.backend == "mock":
            return func(config, MockBackend, cmdargs, *args, **kwargs)

        return func(config, GitlabBackend, cmdargs, *args, **kwargs)
    return wrapper
