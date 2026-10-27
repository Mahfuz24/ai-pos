import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CpanelFoundationTests(unittest.TestCase):
    def test_api_fails_closed(self):
        php = (ROOT / "web/api/index.php").read_text()
        self.assertIn("http_response_code(503)", php)
        self.assertIn("'orchestration' => 'disabled'", php)
        self.assertIn("'release' => 'blocked'", php)
        self.assertNotIn("password", php.lower())
    def test_api_directory_listing_disabled(self):
        self.assertIn("Options -Indexes", (ROOT / "web/api/.htaccess").read_text())
    def test_deployment_keeps_founder_key_off_host(self):
        docs = (ROOT / "docs/CPANEL-DEPLOYMENT.md").read_text()
        self.assertIn("stays on Fedora", docs)
        self.assertIn("separate document root", docs)

if __name__ == "__main__":
    unittest.main()
