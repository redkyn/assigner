from assigner.tests.utils import AssignerTestCase

from assigner.config.versions import validate, get_version, upgrade, ValidationError, VersionError
from assigner.config.upgrades import UPGRADES
from assigner.config.schemas import SCHEMAS


CONFIGS = [
    { # Version 0
        "token": "xxx gitlab token xxx",
        "gitlab-host": "https://git.gitlab.com",
        "namespace": "assigner-testing",
        "semester": "2016-SP",
        "roster": [],
    },
    { # Version 1
        "gitlab-token": "xxx gitlab token xxx",
        "gitlab-host": "https://git.gitlab.com",
        "namespace": "assigner-testing",
        "semester": "2016-SP",
        "roster": [],
    },
    { # Version 2
        "version": 2,
        "backend": {
            "name": "gitlab",
            "token": "xxx gitlab token xxx",
            "host": "https://git.gitlab.com",
        },
        "namespace": "assigner-testing",
        "semester": "2016-SP",
        "roster": [],
    },
]


EMPTY_CONFIGS = [
    {},
    {},
    {
        "version": 2,
        "backend": {
            "name": "gitlab",
        },
    },
]

TOO_NEW_CONFIG = {"version": len(SCHEMAS)}

class UpgradeTester(AssignerTestCase):
    def test_that_we_are_testing_all_schemas_and_upgrades(self):
        self.assertEqual(len(CONFIGS), len(SCHEMAS))
        self.assertEqual(len(CONFIGS), len(UPGRADES) + 1)
        self.assertEqual(len(CONFIGS), len(EMPTY_CONFIGS))

    def test_get_version(self):
        for version, config in enumerate(CONFIGS):
            self.assertEqual(version, get_version(config))

    def test_validate(self):
        for version, config in enumerate(CONFIGS):
            try:
                validate(config, version)
            except ValidationError as e:
                self.fail("Config version {} does not validate:\n\n{}".format(version, e.message))

    def test_UPGRADES(self):
        for version, config in enumerate(CONFIGS[:-1]):
            config = dict(config)
            config = UPGRADES[version](config)
            self.assertEqual(config, CONFIGS[version + 1])

            try:
                validate(config, version + 1)
            except ValidationError as e:
                self.fail("UPGRADEing from version {} to version {} results in an invalid config:\n\n{}".format(version, version + 1, e.message))

    def test_upgrade(self):
        for version, config in enumerate(CONFIGS):
            config = dict(config)

            try:
                config = upgrade(config)
                validate(config)
            except ValidationError as e:
                self.fail("Upgrading from version {} to version {} results in an invalid config:\n\n{}".format(version, len(CONFIGS) - 1, e.message))

            self.assertEqual(config, CONFIGS[-1])

    def test_empty_config_upgrade(self):
        for config in EMPTY_CONFIGS:
            config = upgrade(config)
            self.assertEqual(config, EMPTY_CONFIGS[-1])

    def test_too_new_config(self):
        with self.assertRaises(VersionError):
            validate(TOO_NEW_CONFIG)
