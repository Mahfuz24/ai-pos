import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
class WebFoundationTests(unittest.TestCase):
    def test_static_holding_page_has_no_credentials_or_scripts(self):
        html = (ROOT / "web/index.html").read_text()
        self.assertIn("Deployment not authorized", html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("<form", html.lower())
        self.assertNotIn("founder.key", html)
    def test_headers_fail_closed(self):
        config = (ROOT / "web/.htaccess").read_text()
        self.assertIn("Options -Indexes", config)
        self.assertIn("default-src 'none'", config)
        self.assertIn('X-Frame-Options "DENY"', config)

if __name__ == "__main__":
    unittest.main()
