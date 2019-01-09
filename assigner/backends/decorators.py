import logging

from assigner.backends import from_name
from assigner.config import requires_config


logger = logging.getLogger(__name__)


def requires_config_and_backend(func):
    """Provides a backend depending on configuration."""
    @requires_config
    def wrapper(config, cmdargs, *args, **kwargs):

        backend = from_name(config.backend["name"])

        return func(config, backend, cmdargs, *args, **kwargs)
    return wrapper
