import logging

from assigner.backends import GitlabBackend, MockBackend
from assigner.config import requires_config


logger = logging.getLogger(__name__)


def requires_config_and_backend(func):
    """Provides a backend depending on configuration."""
    @requires_config
    def wrapper(config, cmdargs, *args, **kwargs):
        try:
            config.backend
        except KeyError:
            logger.info(
                "The 'backend' field in config is not set; it will default to Gitlab."
            )
            return func(config, GitlabBackend, cmdargs, *args, **kwargs)

        if config.backend == "gitlab":
            return func(config, GitlabBackend, cmdargs, *args, **kwargs)
        return func(config, MockBackend, cmdargs, *args, **kwargs)
    return wrapper
