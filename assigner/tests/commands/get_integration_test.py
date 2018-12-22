from unittest.mock import call, MagicMock

from assigner.backends.base import BackendBase
from assigner.commands.get import _get as get
from assigner.tests.utils import AssignerIntegrationTestCase


class GetIntegrationTestCase(AssignerIntegrationTestCase):
    integration = True

    def setUp(self):
        super().setUp()

        self.mock_roster = self._create_patch(
            "assigner.commands.get.get_filtered_roster", autospec=True
        )
        self.mock_os = self._create_patch(
            "assigner.commands.get.os", autospec=True
        )
        self.mock_prettytable = self._create_patch(
            "assigner.commands.get.PrettyTable", autospec=True
        )

        self.mock_backend = MagicMock(spec=BackendBase)
        self.mock_conf = MagicMock(**{
            "path": "somepath/",
            "hw_name": "HW2",
            "section": "SP2017",
            "student": MagicMock(),
            "branch": ["a", "b"],
            "force": MagicMock()
        })
        self.mock_args = MagicMock()

    def test_get_no_students(self):
        """
        Test getting no student repositories.
        """
        self.mock_roster.return_value = []
        get(self.mock_conf, self.mock_backend, self.mock_args)

        self.mock_os.path.join.assert_called_once_with(
            self.mock_args.path, self.mock_args.name
        )
        self.mock_os.makedirs.assert_called_once_with(
            self.mock_os.path.join.return_value, mode=0o700, exist_ok=True
        )
        self.assertFalse(self.mock_backend.student_repo.called)

    def test_get_students(self):
        """
        Test getting some student repositories.
        """
        self.mock_roster.return_value = [MagicMock(), MagicMock()]
        get(self.mock_conf, self.mock_backend, self.mock_args)

        for student in self.mock_roster.return_value:
            studentrepo_name = self.mock_backend.student_repo.build_name(
                self.mock_config.semester, student["section"],
                self.mock_args.name, student["username"]
            )
            # Should build a student name and create a StudentRepo object
            studentrepo = self.mock_backend.student_repo(
                self.mock_config.backend, self.mock_config.namespace,
                studentrepo_name
            )
            # Should use their username to build a directory.
            student_dir = self.mock_os.path.join(self.mock_os.path.join(
                self.mock_args.path, self.mock_args.name
            ), student.username)
            # All of this should be used to make a student repo directory.
            studentrepo.add_local_copy.assert_called_with(student_dir)

            # And then get the branch.
            for b in self.mock_args.branch:
                self.assertTrue(studentrepo.get_head(b).checkout.called)

            studentrepo.pull.assert_has_calls(
                [call(b) for b in self.mock_args.branches]
            )
