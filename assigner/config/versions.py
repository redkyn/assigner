import jsonschema
from assigner.config.schemas import SCHEMAS
from assigner.config.upgrades import UPGRADES

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

    for i in range(current, latest):
        config = UPGRADES[i](config)
        #validate(config, i + 1)
        assert get_version(config) == i + 1

    return config
