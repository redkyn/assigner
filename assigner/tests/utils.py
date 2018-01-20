from unittest import TestCase
from unittest.mock import patch


class AssignerTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_CLASS_CLEANUP"):
            [x() for x in cls._CLASS_CLEANUP]

    @classmethod
    def _create_class_patch(cls, target, **kwargs):
        """
        Shortcut for creating a class-level patch with proper
        cleanup handled.
        """
        target_patch = patch(target, **kwargs)
        target_mock = target_patch.start()

        if not hasattr(cls, "_CLASS_CLEANUP"):
            cls._CLASS_CLEANUP = []

        cls._CLASS_CLEANUP.append(target_patch.stop)
        return target_mock

    def _create_patch(self, target, **kwargs):
        """
        Shortcut for creating a class and having it cleaned up
        properly.
        """
        target_patch = patch(target, **kwargs)
        target_mock = target_patch.start()
        self.addCleanup(target_patch.stop)

        return target_mock
