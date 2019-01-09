import itertools
from unittest.mock import patch

from assigner import main, make_parser, subcommands
from assigner.tests.utils import AssignerTestCase

from git.cmd import GitCommandNotFound


class MakeParserTestCase(AssignerTestCase):
    def setUp(self):
        self.mock_argparse = self._create_patch(
            "assigner.argparse", autospec=True
        )
        self.mock_parser = self.mock_argparse.ArgumentParser.return_value
        self.mock_subparser = self.mock_parser.add_subparsers.return_value

    def test_creates_argument_parser(self):
        """
        make_parser should create an ArgumentParser when called.
        """
        make_parser()
        self.assertTrue(self.mock_argparse.ArgumentParser.called)

    def test_adds_all_subcommands(self):
        """
        make_subparser should add all subcommands when called.
        """
        make_parser()

        flattened_calls = list(itertools.chain(*itertools.chain(
            *self.mock_subparser.add_parser.call_args_list
        )))
        for command in subcommands:
            self.assertIn(command, flattened_calls)

    def test_add_default_help(self):
        """
        make_subparser should add a default to print usage when caled.
        """
        make_parser()

        # NOTE: You can't compare lambdas made in different scopes
        self.assertTrue(self.mock_parser.set_defaults.called)
        self.assertFalse(self.mock_parser.print_usage.called)

        mock_args = self.mock_parser.parse_args.return_value
        mock_args.version = False

        _, kwargs = self.mock_parser.set_defaults.call_args
        kwargs['run'](mock_args)
        self.assertTrue(self.mock_parser.print_usage.called)


class ExampleError(Exception):
    pass


class MainTestCase(AssignerTestCase):
    def setUp(self):
        self.mock_configure = self._create_patch(
            "assigner.configure_logging", autospec=True
        )
        self.mock_make_parser = self._create_patch(
            "assigner.make_parser", autospec=True
        )
        self.mock_parser = self.mock_make_parser.return_value
        self.mock_args = self.mock_parser.parse_args.return_value
        self.mock_logging = self._create_patch(
            "assigner.logging", autospec=True
        )

    def test_calls_make_parser(self):
        """
        main calls parse_args on make_parser's returned parser.
        """
        main([])

        self.assertTrue(self.mock_parser.parse_args.called)

    def test_calls_args_run(self):
        """
        main calls args.run with args.
        """
        main([])

        self.mock_args.run.assert_called_once_with(self.mock_args)

    def test_main_catches_exceptions(self):
        """
        main should catch any exceptions and raise SystemExit.
        """
        self.mock_args.tracebacks = False
        self.mock_args.run.side_effect = Exception

        with self.assertRaises(SystemExit):
            main([])

    def test_main_raises_exceptions_with_traceback(self):
        """
        main should raise exceptions if traceback is True.
        """
        self.mock_args.tracebacks = True
        self.mock_args.run.side_effect = ExampleError

        with self.assertRaises(ExampleError):
            main([])

    @patch("assigner.logger", autospec=True)
    def test_main_logs_exceptions(self, mock_logger):
        """
        main should log exceptions when raised.
        """
        self.mock_args.tracebacks = False
        self.mock_args.run.side_effect = ExampleError
        try:
            main([])
        except SystemExit:
            pass

        mock_logger.error.assert_called_once_with(str(ExampleError()))

    @patch("assigner.logger", autospec=True)
    def test_main_logs_keyerror_with_catch(self, mock_logger):
        """
        main should log a KeyError with "is missing" when raised.
        """
        self.mock_args.tracebacks = False
        self.mock_args.run.side_effect = KeyError()
        try:
            main([])
        except SystemExit:
            pass

        mock_logger.error.assert_called_once_with(
            "%s is missing", self.mock_args.run.side_effect
        )

    @patch("assigner.logger", autospec=True)
    def test_main_logs_gitcommandnotfound_with_catch(self, mock_logger):
        """
        main should log a GitCommandNotFound with "git is not installed!" when raised.
        """
        self.mock_args.tracebacks = False
        self.mock_args.run.side_effect = GitCommandNotFound("git", "not installed!")
        try:
            main([])
        except SystemExit:
            pass

        mock_logger.error.assert_called_once_with(
            "git is not installed!"
        )

    def test_main_sets_verbosity(self):
        """
        main should set verosity and level from args.
        """
        main([])

        mock_logger = self.mock_logging.getLogger.return_value
        mock_logger.setLevel.assert_any_call(
            self.mock_args.verbosity
        )
