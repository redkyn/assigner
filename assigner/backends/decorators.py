from assigner.backends import GitlabBackend
from assigner.config import config_context


@config_context
def require_backend(config, func):
    """Provides a backend depending on configuration."""
    def wrapper(*args, **kwargs):
        if config.backend == "gitlab":
            func(GitlabBackend, *args, **kwargs)

        func(GitlabBackend, *args, **kwargs)
    return wrapper
