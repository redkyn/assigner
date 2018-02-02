import jsonschema
import logging

from assigner.config.schemas import SCHEMAS
from assigner.config.upgrades import UPGRADES

logger = logging.getLogger(__name__)


class ValidationError(jsonschema.ValidationError):
    pass


def validate(config, version=(len(SCHEMAS) - 1)):
    assert version < len(SCHEMAS)

    try:
        jsonschema.validate(config, SCHEMAS[version])
    except jsonschema.ValidationError as e:
        raise ValidationError(e)


def get_version(config):
    if "version" not in config:
        # Pre-version tracking
        if "token" in config:
            return 0
        return 1

    return config["version"]


def upgrade(config):
    current = get_version(config)
    latest = len(SCHEMAS) - 1

    if current > latest:
        logger.warning("Configuration version %d is newer than latest known configuration version %d", current, latest)
        logger.warning("Is your installation of Assigner up to date?")
        logger.warning("Attempting to continue anyway...")
        return config

    if current != latest:
        logger.info("Migrating configuration from version %d to version %d.", current, latest)

    for version in range(current, latest):
        config = UPGRADES[version](config)
        assert get_version(config) == version + 1

    return config
