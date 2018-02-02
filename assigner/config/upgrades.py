
def _0_to_1(config):
    config["gitlab-token"] = config["token"]
    del config["token"]
    return config


def _1_to_2(config):
    config["version"] = 2
    config["backend"] = {
        "name": "gitlab",
    }

    if "gitlab-token" in config:
        config["backend"]["token"] = config["gitlab-token"]
        del config["gitlab-token"]

    if "gitlab-host" in config:
        config["backend"]["host"] = config["gitlab-host"]
        del config["gitlab-host"]

    return config


UPGRADES = [
    _0_to_1,
    _1_to_2,
]
