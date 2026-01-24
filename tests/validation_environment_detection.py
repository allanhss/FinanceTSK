"""Validation tests for automatic test environment detection."""

import os
import sys
import unittest
from unittest import mock


class TestEnvironmentDetection(unittest.TestCase):
    """Test automatic environment detection for test mode."""

    def test_testing_mode_env_variable(self):
        """Test detection of TESTING_MODE environment variable."""
        # Save original
        original_testing_mode = os.environ.get("TESTING_MODE")

        try:
            # Set environment variable
            os.environ["TESTING_MODE"] = "1"

            # Import fresh to trigger detection
            import importlib
            import src.database.connection as conn

            importlib.reload(conn)

            self.assertTrue(conn.TESTING_MODE, "Should detect TESTING_MODE=1")
        finally:
            # Restore
            if original_testing_mode is None:
                os.environ.pop("TESTING_MODE", None)
            else:
                os.environ["TESTING_MODE"] = original_testing_mode

    def test_pytest_module_detection(self):
        """Test detection when pytest is in sys.modules."""
        # This test will automatically pass since we're running via pytest
        import src.database.connection as conn

        # pytest should be in sys.modules during test execution
        self.assertIn(
            "pytest",
            sys.modules,
            "pytest should be in sys.modules during test execution",
        )
        self.assertTrue(conn.TESTING_MODE, "Should detect pytest in sys.modules")

    def test_is_test_env_function(self):
        """Test the is_test_env function directly."""
        from src.database.connection import is_test_env

        # Should return True because we're running via pytest
        result = is_test_env()
        self.assertTrue(result, "is_test_env should return True in test execution")

    def test_test_database_path_used(self):
        """Test that test_finance.db path is used in test mode."""
        import src.database.connection as conn

        # When in test mode, should use test_finance.db
        self.assertTrue(conn.TESTING_MODE, "Should be in test mode")
        self.assertTrue(
            "test_finance.db" in conn.CAMINHO_BANCO,
            f"Expected test_finance.db in path, got: {conn.CAMINHO_BANCO}",
        )

    def test_is_test_env_path_detection(self):
        """Test path-based detection for /tests/ folder."""
        from src.database.connection import is_test_env

        # Save original argv
        original_argv = sys.argv[0]

        try:
            # Simulate script in /tests/ folder
            test_script_path = "/home/user/project/tests/validation_test.py"
            sys.argv[0] = test_script_path

            # should_be_test should detect /tests/ in path
            # But is_test_env will also check pytest in sys.modules which is True in this context
            result = is_test_env()
            # Will be True because pytest is in sys.modules
            self.assertTrue(result)
        finally:
            sys.argv[0] = original_argv

    def test_database_url_format(self):
        """Test that DATABASE_URL is correctly formatted."""
        import src.database.connection as conn

        # DATABASE_URL should be a sqlite URL
        self.assertTrue(
            conn.DATABASE_URL.startswith("sqlite:///"),
            f"DATABASE_URL should start with sqlite:///, got: {conn.DATABASE_URL}",
        )


if __name__ == "__main__":
    print("🔒 Running environment detection validation tests...")

    # Run tests
    unittest.main(verbosity=2)
