from parameterized import parameterized

from assigner import main, subcommands
from assigner.tests.utils import AssignerIntegrationTestCase


class HelpIntegrationTestCase(AssignerIntegrationTestCase):
    integration = True

    def test_assigner(self):
        """
        The top level assigner module should respond to help
        without errors.
        """
        with self.assertRaisesRegex(SystemExit, r"^0$"):
            main(["--help"])

    @parameterized.expand(subcommands)
    def test_subcommand(self, command):
        ("The {} subcommand should respond to help without errors."
         .format(command))
        with self.assertRaisesRegex(SystemExit, r"^0$"):
            main([command, "--help"])
