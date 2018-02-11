# Version 0
# Initial config version!

V0 = {
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
            "pattern": r"^\d{4}-(SP|FS|SS)$"
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
                        "pattern": "^[\w\.\-]+$",
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

        # Canvas API token
        "canvas-token": {
            "type": "string",
        },
        # Canvas domain
        "canvas-host": {
            "type": "string",
        }
    },
    "required": ["gitlab-host", "namespace", "token", "semester"],
    "additionalProperties": False,
}
