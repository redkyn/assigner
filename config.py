import logging
import jsonschema
import yaml

from collections import UserDict


def config(filename):
    """Get you a brand new config manager"""
    return _Config(filename)


class _Config(UserDict):
    """Context manager for config; automatically saves changes"""

    CONFIG_SCHEMA = {
        "$schema": "http://json-schema.org/schema#",

        "type": "object",
        "properties": {
            # GitLab private token
            "token": {
                "type": "string",
            },

            # GitLab domain (https://git.gitlab.com)
            "gitlab-host": {
                "type": "string",
            },

            # GitLab Namespace name
            "namespace": {
                "type": "string",
            },

            # GitLab Namespace ID (we'd have to retrieve that)
            "namespace-id": {
                "type": "integer",
            },

            # Verbose name of the course (might be unnecessary)
            "course-name": {
                "type": "string",
            },

            # Current semester
            "semester": {
                "type": "string",
                "pattern": r"^\d{4}(SP|FS|SM)$"
            },

            # Roster of students
            "roster": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {

                        # Their full name
                        "name": {
                            "type": "string"
                        },

                        # Section
                        "section": {
                            "type": "string"
                        },

                        # Their GitLab username (single sign on)
                        "username": {
                            "type": "string",
                            "pattern": "^\w+$",
                        },

                        # Their GitLab id (might be handy, but we'd have
                        # to fetch it and save it). Should save time in
                        # the long run instead of constantly querying
                        "id": {
                            "type": "integer",
                        },
                    },
                    "required": ["name", "username", "section"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["gitlab-host", "namespace", "token", "semester"],
        "additionalProperties": False,
    }

    def __init__(self, filename):
        super().__init__()
        self._filename = filename
        try:
            with open(filename) as f:
                self.data = yaml.safe_load(f)
                jsonschema.validate(self.data, self.__class__.CONFIG_SCHEMA)
        except FileNotFoundError:
            pass  # Just make an empty config; create on __exit__()
        except jsonschema.ValidationError as e:
            logging.warning(str(e))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        with open(self._filename, 'w') as f:
            yaml.dump(self.data, f, indent=2, default_flow_style=False)

        return False  # propagate exceptions from the calling context
