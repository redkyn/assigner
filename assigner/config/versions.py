import jsonschema
import logging

from assigner.config.schemas import SCHEMAS
from assigner.config.upgrades import UPGRADES

logger = logging.getLogger(__name__)


class ValidationError(jsonschema.ValidationError):
    pass


class VersionError(Exception):
    pass


class UpgradeError(Exception):
    pass


def validate(config, version=None):
    if version is None:
        version = get_version(config)

    if version >= len(SCHEMAS):
        raise VersionError(
            "Configuration version %d is newer than latest known configuration version %d" % (version, len(SCHEMAS) - 1)
        )

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
        return config

    if current != latest:
        logger.info("Migrating configuration from version %d to version %d.", current, latest)

    # Determine whether we should look for upgrade-caused
    # validation errors. If the initial config doesn't validate,
    # we can't tell whether upgrading has made things worse, but
    # we'll try anyway.
    try:
        validate(config, current)
        is_valid = True
    except ValidationError:
        is_valid = False

    for version in range(current, latest):
        config = UPGRADES[version](config)

        # Upgrade validation.
        # Upgrades should be rare, so we can afford to be very particular about them.
        assert get_version(config) == version + 1
        if is_valid:
            try:
                validate(config, version + 1)
            except ValidationError as e:
                # pylint: disable=bad-continuation
                raise UpgradeError(
"""
Upgrading configuration from version %d to %d resulted in an invalid configuration:
%s

This is a bug. Please file an issue at https://github.com/redkyn/assigner/issues with your configuration.
Your original configuration has been restored.
""" % (version, version + 1, e.message)
                )

    return config
