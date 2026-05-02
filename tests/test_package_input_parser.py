import unittest

from package_input_parser import parse_package_input


class ParsePackageInputTests(unittest.TestCase):
    def test_pypi_at_version_format(self):
        parsed = parse_package_input("httpx@0.28.1")
        self.assertEqual(parsed["ecosystem"], "pypi")
        self.assertIsNone(parsed["namespace"])
        self.assertEqual(parsed["package"], "httpx")
        self.assertEqual(parsed["version"], "0.28.1")

    def test_pypi_space_version_format(self):
        parsed = parse_package_input("httpx 0.28.1")
        self.assertEqual(parsed["ecosystem"], "pypi")
        self.assertIsNone(parsed["namespace"])
        self.assertEqual(parsed["package"], "httpx")
        self.assertEqual(parsed["version"], "0.28.1")

    def test_explicit_ecosystem_triplet_format(self):
        parsed = parse_package_input("pypi httpx 0.28.1")
        self.assertEqual(parsed["ecosystem"], "pypi")
        self.assertIsNone(parsed["namespace"])
        self.assertEqual(parsed["package"], "httpx")
        self.assertEqual(parsed["version"], "0.28.1")

    def test_compact_prefixed_ecosystem_format(self):
        parsed = parse_package_input("golang:github.com/golang-jwt/jwt/v5@v5.0.0")
        self.assertEqual(parsed["ecosystem"], "golang")
        self.assertEqual(parsed["namespace"], "github.com/golang-jwt")
        self.assertEqual(parsed["package"], "jwt/v5")
        self.assertEqual(parsed["version"], "v5.0.0")

    def test_golang_shorthand_defaults_to_github_namespace(self):
        parsed = parse_package_input("golang-jwt/jwt/v5@v5.0.0")
        self.assertEqual(parsed["ecosystem"], "golang")
        self.assertEqual(parsed["namespace"], "github.com/golang-jwt")
        self.assertEqual(parsed["package"], "jwt/v5")
        self.assertEqual(parsed["version"], "v5.0.0")

    def test_explicit_golang_triplet_github_module(self):
        parsed = parse_package_input("golang github.com/golang-jwt/jwt/v5 v5.0.0")
        self.assertEqual(parsed["ecosystem"], "golang")
        self.assertEqual(parsed["namespace"], "github.com/golang-jwt")
        self.assertEqual(parsed["package"], "jwt/v5")
        self.assertEqual(parsed["version"], "v5.0.0")

    def test_invalid_missing_version(self):
        with self.assertRaises(ValueError):
            parse_package_input("httpx")

    def test_invalid_extra_tokens(self):
        with self.assertRaises(ValueError):
            parse_package_input("pypi httpx 0.28.1 extra")


if __name__ == "__main__":
    unittest.main()
