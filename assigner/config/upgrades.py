
def _0_to_1(config):
    config["gitlab-token"] = config["token"]
    del config["token"]
    return config


def _1_to_2(config):
    config["backend"] = "gitlab"
    config["version"] = 2
    return config


UPGRADES = [
    _0_to_1,
    _1_to_2,
]
