import logging
import yaml

from collections import UserDict

from assigner.config.versions import upgrade, validate, ValidationError


class DuplicateUserError(Exception):
    pass


def config_context(func):
    def wrapper(cmdargs, *args):
        with Config(cmdargs.config) as conf:
            return func(conf, cmdargs, *args)
    return wrapper


class Config(UserDict):
    """Context manager for config; automatically saves changes"""

    def __init__(self, filename):
        super().__init__()
        self._filename = filename

        try:
            with open(filename) as f:
                self.data = yaml.safe_load(f)
        except FileNotFoundError:
            pass  # Just make an empty config; create on __exit__()

        try:
            self.data = upgrade(self.data)
            validate(self.data)
        except ValidationError as e:
            logging.warning("Your configuration is not valid: %s", e.message)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        with open(self._filename, "w") as f:
            yaml.dump(self.data, f, indent=2, default_flow_style=False)

        return False  # propagate exceptions from the calling context

    def __getattr__(self, key):
        attr = getattr(super(Config, self), key, None)
        if attr:
            return attr
        # Keys contained dashes can be called using an underscore
        key = key.replace("_", "-")

        # Fill in a blank roster if needed
        if key == "roster" and self.data.get(key, None) is None:
            self.data[key] = []

        return self.data[key]
