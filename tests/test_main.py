import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from main import format_mcp_content, load_local_env_file


class MainTests(unittest.TestCase):
    def test_load_local_env_file_sets_missing_token(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = os.path.join(temp_dir, ".env")
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_file.write("BOOST_TOKEN=token-from-env-file\n")

            with patch.dict(os.environ, {}, clear=True):
                load_local_env_file(env_path)
                self.assertEqual(os.getenv("BOOST_TOKEN"), "token-from-env-file")

    def test_load_local_env_file_replaces_blank_shell_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = os.path.join(temp_dir, ".env")
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_file.write("BOOST_TOKEN=token-from-env-file\n")

            with patch.dict(os.environ, {"BOOST_TOKEN": "   "}, clear=True):
                load_local_env_file(env_path)
                self.assertEqual(os.getenv("BOOST_TOKEN"), "token-from-env-file")

    def test_load_local_env_file_keeps_non_blank_shell_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = os.path.join(temp_dir, ".env")
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_file.write("BOOST_TOKEN=token-from-env-file\n")

            with patch.dict(os.environ, {"BOOST_TOKEN": "token-from-shell"}, clear=True):
                load_local_env_file(env_path)
                self.assertEqual(os.getenv("BOOST_TOKEN"), "token-from-shell")

    def test_format_mcp_content_pretty_prints_json_text(self):
        content = SimpleNamespace(text='{"a":1,"b":{"c":2}}')
        formatted = format_mcp_content(content)
        self.assertIn('"a": 1', formatted)
        self.assertIn('"b": {', formatted)
        self.assertIn('"c": 2', formatted)

    def test_format_mcp_content_returns_non_json_text_as_is(self):
        content = SimpleNamespace(text="plain text")
        self.assertEqual(format_mcp_content(content), "plain text")

    def test_format_mcp_content_pretty_prints_dict(self):
        formatted = format_mcp_content({"status": "ok", "items": [1, 2]})
        self.assertIn('"status": "ok"', formatted)
        self.assertIn('"items": [', formatted)


if __name__ == "__main__":
    unittest.main()
